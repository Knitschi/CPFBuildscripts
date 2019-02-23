#!/usr/bin/python3
"""Usage:
    3_Make.py [<config_name>] [--target <target>] [--config <config>] [--clean] [--cpus <nr_cpus>] [--help]

    This script builds the given target in the given configuration.

    If no <config_name> is given, the first configuration that already
    has a CMakeCache.txt file will be used.
    If you specify a <config_name> and there is no CMakeCache.txt file
    for that config, 3_Make.py call 2_Generate.py in order to try
    to create one.

    If no <target> is given, the "ALL_BUILD" target will be build.

Options:
    -h --help               Show this
    --target <target>       Specify the build target.
    --config <config>       Specify the configuration for multi-config build systems.
                            This is usually Debug or Release.
    --clean                 Use CMakes --clean-first option for the build, which triggers a fresh rebuild.
    --cpus <nr_cpus>        The number of cpu cores that should be used during the build.
                            If no number is given, the number of available physical cores plus the number of hyper threaded cores will be used.
"""

import sys
from Sources.CPFBuildscripts.python.docopt import docopt
import Sources.CPFBuildscripts.python.buildautomat as buildautomat

if __name__ == "__main__":
    _ARGS = docopt(__doc__, version='3_Make 1.0')
    _AUTOMAT = buildautomat.BuildAutomat()
    if not _AUTOMAT.make(_ARGS):
        print("Error: Script 3_Make.py failed.")
        sys.exit(2)
    else:
        sys.exit(0)