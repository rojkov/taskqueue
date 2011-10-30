import sys
import daemon
import logging
import socket
import signal
import pika
import pkg_resources

from time import sleep
from logging.handlers import SysLogHandler

LOG = logging.getLogger(__name__)

class Application(object):

    def __init__(self):
        """Initialize application."""

        self.channels = []

    def run(self):
        """Event cycle."""

        LOG.debug("run!")
        parameters = pika.ConnectionParameters(host="localhost")
        LOG.debug("create connection")
        connection = pika.BlockingConnection(parameters)

        group = "worker.plugins"
        for entrypoint in pkg_resources.iter_entry_points(group=group):
            LOG.info("register plugin %r" % entrypoint.name)
            plugin = entrypoint.load()
            handler = plugin()
            channel = connection.channel()
            channel.queue_declare(queue="worker_%s" % entrypoint.name,
                                  durable=True,
                                  exclusive=False, auto_delete=False)
            channel.basic_qos(prefetch_count=handler.prefetch_count)
            channel.basic_consume(handler.handle_task,
                                  queue="worker_%s" % entrypoint.name)
            channel.start_consuming()
            self.channels.append(channel)

    def cleanup(self, signum, frame):
        """Handler for terminationsignals."""

        LOG.debug("cleanup")
        for channel in self.channels:
            channel.stop_consuming()
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
