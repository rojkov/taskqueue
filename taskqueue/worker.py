"""
The module `taskqueue.worker` contains the abstract class :class:`BaseWorker`.
All your worker plugins should be derived from it.

Your custom functionality should be put into the method `handle_task()`.
And if you want to modify the way how task results are reported or tracked
then override the method `report_results()` of your worker subclass.
"""

import logging
import pika
import signal
import os
import traceback

from pwd import getpwnam

from taskqueue.workitem import get_workitem

LOG = logging.getLogger(__name__)

CFG_KEY_RES_ROUTING = "results_routing_key"
CFG_DEFAULT_RES_ROUTING = "results"

class BaseWorker(object):
    """Base class for workers."""

    ACCEPT = ["*/*"]

    @classmethod
    def factory(cls):
        """Produce new worker callable."""
        return cls()

    def __init__(self):
        """Constructor."""

        self.channel = None
        self.connection = None
        self.results_routing_key=CFG_DEFAULT_RES_ROUTING
        self.settings = {}

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
        if CFG_KEY_RES_ROUTING in props.keys():
            self.results_routing_key = props[CFG_KEY_RES_ROUTING]
        self.channel.start_consuming()

    def is_acceptable(self, workitem):
        """Check if received workitem can be handled by worker."""
        # TODO: this is a stub. implement workitem type checking
        return True

    def handle_task(self, workitem):
        """Handle task.

        This method is supposed to be overriden in BaseWorker subclasses.

        :param workitem: workflow work item
        :type workitem: dictionary
        :returns: new state of work item
        :rtype: dictionary
        """
        raise NotImplementedError

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
        workitem = get_workitem(header, body)
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

    def report_results(self, channel, workitem):
        """Report task results back to AMQP.

        Feel free to override this method.

        :param channel: AMQP channel
        :type channel: pika.channel.Channel
        :param workitem: workflow work item
        :type workitem: dictionary
        """

        channel.basic_publish(exchange='',
                              routing_key=self.results_routing_key,
                              body=workitem.dumps(),
                              properties=pika.BasicProperties(
                                  delivery_mode=2
                              ))

    def cleanup(self, signum, frame):
        """Cleanup worker process."""

        LOG.debug("target cleanup")
        self.channel.stop_consuming()
        self.connection.close()
