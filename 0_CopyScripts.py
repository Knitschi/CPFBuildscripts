#!/usr/bin/env python3
"""
This script is used to copy the build scripts

1_Configure.py
3_Generate.py
4_Make.py

into the root directory of a CMakeProjectFramework repository.
"""

import shutil
import os
import stat

_SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
_SCRIPTS = ['1_Configure.py', '2_GetDependencies.py', '3_Generate.py', '4_Make.py']

if __name__ == "__main__":
    for script in _SCRIPTS:
        sourcePath = _SCRIPT_DIR + '/' + script
        destPath = _SCRIPT_DIR + '/../../' + script
        shutil.copyfile(sourcePath, destPath)
        # also make the copied file executable
        st = os.stat(destPath)
        os.chmod(destPath, st.st_mode | stat.S_IEXEC)

