import sys
import daemon
import logging
import socket
import signal
import pika

from time import sleep
from logging.handlers import SysLogHandler
from taskqueue.daemonlib import Daemon

LOG = logging.getLogger(__name__)

def handle_delivery(channel, method, header, body):
    """Handle delivery from WFE."""
    LOG.debug("Method: %r" % method)
    LOG.debug("Header: %r" % header)
    LOG.debug("Body: %r" % body)
    worker, msg = body.split(" ", 1)

    channel.basic_publish(exchange='',
                          routing_key='worker_%s' % worker,
                          body=msg,
                          properties=pika.BasicProperties(
                              delivery_mode=2
                          ))

    channel.basic_ack(method.delivery_tag)

class Application(Daemon):

    def __init__(self, config):
        """Initialize application."""

        self.channel = None
        # TODO: set config in base class
        self.config = config

    def run(self):
        """Event cycle."""

        LOG.debug("run!")
        parameters = pika.ConnectionParameters(host="localhost")
        LOG.debug("create connection")
        self.connection = pika.BlockingConnection(parameters)
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
