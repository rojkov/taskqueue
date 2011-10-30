import os
from setuptools import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "taskqueue",
    version = "0.0.1",
    author = "Dmitry Rozhkov",
    author_email = "dmitry.rojkov@gmail.com",
    description = ("Simple task queue with round robin load balancing."),
    license = "GPL",
    keywords = "task queue",
    url = "http://packages.python.org/an_example_pypi_project",
    packages=['taskqueue'],
    long_description=read('README'),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
        "License :: OSI Approved :: GPL License",
    ],
    entry_points={
        'console_scripts':
            [
                'dispatcher = taskqueue.dispatcher:Application.main',
                'worker = taskqueue.workerpool:Application.main'
            ],
        'worker.plugins':
            [
                'first = taskqueue.plugins.first:Worker.factory',
                'second = taskqueue.plugins.second:Worker.factory',
                'third = taskqueue.plugins.third:Worker.factory'
            ]
    },
)
