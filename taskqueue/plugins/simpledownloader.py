import logging
import json
import os

from restkit import Resource, BasicAuth

from taskqueue.worker import BaseWorker

LOG = logging.getLogger(__name__)

class Worker(BaseWorker):

    def handle_task(self, workitem):
        LOG.debug("Body: %r" % workitem)
        pkgname = workitem['fields']['pkgname']
        pkgkey = ["%(name)s/%(version)s/%(id)s" % p
                  for p in workitem['fields']['packages']
                  if p['name'] == pkgname][0]
        LOG.debug("PKey: %s" % pkgkey)
        user = workitem['fields']['user']
        repo = workitem['fields']['repo']
        auth = BasicAuth(user, "qwerty")
        res = Resource("http://localhost:9000", filters=[auth])
        resp = res.get(path="/packages/%s" % pkgkey,
                       headers={'accept': 'application/json'})
        pkg = json.loads(resp.body_string())
        LOG.debug("Package to download: %r" % pkg)
        workitem['fields']['pkgversion'] = pkg['version']
        for f in pkg['files']:
            resp = res.get(path="/users/%s/repos/%s/slices/%s/%s/%s/%s" %
                           (user, repo, workitem['fields']['slice_id'],
                            pkg['name'], pkg['version'], f['name']))
            with resp.body_stream() as body:
                with open(os.path.join(workitem['fields']['workdir'],
                                       f['name']), 'wb') as pf:
                    for block in body:
                        pf.write(block)
        return workitem
