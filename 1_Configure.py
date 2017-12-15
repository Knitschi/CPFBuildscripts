#!/usr/bin/python3
"""Usage: 1_Configure.py <config_name> [--inherits parent_config] [-D definition]...

    Running this script generates the file

    Configuration/<config_name>.config.cmake

    which contains developer specific CMake variables that are required to generate the
    make-files for the CppCodeBase. Among others these include the used CMake generator
    and the compilation toolchain. When doing the configure step, <config_name> can be
    freely chosen. The 2_Generate.py and 3_Make.py step will later take the chosen
    <config_name> to create makefiles or make the created configuration.
    The easiest way to use this is to run the script without options and then edit the
    generated file. Setting the configuration over the command line options is useful on
    the CI-server.

Options:

--inherits parent_config    This option can be given to specify another configuration from
                            which variable definitions are inherited. For now the value must
                            be the base-name of a <base-name>.config.cmake file.
                            The file must be located in one of the following locations.
                            <cppcodebase-root>/Configuration
                            <cppcodebase-root>/Sources
                            <cppcodebase-root>/Sources/CppCodeBase/DefaultConfigurations


-D definition               This option can be given to set cmake variables
                            over the command line. <definition> should look
                            something like this:
                            HUNTER_ROOT=/home/hunter_root
"""

import sys
from Sources.CppCodeBaseBuildscripts.cppcodebasebuildscripts.docopt import docopt
from Sources.CppCodeBaseBuildscripts.cppcodebasebuildscripts import buildautomat

if __name__ == "__main__":
    _ARGS = docopt(__doc__, version='1_Configure 1.0')
    _AUTOMAT = buildautomat.BuildAutomat()
    if not _AUTOMAT.configure(_ARGS):
        print("Error: Script 1_Configure.py failed.")
        sys.exit(2)
