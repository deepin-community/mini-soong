#!/usr/bin/python3

import sys
from setuptools import setup, find_packages

if sys.version_info < (3, 8, 0):
    sys.exit("Python 3.8.0 is the minimum required version")

setup()
