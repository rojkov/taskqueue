"""
The module `taskqueue.worker` contains the abstract class :class:`BaseWorker`.
All your worker plugins should be derived from it.

Your custom functionality should be put into the method `handle_task()`.
And if you want to modify the way how task results are reported or tracked
then override the method `report_results()` of your worker subclass.

Taskqueue uses the `pkg_resources` library to discover registered
plugins. So in order to make your plugins visible to your taskqueue
installation you need to register your worker factories as entry points under
the group `worker.plugins`::

    setup(
        entry_points={
            'worker.plugins': [
                'customworker = yourpackage.yourmodule:YourWorker.factory'
            ]
        }
    )

"""

import logging
import pika
import signal
import os
import sys
import traceback

from pwd import getpwnam

from taskqueue.confparser import OPT_RESULTS_ROUTING_KEY
from taskqueue.workitem import get_workitem, WorkitemError, DEFAULT_CONTENT_TYPE

LOG = logging.getLogger(__name__)

CFG_DEFAULT_RES_ROUTING = "results"

def log_trace(func):
    """Log traceback before raising exception."""
    def new_func(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except:
            exc_type, exc_value, tb = sys.exc_info()
            for line in traceback.format_tb(tb):
                LOG.error(line.strip())
            LOG.error("%s: %s" % (exc_type, exc_value))
            raise
    return new_func

class BaseWorker(object):
    """Base class for workers."""

    #: Specifies list of workitem types accepted by the worker. By default
    #: workers accept workitems of any type.
    ACCEPT = ["*/*"]

    @classmethod
    def factory(cls):
        """Produce new worker callable."""
        return cls()

    def __init__(self):
        """Constructor."""

        self.channel = None
        self.connection = None
        self.results_routing_key = CFG_DEFAULT_RES_ROUTING
        self.settings = {}

    @log_trace
    def __call__(self, props, conn_params, queue):
        """Worker process entry point."""

        self.settings.update(props)

        if "user" in props.keys():
            LOG.debug("Try to switch to user '%s'" % props['user'])
            if os.geteuid() == 0:
                try:
                    newuid = getpwnam(props["user"])[2]
                    os.seteuid(newuid)
                    LOG.debug("Swithced to uid %d" % newuid)
                except KeyError:
                    LOG.error("No such user '%s'" % props['user'])
            else:
                LOG.warning("Not enough permissions to switch user")

        self.connection = pika.BlockingConnection(conn_params)
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=queue, durable=True,
                                   exclusive=False, auto_delete=False)
        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(self.handle_delivery, queue=queue)
        signal.signal(signal.SIGTERM, self.cleanup)
        LOG.debug("created new process with props %r" % props)
        if OPT_RESULTS_ROUTING_KEY in props.keys():
            self.results_routing_key = props[OPT_RESULTS_ROUTING_KEY]
        self.channel.start_consuming()

    def is_acceptable(self, workitem):
        """Check if received workitem can be handled by worker.

        :param workitem: workitem to check
        :type workitem: Workitem
        :rtype: boolean
        """

        wtype, subwtype = workitem.mime_type.split('/')

        for mtype in self.ACCEPT:
            ctype, subctype = mtype.split('/')
            if (ctype == '*' or ctype == wtype) and \
               (subctype == '*' or subctype == subwtype):
                LOG.debug("Accept: %s" % workitem.mime_type)
                return True

        LOG.error("Workitem '%r got rejected by %s.%s as incompatible" %
                  (workitem, self.__module__, self.__class__.__name__))
        return False

    def handle_task(self, workitem):
        """Handle task.

        This method is supposed to be overriden in BaseWorker subclasses.

        :param workitem: workflow work item
        :type workitem: Workitem
        :returns: new state of work item
        :rtype: Workitem
        """
        raise NotImplementedError

    @log_trace
    def handle_delivery(self, channel, method, header, body):
        """Handle AMQP message.

        :param channel: AMQP channel
        :type channel: pika.channel.Channel
        :param method: message's method
        :type method: pika.frame.Method
        :param header: message header
        :type header: pika.frame.Header
        :param body: message body
        :type body: string
        """

        LOG.debug("Method: %r" % method)
        LOG.debug("Header: %r" % header)
        try:
            workitem = get_workitem(header, body,
                                    self.settings.get('workitem_type_map',
                                                      None),
                                    self.settings.get('default_workitem_type',
                                                      DEFAULT_CONTENT_TYPE))
        except WorkitemError as err:
            LOG.error("Worker %s.%s can't handle delivery with header '%r' "
                      "and body:\n%s" % (self.__module__,
                                         self.__class__.__name__,
                                         header, body))
            channel.basic_ack(method.delivery_tag)
            return False
        wi_out = workitem
        if self.is_acceptable(workitem):
            try:
                wi_out = self.handle_task(workitem)
            except Exception as err:
                wi_out.set_error(str(err))
                wi_out.set_trace(traceback.format_exc())
        else:
            wi_out.set_error("Worker doesn't support this type of workitems")
        self.report_results(channel, wi_out)
        channel.basic_ack(method.delivery_tag)
        return True

    def report_results(self, channel, workitem):
        """Report task results back to AMQP.

        Feel free to override this method.

        :param channel: AMQP channel
        :type channel: pika.channel.Channel
        :param workitem: workflow work item
        :type workitem: Workitem
        """

        channel.basic_publish(exchange='',
                              routing_key=self.results_routing_key,
                              body=workitem.dumps(),
                              properties=pika.BasicProperties(
                                  delivery_mode=2,
                                  content_type=workitem.mime_type
                              ))

    def cleanup(self, signum, frame):
        """Cleanup worker process."""

        LOG.debug("target cleanup")
        self.channel.stop_consuming()
        self.connection.close()
