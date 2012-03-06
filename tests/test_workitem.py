import unittest

from mock import Mock

from taskqueue.workitem import BasicWorkitem, RuoteWorkitem, get_workitem
from taskqueue.workitem import BasicWorkitemError, RuoteWorkitemError, \
                               WorkitemError

class TestModule(unittest.TestCase):

    def test_get_workitem(self):
        """Test get_workitem()."""

        header = Mock
        header.content_type = "test/fake"
        self.assertRaises(WorkitemError, get_workitem, header, "")
        header.content_type = None
        self.assertRaises(WorkitemError, get_workitem, header, "")

        self.assertRaises(WorkitemError, get_workitem, header, "", "")
        self.assertRaises(WorkitemError, get_workitem, header, "", "key=value")

        import taskqueue.workitem
        entry = Mock()
        entry.load = Mock(side_effect=ImportError)
        taskqueue.workitem.iter_entry_points = Mock(return_value=[entry])
        self.assertRaises(WorkitemError, get_workitem, header, "")

class TestWorkitem(object):

    def test_set_error(self):
        self.loaded_wi.set_error("error")

    def test_set_trace(self):
        self.loaded_wi.set_trace("traceback")

    def test_worker_type(self):
        def explode():
            self.wi.worker_type
        self.assertRaises(WorkitemError, explode)
        self.loaded_wi.worker_type

    def test_dumps(self):
        self.assertRaises(WorkitemError, self.wi.dumps)

class TestBasicWorkitem(TestWorkitem, unittest.TestCase):

    def setUp(self):
        wi = BasicWorkitem('application/x-basic-workitem')
        wi.loads("wtype body")
        self.loaded_wi = wi
        self.wi = BasicWorkitem('application/x-basic-workitem')

class TestRuoteWorkitem(TestWorkitem, unittest.TestCase):
    """Tests for RuoteWorkitems."""

    def setUp(self):
        self.wi = RuoteWorkitem('application/x-ruote-workitem')

        wi = RuoteWorkitem('application/x-ruote-workitem')
        wi.loads('{"fields": {"params": {"worker_type": "test"}}, "fei": {}}')
        self.loaded_wi = wi

    def test_repr(self):
        """Test RuoteWorkitem.__repr__()."""
        self.wi._worker_type = "worker_type"
        self.assertEqual(self.wi.__repr__(), "<RuoteWorkitem([worker_type='worker_type'])>")

    def test_loads(self):
        """Tests RuoteWorkitem.loads()."""

        self.wi.loads('{"fields": {"params": {"worker_type": "test"}}}')

        self.assertRaises(RuoteWorkitemError, self.wi.loads, "{}")

    def test_dumps(self):
        """Test RuoteWorkitem.dumps()."""

        TestWorkitem.test_dumps(self)

        self.wi._body = {}
        self.assertEqual("{}", self.wi.dumps())

    def test_fei(self):
        fei = self.loaded_wi.fei
        fei["test"] = 1
        self.assertFalse(self.loaded_wi._body["fei"].has_key("test"))

    def test_fields(self):
        fields = self.loaded_wi.fields
        fields["test"] = 1
        self.assertTrue(self.loaded_wi._body["fields"].has_key("test"))
