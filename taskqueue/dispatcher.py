"""
Taskqueue dispatcher daemon
"""

import sys
import logging
import pika
import json

from taskqueue.daemonlib import Daemon
from taskqueue.workitem import get_workitem, WorkitemError

LOG = logging.getLogger(__name__)

def handle_delivery(channel, method, header, body):
    """Handle delivery from WFE."""
    LOG.debug("Method: %r" % method)
    LOG.debug("Header: %r" % header)
    LOG.debug("Body: %r" % body)

    try:
        workitem = get_workitem(header, body)
    except WorkitemError as err:
        # Report error and accept message
        LOG.error("%s" % err)
        channel.basic_ack(method.delivery_tag)
        return

    worker = workitem.worker_type
    channel.basic_publish(exchange='',
                          routing_key='worker_%s' % worker,
                          body=body,
                          properties=pika.BasicProperties(
                              delivery_mode=2,
                              content_type=header.content_type
                          ))

    channel.basic_ack(method.delivery_tag)

class Dispatcher(Daemon):
    """Dispatcher daemon"""

    pidfile = "/var/run/dispatcher.pid"

    def __init__(self, config):
        """Initialize application."""

        self.channel = None
        self.connection = None
        super(Dispatcher, self).__init__(config)

    def run(self):
        """Event cycle."""

        LOG.debug("run!")
        LOG.debug("create connection")
        self.connection = pika.BlockingConnection(self.amqp_params)
        LOG.debug("dispatcher connected")
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue="taskqueue", durable=True,
                                   exclusive=False, auto_delete=False)
        self.channel.basic_consume(handle_delivery, queue="taskqueue")
        self.channel.start_consuming()

    def cleanup(self, signum, frame):
        """Handler for termination signals."""

        LOG.debug("cleanup")
        self.channel.stop_consuming()
        self.connection.close()
        sys.exit(0)
