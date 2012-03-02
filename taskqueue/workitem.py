import logging
import json

from pkg_resources import iter_entry_points

LOG = logging.getLogger(__name__)

DEFAULT_CONTENT_TYPE = 'application/json'

CONTENT_TYPE_MAP = {
    'application/json': 'application/x-ruote-workitem',
    'text/plain':       'application/x-basic-workitem'
}

class WorkitemError(Exception):
    pass

def get_workitem(amqp_header, amqp_body):
    """Constructs workitems of a certain type."""

    if amqp_header.content_type:
        ctype = amqp_header.content_type
    else:
        ctype = DEFAULT_CONTENT_TYPE

    ctype = CONTENT_TYPE_MAP.get(ctype, ctype)

    workitem = None
    # look for a Workitem class
    for entry in iter_entry_points(group='workitems', name=ctype):
        LOG.debug("found module '%s'" % entry.module_name)
        try:
            cls = entry.load()
            workitem = cls()
            workitem.loads(amqp_body)
            break
        except ImportError:
            LOG.info("plugin '%s' is not installed. skipping..." %
                     entry.module_name)
            continue
        except WorkitemError:
            LOG.warning("Can't parse workitem with the plugin '%s'" %
                        entry.module_name)
            continue

    if workitem is None:
        raise WorkitemError("No working plugin found for workitem of "
                            "the type '%s'" % ctype)
    return workitem

class BasicWorkitemError(WorkitemError):
    pass

class BasicWorkitem(object):

    mime_type = 'application/x-basic-workitem'

    def __init__(self, options=None):
        self._body = None
        self._worker_type = None

    def __repr__(self):
        return "<BasicWorkitem([worker_type='%s'])>" % self._worker_type

    def loads(self, blob):
        try:
            self._worker_type, self._body = blob.split(" ", 1)
        except (ValueError, TypeError):
            raise BasicWorkitemError("Can't parse workitem body")

    def dumps(self):
        if self._body is None:
            raise BasicWorkitemError("Workitem hasn't been loaded")
        return "%s %s" % (self._worker_type, self._body)

    @property
    def worker_type(self):
        if self._worker_type is None:
            raise BasicWorkitemError("Workitem hasn't been loaded")
        return self._worker_type

    def set_error(error):
        self._body += "\nError: %s" % error

    def set_trace(trace):
        self._body += "\nTrace: %s" % trace

class RuoteWorkitemError(WorkitemError):
    pass

class RuoteWorkitem(object):

    mime_type = 'application/x-ruote-workitem'

    def __init__(self, options=None):
        self._body = None
        self._worker_type = None

    def __repr__(self):
        return "<RuoteWorkitem([worker_type='%s'])>" % self._worker_type

    def loads(self, blob):
        try:
            self._body = json.loads(blob)
            self._worker_type = self._body["fields"]["params"]["worker_type"]
        except (ValueError, KeyError, TypeError):
            raise RuoteWorkitemError("Can't parse workitem body")

    def dumps(self):
        if self._body is None:
            raise RuoteWorkitemError("Workitem hasn't been loaded")
        return json.dumps(self._body)

    @property
    def worker_type(self):
        if self._worker_type is None:
            raise RuoteWorkitemError("Workitem hasn't been loaded")
        return self._worker_type

    def set_error(error):
        self._body["error"] = error

    def set_trace(trace):
        self._body["trace"] = trace

    @property
    def fei(self):
        # fei is a read-only attribute
        return self._body["fei"].copy()

    @property
    def fields(self):
        return self._body["fields"]
