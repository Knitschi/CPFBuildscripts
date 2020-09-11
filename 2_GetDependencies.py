#!/usr/bin/env python3
"""Usage: 
    2_GetDependencies.py [<config_name>]

    Running this script runs the conan command

    conan install -pr <config_dir>/ConanProfile-<config_name> -if Configuration/<config_name> Sources --build=missing

    if the file conanfile.txt exists in the deployment-repository's root directory. 
    This command will then download or build the dependencies that are specified in the conanfile.txt
    in the configuration that is specified in the <config_dir>/ConanProfile-<config_name> conan profile file.
"""

import sys
from Sources.CPFBuildscripts.python.docopt import docopt
from Sources.CPFBuildscripts.python import buildautomat

if __name__ == "__main__":
    _ARGS = docopt(__doc__, version='2_GetDependencies 1.0')
    _AUTOMAT = buildautomat.BuildAutomat()
    if not _AUTOMAT.get_dependencies(_ARGS):
        print("Error: Script 2_GetDependencies.py failed.")
        sys.exit(1)
    else:
        sys.exit(0)