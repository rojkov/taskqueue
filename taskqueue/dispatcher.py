"""
Taskqueue dispatcher daemon
"""

import sys
import logging
import pika

from taskqueue.daemonlib import Daemon

from ConfigParser import NoSectionError

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
    """Dispatcher daemon"""

    pidfile = "/var/run/dispatcher.pid"

    def __init__(self, config):
        """Initialize application."""

        self.channel = None
        self.connection = None
        # TODO: set config in base class
        self.config = config
        try:
            amqp_host   = config.get("amqp", "host")
            amqp_user   = config.get("amqp", "user")
            amqp_passwd = config.get("amqp", "passwd")
            amqp_vhost  = config.get("amqp", "vhost")
            credentials = pika.PlainCredentials(amqp_user, amqp_passwd)
            self.amqp_params = pika.ConnectionParameters(
                credentials=credentials,
                host=amqp_host,
                virtual_host=amqp_vhost)
            LOG.debug("amqp params read from config")
        except NoSectionError:
            self.amqp_params = pika.ConnectionParameters(host="localhost")

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
