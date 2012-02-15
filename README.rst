Simple distributed task queue.

Features
========

 * no registration is required for installed worker pluggins
 * round robin load balancing
 * crashed workers get restarted
 * task queue works as soon as dispatcher and worker pool components
   get installed

Design
======

Task queue consists of two major components: a dispatcher and a worker
manager. The dispatcher listens to messages in the AMQP queue "taskqueue".
When a new message arrives the dispatcher parses its body, extracts
the workitem and the type of worker needed to handle the workitem.
Then the dispatcher resends the workitem to the queue "worker_<worker_type>".

For every installed plugin the worker manager starts one or more worker
processes according to the config file `/etc/taskqueue/config.ini`. For example
for the following config::

    [DEFAULT]
    workers: 1

    ; Workers
    [worker1]
    workers: 3

    [worker2]
    workers: bifh1, bifh2

    [worker2_bifh1]
    workers: 1
    user: bifh1

    [worker2_bifh2]
    workers: 1
    user: bifh2

the worker manager creates 3 identical instances of the type `worker1` and
2 instances of the type `worker2` configured to run under users `bifh1` and
`bifh2`. The worker processes of the type `worker1` listen to the queue
`worker_worker1` and the worker processes of the type `worker2` listen to the
queue `worker_worker2`.

If a worker process gets crashed the worker manager restarts it.

The following code in the package `extpackage.workerext` defines a new worker
plugin::

    from taskqueue.worker import BaseWorker

    class Worker(BaseWorker):
        def handle_task(self, body):
            # put meat here
            return do_something_heavy(body)

The return value of Worker.handle_task() is sent back to AMQP with the routing
key `results` though the key is configurable (i.e. when taskqueue is used with
Ruote together then the name of the key should be `ruote_workitems`).

The plugin needs to be registered as a pluggable resource in the egg's
`setup.py`::

    from setuptools import setup

    setup(
        ...
        entry_points={
            'worker.plugins':
                ['workerext = extpackage.workerext:Worker.factory']
        }
    )

Installation
============

Unpack the tarball, then::

    $ cd taskqueue
    $ dpkg-buildpackage -rfakeroot

The commands above will produce three packages: `python-taskqueue-common`,
`python-taskqueue-dispatcher` and `python-taskqueue-workerpool`.

Update AMQP settings in the section `amqp` of the file
`/etc/taskqueue/config.ini`.

Start the task queue::

    # /etc/init.d/python-taskqueue-dispatcher start
    # /etc/init.d/python-taskqueue-workerpool start

The packages `python-taskqueue-dispatcher` and `python-taskqueue-workerpool`
can be installed on different hosts. It's advised to install
`python-taskqueue-dispatcher`  on at least two hosts to make the setup
more reliable. And `python-taskqueue-workerpool` should be installed on
as many hosts as possible for better load balancing.
