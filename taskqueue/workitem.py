"""
Workitems incapsulate algorithms used to parse bodies of AMQP messages
received by dispatchers and workers.

Taskqueue comes with two predefined classes for workitems:
:class:`BasicWorkitem` and :class:`RuoteWorkitem`. The former one exists
for debugging and demonstration purposes mostly and the latter was developed
to integrate Taskqueue with Ruote. It is possible to register your own
workitem class to extract, for example, pickled python objects from
AMQP message body in the way similar to how Celery does it.

The requirements for a Workitem class are:

    1. the class should implement the following methods:

       - `loads(blob::Blob)` to parse AMQP message bodies,
       - `dumps()::Blob` to convert workitem's state back to AMQP message body,
       - `set_error(error::string)` to set error message,
       - `set_trace(trace::string)` to set traceback,
       - property `worker_type` to let the dispatcher know where to
         dispatch the workitem to;

    2. the class needs to be registered as a setuptool resource under the group
       name `workitems`::

            setup(
                entry_points={
                    'workitems': [
                        'application/x-your-workitem = yourpackage.yourmodule:YourWorkitemClass'
                    ]
                }
            )
"""

import logging
import json

from pkg_resources import iter_entry_points

LOG = logging.getLogger(__name__)

#: Default content type
DEFAULT_CONTENT_TYPE = 'application/json'

#: Default mappings of workitem types
DEFAULT_CONTENT_TYPE_MAP = {
    'application/json': 'application/x-ruote-workitem',
    'text/plain':       'application/x-basic-workitem'
}

class WorkitemError(Exception):
    pass

def get_workitem(amqp_header, amqp_body, ctype_map=None,
                 default_ctype=DEFAULT_CONTENT_TYPE):
    """Constructs workitems of a certain type.

    :param amqp_header: AMQP message header
    :type amqp_header: pika.frame.Header
    :param amqp_body: AMQP message body
    :type amqp_body: blob
    :param ctype_map: workitem type mapping
    :type ctype_map: dictionary
    :param default_ctype: default workitem type
    :type default_ctype: string
    """
    LOG.debug("get_workitem(%s, '%s')" % (amqp_header, amqp_body))

    if amqp_header.content_type:
        ctype = amqp_header.content_type
    else:
        LOG.warning("header doesn't have Content-type. Assume default '%s'" %
                    default_ctype)
        ctype = default_ctype

    if ctype_map is None:
        ctype_map = DEFAULT_CONTENT_TYPE_MAP

    if isinstance(ctype_map, basestring):
        try:
            ctype_map = dict([[token.strip() for token in pair.split('=', 1)]
                                for pair in ctype_map.split(',')])
        except ValueError:
            raise WorkitemError("can't parse content type map '%s'" %
                                ctype_map)
        LOG.debug("default content type got overridden with %r" % ctype_map)

    ctype = ctype_map.get(ctype, ctype)

    workitem = None
    # look for a Workitem class
    for entry in iter_entry_points(group='workitems', name=ctype):
        LOG.debug("found %r" % entry)
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
            LOG.warning("Can't parse workitem with the plugin '%s.%s'" %
                        (entry.module_name, cls.__name__))
            workitem = None
            continue

    if workitem is None:
        raise WorkitemError("No suitable plugin found for workitem of "
                            "the type '%s'" % ctype)
    return workitem

class BasicWorkitemError(WorkitemError):
    pass

class BasicWorkitem(object):
    """Basic workitem.

    The format of a message body understandable by this class is a simple
    string: `<worker_type> <the rest of the body>`.
    """

    mime_type = 'application/x-basic-workitem'

    def __init__(self):
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

    def set_error(self, error):
        self._body += "\nError: %s" % error

    def set_trace(self, trace):
        self._body += "\nTrace: %s" % trace

class RuoteWorkitemError(WorkitemError):
    pass

class RuoteWorkitem(object):
    """Ruote workitem.

    This class is used to parse JSON-based Ruote workitems like:

    .. code-block:: guess

        {
            "re_dispatch_count": 0,
            "participant_name": "hardworker",
            "wf_revision": null,
            "fields": {
                "repo": "testrepo1",
                "pkgname": "python-riak",
                "pkgversion": "1.2.1",
                "branch": "master2",
                "workdir": "/home/rozhkov/tmp",
                "dispatched_at": "2012-03-04 14:00:22.861908 UTC",
                "params": {
                    "participant_options": {
                        "forget": false,
                        "queue": "taskqueue"
                    },
                    "worker_type": "simplebuilder",
                    "ref": "hardworker"
                },
                "user": "vasya"
            },
            "wf_name":null,
            "fei": {
                "wfid": "20120304-bejeruwodi",
                "engine_id": "engine",
                "expid": "0_1_3",
                "subid": "8079afecd0256e8280b355455ea3435f"
            }
        }
    """

    mime_type = 'application/x-ruote-workitem'

    def __init__(self):
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

    def set_error(self, error):
        self._body["error"] = error

    def set_trace(self, trace):
        self._body["trace"] = trace

    @property
    def fei(self):
        # fei is a read-only attribute
        return self._body["fei"].copy()

    @property
    def fields(self):
        return self._body["fields"]
