import logging, logging.config
import daemon
import signal
import sys
import os
import fcntl
import pika

from taskqueue.confparser import ConfigParser, NoSectionError

from optparse import OptionParser

LOG = logging.getLogger(__name__)

def parse_cmdline(defaults):
    """Parse commandline options."""

    parser = OptionParser()
    parser.add_option("-f", "--foreground", dest="foreground",
                      action="store_true", default=False,
                      help="don't deamonize")
    parser.add_option("-c", "--config", dest="config",
                      default="/etc/taskqueue/config.ini",
                      help="path to config file")
    parser.add_option("-p", "--pid-file", dest="pidfile",
                      default=defaults["pidfile"])

    (options, args) = parser.parse_args()
    return options

class PidFile(object):
    """Context manager that locks a pid file.

    Implemented as class not generator because daemon.py is
    calling .__exit__() with no parameters instead of the None, None, None
    specified by PEP-343.
    copy&pasted from
    http://code.activestate.com/recipes/577911-context-manager-for-a-daemon-pid-file/
    """
    # pylint: disable=R0903

    def __init__(self, path):
        self.path = path
        self.pidfile = None

    def __enter__(self):
        self.pidfile = open(self.path, "a+")
        try:
            fcntl.flock(self.pidfile.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except IOError:
            raise SystemExit("Already running according to " + self.path)
        self.pidfile.seek(0)
        self.pidfile.truncate()
        self.pidfile.write(str(os.getpid()))
        self.pidfile.flush()
        self.pidfile.seek(0)
        return self.pidfile

    def __exit__(self, exc_type=None, exc_value=None, exc_tb=None):
        try:
            self.pidfile.close()
        except IOError as err:
            # ok if file was just closed elsewhere
            if err.errno != 9:
                raise
        os.remove(self.path)

class Daemon(object):

    pidfile = "/var/run/python-daemon.pid"

    def __init__(self, config):
        self.config = config
        try:
            amqp_items  = dict(config.items("amqp"))
            amqp_host   = amqp_items.get("host", "localhost")
            amqp_user   = amqp_items.get("user", "guest")
            amqp_passwd = amqp_items.get("passwd", "guest")
            amqp_vhost  = amqp_items.get("vhost", "/")
            credentials = pika.PlainCredentials(amqp_user, amqp_passwd)
            self.amqp_params = pika.ConnectionParameters(
                credentials=credentials,
                host=amqp_host,
                virtual_host=amqp_vhost)
        except NoSectionError:
            self.amqp_params = pika.ConnectionParameters(host="localhost")

    def cleanup(self, signum, frame):
        """Abstract cleanup."""
        raise NotImplementedError

    def run(self):
        """Abstract run."""
        raise NotImplementedError

    @classmethod
    def main(cls):
        """Dispatcher entry point."""

        options = parse_cmdline({"pidfile": cls.pidfile})

        # configure logging
        logging.config.fileConfig(options.config,
                                  disable_existing_loggers=False)

        config = ConfigParser()
        config.read(options.config)

        daemon_obj = cls(config)

        context = daemon.DaemonContext()

        context.pidfile = PidFile(options.pidfile)
        if options.foreground:
            context.detach_process = False
            context.stdout = sys.stdout
            context.stderr = sys.stdout

        context.signal_map = {
            signal.SIGTERM: daemon_obj.cleanup,
            signal.SIGHUP: daemon_obj.cleanup
        }

        with context:
            daemon_obj.run()
