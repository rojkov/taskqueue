"""
Taskqueue dispatcher daemon
"""

import sys
import logging
import pika
import json

from taskqueue.daemonlib import Daemon

LOG = logging.getLogger(__name__)

def handle_delivery(channel, method, header, body):
    """Handle delivery from WFE."""
    LOG.debug("Method: %r" % method)
    LOG.debug("Header: %r" % header)
    LOG.debug("Body: %r" % body)
    workitem = json.loads(body)
    worker = workitem["fields"]["params"]["worker_type"]
    msg = body

    channel.basic_publish(exchange='',
                          routing_key='worker_%s' % worker,
                          body=msg,
                          properties=pika.BasicProperties(
                              delivery_mode=2
                          ))

    channel.basic_ack(method.delivery_tag)

class Application(Daemon):
    """Dispatcher daemon"""

    pidfile = "/var/run/dispatcher.pid"

    def __init__(self, config):
        """Initialize application."""

        self.channel = None
        self.connection = None
        super(Application, self).__init__(config)

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
