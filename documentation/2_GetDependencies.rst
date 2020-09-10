
2_GetDependencies.py
====================

This script runs the CMake generate step that creates the native "make files" for you chosen generator.

Command Line Interface
----------------------

.. code-block:: bash

    Usage: 
        2_GetDependencies.py <config_name>

        Running this script runs the conan command

        conan install -pr <config_dir>/ConanProfile-<config_name> -if Configuration/<config_name> Sources --build=missing

        if the file conanfile.txt exists in the deployment-repository's root directory. 
        This command will then download or build the dependencies that are specified in the conanfile.txt
        in the configuration that is specified in the <config_dir>/ConanProfile-<config_name> conan profile file.