import unittest

from taskqueue.confparser import ConfigParser
from mock import Mock

import taskqueue.workerpool

class TestError(Exception):
    pass

class TestWorkerPool(unittest.TestCase):
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
        self.wpool = taskqueue.workerpool.WorkerPool(config)
        self.wpool.plugins['first'] = fake_fun
        self.wpool.create_worker('first', {})

    def test_is_plugin_enabled(self):
        """Test WorkerPool.is_plugin_enabled()."""
        self.assertTrue(self.wpool.is_plugin_enabled("fakeplugin"))

        self.wpool._enabled_plugins = ["fakeplugin"]
        self.assertTrue(self.wpool.is_plugin_enabled("fakeplugin"))
        self.assertFalse(self.wpool.is_plugin_enabled("not_enabled_plugin"))

    def test_create_worker(self):
        """Test WorkerPool.create_worker()."""

        self.assertTrue(len(self.wpool.processes) > 0)

    def test_cleanup(self):
        """Test WorkerPool.cleanup()."""
        self.assertRaises(SystemExit, self.wpool.cleanup, None, None)

    def test_monitor(self):
        """Test WorkerPool.monitor()."""

        self.assertRaises(TestError, self.wpool.monitor)
        self.assertTrue(self.is_alive_counter == 1)

    def test_run(self):
        """Test WorkerPool.run()."""

        self.assertRaises(TestError, self.wpool.run)
        self.assertTrue(self.is_alive_counter == 1)

    def test_run_with_group(self):
        """Test WorkerPool.run() with process group."""

        self.wpool.config.add_section('workers')
        self.wpool.config.set('workers', 'enabled_plugins', 'first')
        self.wpool.config.add_section('worker_first')
        self.wpool.config.add_section('worker_first_subgroup1')
        self.wpool.config.set('worker_first', 'subgroups', 'subgroup1')
        self.assertRaises(TestError, self.wpool.run)
        self.assertTrue(self.is_alive_counter == 1)
