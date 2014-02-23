#!/usr/bin/env python3

from setuptools import setup

import rap

setup(
    name='rap',
    version=rap.__version__,
    description="Register Assembly Programming",
    long_description=open("README.rst").read(),

    classifiers=[
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python :: 3",
        "Topic :: Education",
        "Topic :: Software Development :: Interpreters",
        "Topic :: System :: Emulators",
    ],
    keywords='',
    author='lemon24',
    url='https://github.com/lemon24/rap',
    license='BSD',
    packages=['rap'],
)
