import unittest

from mock import Mock
from ConfigParser import SafeConfigParser as ConfigParser

import taskqueue.dispatcher

class TestHandler(unittest.TestCase):

    def test_handle_delivery(self):
        """Test handle_delivery()."""
        taskqueue.dispatcher.handle_delivery(Mock(), Mock(), None,
            '{"fields": {"params": {"worker_type": "first"}}}')


class TestDispatcher(unittest.TestCase):
    """Tests for dispatcher."""

    def setUp(self):
        config = ConfigParser()
        self.disp = taskqueue.dispatcher.Dispatcher(config)
        self.disp.channel = Mock()
        self.disp.connection = Mock()
        taskqueue.dispatcher.pika = Mock()

    def test_cleanup(self):
        """Test Dispatcher.cleanup()."""
        self.assertRaises(SystemExit, self.disp.cleanup, None, None)

    def test_run(self):
        """Test Dispatcher.run()."""
        self.disp.run()
