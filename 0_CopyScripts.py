#!/usr/bin/python3
"""
This script is used to copy the build scripts

1_Configure.py
2_Generate.py
3_Make.py

into the root directory of a CppCodeBase project.
"""

import shutil
import os

_SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
_SCRIPTS = ['1_Configure.py', '2_Generate.py', '3_Make.py']

if __name__ == "__main__":
    for script in _SCRIPTS:
        shutil.copyfile(_SCRIPT_DIR + '/' + script, _SCRIPT_DIR + '/../../' + script)
