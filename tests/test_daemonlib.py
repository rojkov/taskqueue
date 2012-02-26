import unittest
import os

from mock import Mock
from ConfigParser import SafeConfigParser as ConfigParser

import taskqueue.daemonlib

class TestModule(unittest.TestCase):

    def test_parse_cmdline(self):
        """Test parse_cmdline()."""

        taskqueue.daemonlib.parse_cmdline({"pidfile": "test.pid"})


class TestPidFile(unittest.TestCase):

    def setUp(self):
        self.fname = "/tmp/1234qwer.pid"

    def test_context(self):
        """Test using PidFile() as context wrapper."""

        fname = self.fname

        with taskqueue.daemonlib.PidFile(fname):
            self.assertTrue(os.path.isfile(fname))
            secondpf = taskqueue.daemonlib.PidFile(fname)
            self.assertRaises(SystemExit, secondpf.__enter__)

        self.assertFalse(os.path.isfile(fname))

    def test_exit_error(self):
        """Test raising exception in PidFile.__exit__()."""

        pf = taskqueue.daemonlib.PidFile(self.fname)
        pf.pidfile = Mock()
        pf.pidfile.close = Mock(side_effect=IOError)
        self.assertRaises(IOError, pf.__exit__)


class TestDaemon(unittest.TestCase):
    """Tests for Daemon class."""

    def setUp(self):
        self.pcmd = taskqueue.daemonlib.parse_cmdline
        opts = Mock()
        opts.foreground = True
        taskqueue.daemonlib.parse_cmdline = Mock(return_value=opts)
        self.config = ConfigParser()
        taskqueue.daemonlib.pika = Mock()
        fake_ctx = Mock()
        fake_ctx.__exit__ = Mock()
        fake_ctx.__enter__ = Mock()
        taskqueue.daemonlib.daemon.DaemonContext = Mock(return_value=fake_ctx)
        taskqueue.daemonlib.logging.config = Mock()
        config = Mock()
        config.items = Mock(return_value=[])
        taskqueue.daemonlib.ConfigParser = Mock(return_value=config)
        self.daemon = taskqueue.daemonlib.Daemon(self.config)

    def tearDown(self):
        taskqueue.daemonlib.parse_cmdline = self.pcmd

    def test_constructor(self):
        """Test Daemon.__init__()."""

        self.config.add_section('amqp')
        taskqueue.daemonlib.Daemon(self.config)

    def test_cleanup(self):
        self.assertRaises(NotImplementedError, self.daemon.cleanup, None, None)

    def test_run(self):
        self.assertRaises(NotImplementedError, self.daemon.run)

    def test_main(self):

        taskqueue.daemonlib.Daemon.pidfile = "/tmp/1234frre.pid"
        taskqueue.daemonlib.Daemon.main()
