#!/usr/bin/python3

import unittest

import sys
import os
sys.path.append(os.path.dirname(os.path.realpath(__file__)))

from python.buildautomat_unit_tests import *
from python.filesystemaccess_unit_tests import *

if __name__ == '__main__':
    unittest.main()
    