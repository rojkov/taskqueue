import unittest

from mock import Mock
from ConfigParser import SafeConfigParser as ConfigParser

import taskqueue.dispatcher

class TestHandler(unittest.TestCase):

    def test_handle_delivery(self):
        """Test handle_delivery()."""
        taskqueue.dispatcher.handle_delivery(Mock(), Mock(), None,
            '{"fields": {"params": {"worker_type": "first"}}}')


class TestApplication(unittest.TestCase):
    """Tests for dispatcher."""

    def setUp(self):
        config = ConfigParser()
        self.disp = taskqueue.dispatcher.Application(config)
        self.disp.channel = Mock()
        self.disp.connection = Mock()
        taskqueue.dispatcher.pika = Mock()

    def test_cleanup(self):
        """Test Application.cleanup()."""
        self.assertRaises(SystemExit, self.disp.cleanup, None, None)

    def test_run(self):
        """Test Application.run()."""
        self.disp.run()
