import unittest

from ConfigParser import SafeConfigParser as ConfigParser
from mock import Mock

import multiprocessing
import taskqueue.workerpool

class TestError(Exception):
    pass

class TestApplication(unittest.TestCase):
    """Tests for worker pool."""

    def setUp(self):

        def fake_fun():
            pass

        self.is_alive_counter = 0
        def fake_is_alive():
            if self.is_alive_counter > 0:
                raise TestError
            self.is_alive_counter = self.is_alive_counter + 1
            return False

        mockproc = Mock()
        mockproc.is_alive = fake_is_alive
        config = ConfigParser()
        taskqueue.workerpool.Process = Mock(return_value=mockproc)
        self.wpool = taskqueue.workerpool.Application(config)
        self.wpool.plugins['first'] = fake_fun
        self.wpool.create_worker('first', {})

    def test_create_worker(self):
        """Test Application.create_worker()."""

        self.assertTrue(len(self.wpool.processes) > 0)

    def test_cleanup(self):
        """Test Application.cleanup()."""
        self.assertRaises(SystemExit, self.wpool.cleanup, None, None)

    def test_monitor(self):
        """Test Application.monitor()."""

        self.assertRaises(TestError, self.wpool.monitor)
        self.assertTrue(self.is_alive_counter == 1)

    def test_run(self):
        """Test Application.run()."""

        self.assertRaises(TestError, self.wpool.run)
        self.assertTrue(self.is_alive_counter == 1)

    def test_run_with_group(self):
        """Test Application.run() with process group."""

        self.wpool.config.add_section('first')
        self.wpool.config.add_section('first_group1')
        self.wpool.config.set('first', 'workers', 'group1')
        self.assertRaises(TestError, self.wpool.run)
        self.assertTrue(self.is_alive_counter == 1)
