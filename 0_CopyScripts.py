#!/usr/bin/env python3
"""Usage:
    0_CopyScripts.py --CPFCMake_DIR <dir> --CIBuildConfigurations_DIR <dir>

    This script is used to copy the build scripts

    1_Configure.py
    2_GetDependencies.py
    3_Generate.py
    4_Make.py

    into the root directory of a CMakeProjectFramework repository.

Options:

--CPFCMake_DIR <dir>                The path to the directory of the CPFCMake package. It can be absolute or relative to
                                    the projects root directroy.
--CIBuildConfigurations_DIR <dir>   The path to the  directory that contains the .config.cmake files that
                                    contain the default project configurations. It can be absolute or relative to
                                    the projects root directroy.
"""

import shutil
import os
import stat
from python.docopt import docopt
from python import buildautomat


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


def toAbsolutePath(root_dir, path):
    if not os.path.isabs(str(path)):
        return root_dir + '/' + path
    return path


if __name__ == "__main__":

    _ARGS = docopt(__doc__, version='1_Configure 1.0')

    for scriptTemplate in _SCRIPTS:
        # Copy the script template to the working directory.
        sourcePath = _SCRIPT_DIR + '/' + scriptTemplate
        script = scriptTemplate[:-3] # Remove the .in
        cpfRootDir = os.getcwd()
        destPath = cpfRootDir + '/' + script
        shutil.copyfile(sourcePath, destPath)

        # Get the absolute paths to the CPFCMake and CIBuildConfigurations dependencies.
        abs_CPFCMake_dir = toAbsolutePath(cpfRootDir, _ARGS['--CPFCMake_DIR']).replace('\\','/')
        abs_CIBuildConfigurations_dir = toAbsolutePath(cpfRootDir, _ARGS['--CIBuildConfigurations_DIR']).replace('\\','/')

        _automat = buildautomat.BuildAutomat(
            cpfRootDir,
            abs_CPFCMake_dir,
            abs_CIBuildConfigurations_dir
        )
        cpf_buildscripts_version = _automat.get_package_version(_SCRIPT_DIR)

        # Inject the location of CPFBuildscripts into the copied script so imports
        # work independent of the destination. 
        placeHolderDict = {
            'CPFBuildscripts_DIR': _SCRIPT_DIR.replace('\\','/'),
            'CPFBuildscripts_VERSION': cpf_buildscripts_version,
            'CPFCMake_DIR': abs_CPFCMake_dir,
            'CIBuildConfigurations_DIR': abs_CIBuildConfigurations_dir,
            }
        replacePlaceHolder(destPath, placeHolderDict)
        # also make the copied file executable
        st = os.stat(destPath)
        os.chmod(destPath, st.st_mode | stat.S_IEXEC)




