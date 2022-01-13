#!/usr/bin/python3
"""
This module provides the BuildAutomat class which implements the functionality
of the primary build scripts.
"""

import time
import os
import datetime
from pathlib import PurePosixPath

from . import filelocations
from . import miscosaccess
from . import filesystemaccess


_CONFIG_NAME_KEY = '<config_name>'
_INHERITS_KEY = '--inherits'
_LIST_KEY = '--list'
_TARGET_KEY = '--target'
_CONFIG_KEY = '--config'
_CLEAN_KEY = '--clean'
_CPUS_KEY = '--cpus'

class BuildAutomat:
    """
    The entry point for running the various steps of the make-pipeline.
    """
    def __init__(self, cpf_root_dir, cpf_cmake_dir, cibuildconfigurations_dir, filesystemaccess=filesystemaccess.FileSystemAccess()):

        # Object to operate on the file-system
        self.m_fs_access = filesystemaccess

        if not self.m_fs_access.exists(cpf_cmake_dir):
            raise Exception("The given directory CPFCMake_DIR \"{0}\" does not exist.".format(cpf_cmake_dir))

        if not self.m_fs_access.exists(cibuildconfigurations_dir):
            raise Exception("The given directory CIBuildConfigurations_DIR \"{0}\" does not exist.".format(cibuildconfigurations_dir))

        # Get information about where is what in the cpf
        self.m_file_locations = filelocations.FileLocations(cpf_root_dir, cpf_cmake_dir, cibuildconfigurations_dir)
        # Object to access other os functionality
        self.m_os_access = miscosaccess.MiscOsAccess()

    def cpf_buildscripts_version_is_compatible_to_copied_script(self, copied_script_version):
        """
        Returns true if the first digit of the CPFBuildscripts version number is still the same
        as the first digit of the version number of the copied script in the cpf root directory.

        This is used to catch the case that CPFBuildscripts made an incompatible change that broke
        the copied build scripts.
        """
        copied_script_major_version = copied_script_version.split('.')[0]

        buildscripts_dir = os.path.dirname(os.path.realpath(__file__)).replace('\\', '/')  + '/..'
        build_scripts_version = self.get_package_version(buildscripts_dir)
        package_major_version = build_scripts_version.split('.')[0]

        is_compatible = copied_script_major_version == package_major_version
        if not is_compatible:
            print("Error: Script 1_Configure.py at version {0} is no longer compatible to your CPFBuildscripts package at version {1}. You need to run 0_CopyScripts.py again to update your local build-scripts.".format(copied_script_version, build_scripts_version))

        return is_compatible

    def get_package_version(self, package_dir):
        package_dir = package_dir.replace('\\', '/')
        cmake_command = "cmake -D PACKAGE_DIR=\"{0}\" -P \"{1}\"".format(package_dir,self.m_file_locations.GET_PACKAGE_VERSION_SCRIPT)
        return self.m_os_access.execute_command_output(cmake_command, print_output=miscosaccess.OutputMode.ON_ERROR)[0]

    def configure(self, args):
        """
        Runs a cmake script in order to generate the developer cmake configuration file.
        """
        try:
            args = self._add_quotes_to_d_options(args)

            # Assemble the cmake command for calling the cmake script that does the work.
            cmake_command = ""
            if args[_LIST_KEY]:
                cmake_command = "cmake -DLIST_CONFIGURATIONS=TRUE" \
                    + " -DCPF_ROOT_DIR=" + _quotes(str(self.m_file_locations.cpf_root_dir)) \
                    + " -DCPFCMake_DIR=" + _quotes(str(self.m_file_locations.cpf_cmake_dir)) \
                    + " -DCIBuildConfigurations_DIR=" + _quotes(str(self.m_file_locations.cibuildconfigurations_dir)) \

            else:
                if not args[_CONFIG_NAME_KEY]:
                    return self._print_exception("Required argument {0} is missing.".format(_CONFIG_NAME_KEY))

                inherited_config = args[_INHERITS_KEY]
                if not inherited_config:
                    inherited_config = args[_CONFIG_NAME_KEY]

                # add basic options
                cmake_command = "cmake" \
                            + " -DDERIVED_CONFIG=" + args[_CONFIG_NAME_KEY] \
                            + " -DPARENT_CONFIG=" + inherited_config \
                            + " -DCPF_ROOT_DIR=" + _quotes(str(self.m_file_locations.cpf_root_dir)) \
                            + " -DCPFCMake_DIR=" + _quotes(str(self.m_file_locations.cpf_cmake_dir)) \
                            + " -DCIBuildConfigurations_DIR=" + _quotes(str(self.m_file_locations.cibuildconfigurations_dir)) \

                # Get the variable definitions
                definitions = args["-D"]
                if definitions:
                    cmake_arg_definitions = []
                    for definition in definitions:
                        cmake_arg_definitions.append("-D" + definition)
                    cmake_command += " " + " ".join(cmake_arg_definitions)

            cmake_command += " -P " + _quotes(self.m_file_locations.GENERATE_CONFIG_FILE_SCRIPT)

            return self.m_os_access.execute_command(cmake_command, print_command=True) # Print the command which may be helpfull when the script is called from other tools.

        except BaseException as exception:
            return self._print_exception(exception)


    def get_dependencies(self, args):
        """
        Runs conan to get external binary packages.
        """
        try:

            if not self.m_fs_access.exists(self.m_file_locations.get_full_path_conan_file()):
                # If there is no conanfile we consider this step to be not necessary an always return true.
                self.m_os_access.print_console("Found no conanfile. No external packages were acquired.")
                return True
            else:
                # Get the conan packages for the specified configuration.
                config_name = self._get_config_name_and_run_config_step_if_needed(args)
                self._call_conan_install(config_name)

            return True

        except BaseException as exception:
            return self._print_exception(exception)

    def generate_make_files(self, args):
        """
        Runs the cmake to create the makefiles.
        """
        try:
            start_time = time.perf_counter()

            config_name = self._get_config_name_and_run_config_step_if_needed(args)

            # If a conanfile exists we need to get the dependencies before we can generate.
            #if self.m_fs_access.exists(self.m_file_locations.get_full_path_conan_file()):
            #    if not self.get_dependencies(args):
            #        return False

            # Clean the build-tree if demanded
            if args[_CLEAN_KEY]:
                self._clear_makefile_dir(config_name)

            if self._has_existing_cache_file(config_name):
                # Do the incremental generate if possible
                self._call_cmake_for_existing_cache_file(config_name)
            else:
                # Do the full generate if no cache file is available.
                self._call_cmake_with_full_arguments(config_name)

            _print_elapsed_time(self.m_os_access, start_time, "Generating the make-files took")
            self.m_os_access.print_console('SUCCESS!')
            
            return True

        except BaseException as exception:
            return self._print_exception(exception)


    def make(self, args):
        """
        Uses CMake to make the code-base using the given make configuration.
        """
        try:
            start_time = time.perf_counter()

            config_name = args[_CONFIG_NAME_KEY]
            if config_name:
                # Try to generate a cache file if it does not yet exist.
                if (not self._has_existing_cache_file(config_name)) or (not self._developer_config_file_exists(config_name)):
                    generateArgs = {
                        _CONFIG_NAME_KEY : config_name,
                        _CLEAN_KEY : False
                    }
                    if not self.generate_make_files(generateArgs):
                        return self._print_exception('Error: Could not find the CMakeCache.txt file for the given configuration.')
            else:
                config_name = self._get_first_config_that_has_cache_file()
                if not config_name:
                    return self._print_exception("No existing CMakeCache.txt file found. You need to run 3_Generate.py before running 4_Make.py")

            # We not have a configuration with a cache file and can call cmake to build it.
            cmake_build_command = self._get_cmake_build_command(config_name, args)
            return_value = self.m_os_access.execute_command(cmake_build_command)

            # Print some final output.
            _print_elapsed_time(self.m_os_access, start_time, "The build took")
            if return_value:
                self.m_os_access.print_console('SUCCESS!')

            return return_value

        except BaseException as exception:
            return self._print_exception(exception)


###############################################################################################################

    def _add_quotes_to_d_options(self, args):
        """
        This is necessary because docopt will loose quotes around definitions that contain spaces.
        """
        d_options = args['-D']
        if d_options:
            for index, option in enumerate(d_options):
                if '=' not in option:
                    raise Exception('-D option "' + option + '" does not seem to be a valid definition because of a missing "=" character.')
                definition = option.split('=')[1]
                if ' ' in definition:
                    cmake_variable = option.split('=')[0]
                    d_options[index] = cmake_variable + '=' + _quotes(definition)
        args['-D'] = d_options
        return args

    def _get_inherit_option(self, args):
        """
        Returns the argument or the default inheritance depending on the system.
        """
        inherit_option = args['--inherits']
        if not inherit_option:
            inherit_option = self.m_os_access.system()
        return inherit_option

    def _print_exception(self, exception):
        #print('---------------- ' + str(exception))
        self.m_os_access.print_console(str(exception))
        return False

    def _get_config_name_and_run_config_step_if_needed(self, args):
        config_name = args[_CONFIG_NAME_KEY]
        if config_name:
            if not self._developer_config_file_exists(config_name):
                configureArgs = {
                    _CONFIG_NAME_KEY: config_name,
                    _INHERITS_KEY: None,
                    _LIST_KEY: False,
                    '-D': []
                }
                if not self.configure(configureArgs):
                    raise Exception('Error: The given configuration {0} does not exist.'.format(config_name))
            return config_name
        else:
            return self._get_first_existing_config_name()

    def _get_first_existing_config_name(self):
        """
        The function will return the first config for which a config file and a CMakeCache.txt file exists.
        If there is no config for which a CMakeCache.txt exists, it will return the first config in the
        Configurations directory.
        """
        config_file_configs = self._get_existing_config_file_configs()
        if not config_file_configs:
            raise Exception('Error: You need to specify a <config_name> if there is no config file in <root>/Configuration.')
        return config_file_configs[0]

    def _get_existing_config_file_configs(self):
        configs = []
        if self.m_fs_access.isdir(self.m_file_locations.get_full_path_configuration_folder()):
            entries = self.m_fs_access.listdir(self.m_file_locations.get_full_path_configuration_folder())
            for entry in entries:
                full_entry_path = self.m_file_locations.get_full_path_configuration_folder() / entry
                config_file_ending = self.m_file_locations.get_config_file_ending()
                length_ending = len(config_file_ending)
                ending = entry[-length_ending:]
                if self.m_fs_access.isfile(full_entry_path) and ending == config_file_ending:
                    length = len(entry)
                    configs.append(entry[:(length - length_ending)])
        return configs

    def _developer_config_file_exists(self, config):
        config_file = self.m_file_locations.get_full_path_configuration_folder() / (config + self.m_file_locations.get_config_file_ending())
        return self.m_fs_access.isfile(config_file)

    def _get_first_config_that_has_cache_file(self):
        config_file_configs = self._get_existing_config_file_configs()
        for config in config_file_configs:
            if self._has_existing_cache_file(config):
                return config
        return None

    def _has_conanfile(self):
        return self.m_fs_access.exists(self.m_file_locations.get_full_path_conan_file())

    def _call_conan_install(self, config_name):
        """
        runs the 
        
        conan install -pr conan-profile -if generated-files-dir source-dir --build=missing
        
        command
        """
        conanProfilePath = self.m_file_locations.get_full_path_source_folder() / ('CIBuildConfigurations/ConanProfile-' + config_name)

        if not self.m_fs_access.exists(conanProfilePath):
            # Todo: Clear how profiles are handled.
            raise Exception("2_GetDependencies.py currently expects a conan profile file {0} to exist.".format(conanProfilePath))

        conan_command = "conan install -pr {0} -if {1} {2} --build=missing".format(
            _quotes(conanProfilePath),
            _quotes(self.m_file_locations.get_full_path_conan_generated_cmake_files_dir(config_name)),
            _quotes(self.m_file_locations.get_full_path_cpf_root()))

        if not self.m_os_access.execute_command(conan_command):
            raise Exception("The python script failed because the call to conan failed!")

    def _has_existing_cache_file(self, config_name):
        cache_file_path = self.m_file_locations.get_full_path_generated_folder() / config_name / "CMakeCache.txt"
        return self.m_fs_access.isfile(cache_file_path)

    def _clear_makefile_dir(self, config_name):
        """
        Deletes the make folder to make sure that we start from scratch.
        """
        full_config_path = self.m_file_locations.get_full_path_config_makefile_folder(config_name)
        if self.m_fs_access.exists(full_config_path):
            self.m_fs_access.rmtree(full_config_path)

    def _call_cmake_with_full_arguments(self, config_name):
        """
        Assembles the correct arguments for cmake and executes the cmake generate step
        """

        makefile_directory = self.m_file_locations.get_full_path_config_makefile_folder(config_name)
        sources_directory = self.m_file_locations.get_full_path_source_folder()
        full_path_config_file = self.m_file_locations.get_full_path_config_file(config_name)

        command = (
            "cmake"
            # set the cmakelists root directory
            " -H" + _quotes(sources_directory) +
            # set the folder for the generated make files
            " -B" + _quotes(makefile_directory) +
            # set the generator (makefileType)
            " -C" + _quotes(full_path_config_file) +
            # Generate the .dot file that is used to document the target dependencies.
            " --graphviz="+ _quotes(makefile_directory  / self.m_file_locations.TARGET_DEPENDENCIES_DOT_FILE_NAME)
            )

        if not self.m_os_access.execute_command(command):
            raise Exception("The python script failed because the call to cmake failed!")

    def _call_cmake_for_existing_cache_file(self, config_name):
        """
        runs CMake and uses the cached variables from the CMakeCache file.
        """
        makefile_directory = self.m_file_locations.get_full_path_config_makefile_folder(config_name)
        full_command = (
            "cmake " + _quotes(makefile_directory) +
            " --graphviz="+ _quotes(makefile_directory / self.m_file_locations.TARGET_DEPENDENCIES_DOT_FILE_NAME)
            )

        if not self.m_os_access.execute_command(full_command):
            raise Exception("The python script failed because the call to cmake failed!")

    def _get_cmake_build_command(self, config_name, args):
        """
        Assembles a cmake command line call to build the given configuration.
        """
        # get command argument values
        is_clean_build = args[_CLEAN_KEY]
        target = args[_TARGET_KEY]
        config = args[_CONFIG_KEY]
        nr_cpus = args[_CPUS_KEY]
        if not nr_cpus:
            nr_cpus = str(self.m_os_access.cpu_count())

        # now assemble the command
        makefile_directory = self.m_file_locations.get_full_path_config_makefile_folder(config_name)
        command = 'cmake --build ' + _quotes(makefile_directory)

        if target:
            command += ' --target ' + target

        if config:
            command += ' --config ' + config

        if is_clean_build:
            command += ' --clean-first'

        command +=' --parallel ' + nr_cpus

        return command

########### free functions #########################################################################
def _quotes(string):
    return '"' + str(string) + '"'

def _get_option_from_args(args, possible_options):
    for option in possible_options:
        option_arg = '--' + option
        if option_arg in args and args[option_arg] is True:
            return option
    return None


def _print_elapsed_time(os_access, start_time, prefix_string):
    """Prints the time that has elapsed between the given start time and the call of this function."""
    end_time = time.perf_counter()
    time_rounded_seconds = round(end_time - start_time)
    time_string = str(datetime.timedelta(seconds=time_rounded_seconds))
    os_access.print_console("{0} {1} h:m:s or {2} s".format(prefix_string, time_string, time_rounded_seconds))
