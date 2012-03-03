import unittest

from mock import Mock
from ConfigParser import SafeConfigParser as ConfigParser

import taskqueue.dispatcher

class TestDispatcher(unittest.TestCase):
    """Tests for dispatcher."""

    def setUp(self):
        config = ConfigParser()
        self.disp = taskqueue.dispatcher.Dispatcher(config)
        self.disp.channel = Mock()
        self.disp.connection = Mock()
        taskqueue.dispatcher.pika = Mock()

    def test_handle_delivery(self):
        """Test handle_delivery()."""
        self.disp.handle_delivery(Mock(), Mock(), Mock(),
            '{"fields": {"params": {"worker_type": "first"}}}')

    def test_cleanup(self):
        """Test Dispatcher.cleanup()."""
        self.assertRaises(SystemExit, self.disp.cleanup, None, None)

    def test_run(self):
        """Test Dispatcher.run()."""
        self.disp.run()
