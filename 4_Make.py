#!/usr/bin/env python3
"""Usage:
    4_Make.py [<config_name>] [--target <target>] [--config <config>] [--clean] [--cpus <nr_cpus>] [--help]

    This script builds the given target in the given configuration.

    If no <config_name> is given, the first configuration that already
    has a CMakeCache.txt file will be used.
    If you specify a <config_name> and there is no CMakeCache.txt file
    for that config, 4_Make.py call 3_Generate.py in order to try
    to create one.

    If no <target> is given, the "ALL_BUILD" target will be build.

Options:
    -h --help               Show this
    --target <target>       Specify the build target. For the options see the list below.
    --config <config>       Specify the configuration for multi-config build systems.
                            This is usually Debug or Release.
    --clean                 Use CMakes --clean-first option for the build, which triggers a fresh rebuild.
    --cpus <nr_cpus>        The number of cpu cores that should be used during the build.
                            If no number is given, the number of available physical cores plus the number
                            of hyper-threading cores will be used.

Custom Targets:
    The following custom targets may be available.
    The availability depends on the project configuration.

    Global Targets
    - abi-compliance-checker
    - acyclic
    - ALL_BUILD (Visual Studio) / all (Makefiles)
    - clang-format
    - clang-tidy
    - packageArchives
    - install
    - opencppcoverage
    - pipeline
    - runAllTests
    - runFastTests
    - valgrind
    - ZERO_CHECK (Visual Studio)

    Package Targets
    - abi-compliance-checker_<package-component>
    - clang-format_<binary-target>
    - clang-tidy_<package>
    - packageArchives_<package>
    - opencppcoverage_<package>
    - <package>
    - <package>_fixtures
    - <package>_tests
    - runAllTests_<package>
    - runFastTests_<package>
    - valgrind_<package>
    
"""

import sys
from Sources.CPFBuildscripts.python.docopt import docopt
import Sources.CPFBuildscripts.python.buildautomat as buildautomat

if __name__ == "__main__":
    _ARGS = docopt(__doc__, version='4_Make 1.0')
    _AUTOMAT = buildautomat.BuildAutomat()
    if not _AUTOMAT.make(_ARGS):
        print("Error: Script 4_Make.py failed.")
        sys.exit(2)
    else:
        sys.exit(0)

