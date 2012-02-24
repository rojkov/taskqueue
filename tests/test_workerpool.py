import unittest

from ConfigParser import SafeConfigParser as ConfigParser
from mock import Mock

import multiprocessing
import taskqueue.workerpool

class TestApplication(unittest.TestCase):
    """Tests for worker pool."""

    def setUp(self):
        config = ConfigParser()
        taskqueue.workerpool.Process = Mock()
        self.wpool = taskqueue.workerpool.Application(config)

    def test_create_worker(self):
        """Test Application.create_worker()."""

        def fake_fun():
            pass

        self.wpool.plugins['first'] = fake_fun
        self.wpool.create_worker('first', {})
