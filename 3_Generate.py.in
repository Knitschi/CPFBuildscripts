#!/usr/bin/env python3
"""Usage:
    3_Generate.py [<config_name>] [--clean] [--help]

    Running this script will run CMake to generate the "make-files" for the given
    configuration. <config_name> must be the base-name of a configuration file
    found in the "<root>/Configuration" directory. 
    After calling this script, the makefiles can be found in the "<root>/Generated/<config-name> directory.
    If <config_name> is a configuration that does not yet exist in the
    "<root>/Configuration" directory the script will run "1_Configure <config_name>"
    in order to create it.

Options:
    -c --clean              Deletes the Generated/<config_name> directory before 
                            running CMake to get a clean build-tree.
    -h --help               Shows this page.

"""
import sys
sys.path.append('@CPF_BUILDSCRIPTS_DIR@')

from python.docopt import docopt
from python import buildautomat

if __name__ == "__main__":
    _ARGS = docopt(__doc__, version='3_Generate 1.0')
    _AUTOMAT = buildautomat.BuildAutomat()
    if not _AUTOMAT.generate_make_files(_ARGS):
        print("Error: Script 3_Generate.py failed.")
        sys.exit(2)
    else:
        sys.exit(0)

