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
_SCRIPTS = ['1_Configure.py.in', '2_GetDependencies.py.in', '3_Generate.py.in', '4_Make.py.in']

def replacePlaceHolder(filePath, placeHolderDict):
    """
    Replaces substrings in the file that are marked with @<key>@
    with the value of that key in the placeHolderDict.
    """

    # Read in the file
    with open(filePath, 'r') as file :
        filedata = file.read()

    # Replace the target string
    for key in placeHolderDict:
        filedata = filedata.replace('@{0}@'.format(key), placeHolderDict[key])

    # Write the file out again
    with open(filePath, 'w') as file:
        file.write(filedata)

if __name__ == "__main__":
    for scriptTemplate in _SCRIPTS:
        # Copy the script template to the working directory.
        sourcePath = _SCRIPT_DIR + '/' + scriptTemplate
        script = scriptTemplate[:-3] # Remove the .in
        destPath = os.getcwd() + '/' + script

        shutil.copyfile(sourcePath, destPath)
        # Inject the location of CPFBuildscripts into the copied script so imports
        # work independent of the destination. 
        placeHolderDict = {'CPF_BUILDSCRIPTS_DIR': _SCRIPT_DIR}
        replacePlaceHolder(destPath, placeHolderDict)
        # also make the copied file executable
        st = os.stat(destPath)
        os.chmod(destPath, st.st_mode | stat.S_IEXEC)




