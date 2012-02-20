Configuration
=============

The only configuration file needed for Taskqueue is
`/etc/taskqueue/config.ini`. You can point your dispatcher and worker pool
manager to an alternative configuration file with the command line option
`--config`.

The configuration file format understood by Taskqueue is based on python's
`configparser` functionality and is known as INI format.

The simplest config is an empty file.

You can provide settings for

  1. all workers,
  2. a specific type of workers,
  3. a named group of workers of some type.

The example below explains all three cases::

    [DEFAULT]
    global_option_name: some value

    [worker1]
    some_worker1_option: this value is common for all instances of worker1 workers

    [worker2]
    some_worker2_option: this value is common for all instances of worker2 workers
    workers: group1, group2

    [worker2_group1]
    group1_specific_option: only the instances in group1 of worker2 type will get this option

Effective worker settings are available in the attribute :attr:`BaseWorker.settings`.

Currently Taskqueue reserves three option names for its internal use:
`results_routing_key`, `user` and `workers`.

results_routing_key
    Ruouting key for results returned by workers. Default value is `results`.

user
    Defines effective UID of worker processes. If not specified the worker pool
    manager doesn't change worker's UID.

workers
    This option defines how many worker processes of a particular type
    or a group should be started. The default value is `1`. In the context of
    worker types this option may have a string value with comma-seprated
    enumeration of worker groups.

.. note::
    In future the enumeration of worker groups might be moved to
    a dedicated option (i.e `groups`) to avoid ambiguity.

Logging configuration is described in the manual for python standard library
`logging`: http://docs.python.org/library/logging.config.html#module-logging.config

