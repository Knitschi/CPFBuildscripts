
.. _0_CopyScripts:

0_CopyScripts.py
================

The :code:`0_CopyScripts.py` script installs the other python scripts from CPFBuildscripts into the root directory of your CPF project.
This script must be executed once after cloning a CPF project. The script does not take any arguments.

Command Line Interface
----------------------


.. code-block:: bash

    Usage:
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



Versioning
----------

The copying of the scripts brings the problem, that the copied scripts can be outdated when the client project
updates CPFBuildscripts. All four copied scripts have a mechanism in place that compares the major version number
of the CPFBuildscripts version from which the script was originally copied with major version number of the
CPFBuildscripts package that it currently calls. If these are not the same, the scripts will abort with an error.

This means that developers of CPFBuildscripts must increment the major version if changes are made that break existing
copies of the four scripts.

