import sys
import daemon
import logging
import socket
import signal
import pika

from time import sleep
from logging.handlers import SysLogHandler

LOG = logging.getLogger(__name__)

def handle_delivery(channel, method, header, body):
    """Handle delivery from WFE."""
    LOG.debug("Method: %r" % method)
    LOG.debug("Header: %r" % header)
    LOG.debug("Body: %r" % body)

    channel.basic_publish(exchange='',
                          routing_key='worker_first',
                          body=body,
                          properties=pika.BasicProperties(
                              delivery_mode=2
                          ))

    channel.basic_ack(method.delivery_tag)

class Application(object):

    def __init__(self):
        """Initialize application."""

        self.channel = None

    def run(self):
        """Event cycle."""

        LOG.debug("run!")
        parameters = pika.ConnectionParameters(host="localhost")
        LOG.debug("create connection")
        connection = pika.BlockingConnection(parameters)
        self.channel = connection.channel()
        self.channel.queue_declare(queue="taskqueue", durable=True,
                                   exclusive=False, auto_delete=False)
        self.channel.basic_consume(handle_delivery, queue="taskqueue")
        self.channel.start_consuming()

    def cleanup(self, signum, frame):
        """Handler for terminationsignals."""

        LOG.debug("cleanup")
        self.channel.stop_consuming()
        sys.exit(0)

def main():
    """Dispatcher entry point."""

    # configure logging
    rootlogger = logging.getLogger()
    rootlogger.setLevel(logging.DEBUG)
    sh = SysLogHandler(address='/dev/log',
                       facility=SysLogHandler.LOG_DAEMON,
                       socktype=socket.SOCK_STREAM)
    sh.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(name)s:%(levelname)s:%(message)s')
    sh.setFormatter(formatter)
    rootlogger.addHandler(sh)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)
    rootlogger.addHandler(ch)

    app = Application()

    context = daemon.DaemonContext()
    context.detach_process = False # for development purposes
    context.stdout = sys.stdout
    context.stderr = sys.stdout

    context.signal_map = {
        signal.SIGTERM: app.cleanup,
        signal.SIGHUP: app.cleanup
    }

    with context:
        app.run()
