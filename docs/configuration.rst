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

The example below explains all three cases:

.. code-block:: guess

    [DEFAULT]
    global_option_name = some value

    [taskqueue]
    common_option = this value is common for all worker instances

    [worker_worker1]
    some_worker1_option = this value is common for all instances of worker1 workers

    [worker_worker2]
    some_worker2_option = this value is common for all instances of worker2 workers
    subgroups = group1, group2

    [worker_worker2_group1]
    group1_specific_option = only the instances in group1 of worker2 type will get this option
    common_option = this overrides the value set in the section taskqueue

Effective worker settings are available in the attribute :attr:`BaseWorker.settings`.

Currently Taskqueue reserves five option names for its internal use:
`workers`, `results_routing_key`, `user`, `instances` and `subgroups`.

workers
    Defines a comma-separated list of worker plugins enabled on the host. By default
    this option contains `*` which means that all installed plugins are enabled.
    This option make sense only in the context of the section `taskqueue`.

results_routing_key
    Ruouting key for results returned by workers. Default value is `results`.

user
    Defines effective UID of worker processes. If not specified the worker pool
    manager doesn't change worker's UID.

instances
    This option defines how many worker processes of a particular type
    or a subgroup should be started. The default value is `1`.

subgroups
    Introduces a comma-separated list of subgroups of worker processes of the same type.
    Settings for each group are defined in a respective section.

Logging configuration is described in the manual for python standard library
`logging`: http://docs.python.org/library/logging.config.html#module-logging.config

