import unittest

from mock import Mock

import taskqueue.worker

class TestBaseWorker(unittest.TestCase):
    """Tests for BaseWorker."""

    def setUp(self):
        self.worker = taskqueue.worker.BaseWorker.factory()
        taskqueue.worker.pika = Mock()
        taskqueue.worker.os.geteuid = Mock(return_value=0)
        taskqueue.worker.os.seteuid = Mock()
        taskqueue.worker.getpwnam = Mock(return_value=[None, None, 1234])

    def test_factory(self):
        """Test BaseWorker.factory()."""
        self.assertTrue(isinstance(self.worker, taskqueue.worker.BaseWorker))

    def test_handle_task(self):
        """Test BaseWorker.handle_task()."""
        self.assertRaises(NotImplementedError, self.worker.handle_task, {})

    def test_callable(self):
        """Test BaseWorker.__call__()."""
        self.worker({'results_routing_key': 'results'}, {}, 'fakequeue')
        self.assertFalse(taskqueue.worker.os.geteuid.called)

        self.worker({"user": "fakeuser"}, {}, 'fakequeue')
        self.assertTrue(taskqueue.worker.os.geteuid.called)
        taskqueue.worker.os.seteuid.assert_called_once_with(1234)

        taskqueue.worker.getpwnam = Mock(side_effect=KeyError)
        self.worker({"user": "fakeuser"}, {}, 'fakequeue')

        # not enough permissions to change euid
        taskqueue.worker.os.geteuid = Mock(return_value=1000)
        self.worker({"user": "fakeuser"}, {}, 'fakequeue')

    def test_handle_delivery(self):
        """Test BaseWorker.handle_delivery()."""

        self.worker.handle_delivery(Mock(), Mock(), "header", "{}")

    def test_report_results(self):
        """Test BaseWorker.report_results()."""

        self.worker.report_results(Mock(), "{}")

    def test_cleanup(self):
        """Test BaseWorker.cleanup()."""

        self.worker.channel = Mock()
        self.worker.connection = Mock()
        self.worker.cleanup("fake_signum", "fake_frame")

if __name__ == "__main__":
    unittest.main()
