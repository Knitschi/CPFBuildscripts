
1_Configure.py
==============

This script instantiates a configuration file in the \c Configuration directory.

Command Line Interface
----------------------


.. code-block:: bash

  Usage: 
      1_Configure.py <config_name> [--inherits <parent_config>] [-D definition]...

      Running this script generates the file

      Configuration/<config_name>.config.cmake

      which contains a set of CMake variables that define one configuration of a CPF project.
      The configuration defines which compiler or make-file generator is used and other arbitrary
      settings. The generated config file can be changed by each developer to tweak the build or
      set different paths to dependencies.

      The short way of using this script is by only giving the <config_name> argument
      which in this case must be the name of one of the existing config file names that
      can be found at the following locations.

      <root>/Configuration
      <root>/Sources/CIBuildConfigurations
      <root>/Sources/CPFCMake/DefaultConfigurations

      If you want to create a configuration with a new name you can also specify
      the --inherits to pass in the parent configuration which allows you to set
      <config_name> freely.

      For more information about configurations see:
      https://knitschi.github.io/CMakeProjectFramework/doxygen/html/d7/d8d/_c_p_f_configuration.html

  Options:

  --inherits <parent_config>  This option must be set to an existing configuration from
                              which variable definitions are inherited. 

  -D definition               This option can be given to set CMake variables
                              int the generated file over the command line.
                              This may be useful on a build-server.
                              <definition> should look something like this:
                              HUNTER_ROOT=/home/hunter_root
                            
  --list                      When this argument is given, the script will list
                              the available existing configurations instead
                              of generating a new file.


