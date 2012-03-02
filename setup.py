import os
from setuptools import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "taskqueue",
    version = "0.3.0",
    author = "Dmitry Rozhkov",
    author_email = "dmitry.rojkov@gmail.com",
    description = ("Simple task queue with round robin load balancing."),
    license = "GPL",
    keywords = "task queue",
    url = "http://packages.python.org/an_example_pypi_project",
    packages = ['taskqueue', 'taskqueue.plugins'],
    install_requires = ['pika>=0.9.5', 'python-daemon>=1.5.5'],
    long_description=read('README.rst'),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
        "License :: OSI Approved :: GPL License",
    ],
    entry_points={
        'console_scripts':
            [
                'dispatcher = taskqueue.dispatcher:Dispatcher.main',
                'worker = taskqueue.workerpool:WorkerPool.main'
            ],
        'worker.plugins':
            [
                'first = taskqueue.plugins.first:Worker.factory',
                'second = taskqueue.plugins.second:Worker.factory',
                'simplebuilder = taskqueue.plugins.simplebuilder:Worker.factory',
                'simpledownloader = taskqueue.plugins.simpledownloader:Worker.factory',
                'third = taskqueue.plugins.third:Worker.factory'
            ],
        'workitems': [
                'application/x-ruote-workitem = taskqueue.workitem:RuoteWorkitem',
                'application/x-basic-workitem = taskqueue.workitem:BasicWorkitem'
            ]
    },
    test_suite = "tests",
    tests_require = ['mock>=0.8.0']
)
