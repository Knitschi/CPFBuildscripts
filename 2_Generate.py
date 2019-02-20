#!/usr/bin/python3
"""Usage:
    2_Generate.py [<config_name>] [--clean] [--help]

    Running this script will run CMake to generate the "make-files" for the given
    configuration. <config_name> must be the base-name of a configuration file
    found in the "Configuration" sub-directory. After calling this script,
    the makefiles can be found in the "Generated/<config-name> sub-directory.
    When the <config_name> is given, an possibly existing "Generated/<config-name>"
    directory will be deleted before running CMake. If the <config_name> option
    is not given, the script will choose the first available config in the
    "Configuration" directory. It will also not delete the "Generated/<config-name>"
    directory, so this can be used for running CMake incrementally.
    Note that when calling this for the first time, this step will download and
    compile all dependencies that are handled with the hunter package manager,
    so the execution may take some time.

Options:
    -c --clean              Deletes the Generated/<config_name> directory before 
                            running CMake to get a clean build-tree.
    -h --help               Shows this page.

"""
import sys
from Sources.CPFBuildscripts.python.docopt import docopt
from Sources.CPFBuildscripts.python import buildautomat

if __name__ == "__main__":
    _ARGS = docopt(__doc__, version='2_Generate 1.0')
    _AUTOMAT = buildautomat.BuildAutomat()
    if not _AUTOMAT.generate_make_files(_ARGS):
        print("Error: Script 2_Generate.py failed.")
        sys.exit(2)
    else:
        sys.exit(0)