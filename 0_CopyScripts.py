
# This script is used to copy the base build scripts into the root directory of a CppCodeBase project.
# 

import shutil
import os

if __name__ == "__main__":
    dirOfScript = os.path.dirname(os.path.realpath(__file__))
    scripts = ['1_Configure.py','2_Generate.py','3_Make.py']
    for script in scripts:
        shutil.copyfile(dirOfScript + '/' + script , dirOfScript + '/../../' + script)
