﻿#!/usr/bin/python3
"""
This module provides the BuildAutomat class which implements the functionality
of the primary build scripts.
"""

import time
import datetime

from . import filelocations
from . import miscosaccess
from . import filesystemaccess

_CONFIG_NAME_KEY = '<config_name>'
_TARGET_KEY = '--target'
_CONFIG_KEY = '--config'
_CLEAN_KEY = '--clean'
_CPUS_KEY = '--cpus'

class BuildAutomat:
    """
    The entry point for running the various steps of the make-pipeline.
    """
    def __init__(self):
        # Get information about where is what in the cpf
        self.m_file_locations = filelocations.FileLocations(filelocations.get_cpf_root_dir_from_script_dir())
        # Object to operate on the file-system
        self.m_fs_access = filesystemaccess.FileSystemAccess()
        # Object to access other os functionality
        self.m_os_access = miscosaccess.MiscOsAccess()


    def configure(self, args):
        """
        Runs a cmake script in order to generate the developer cmake configuration file.
        """
        try:
            args = self._add_quotes_to_d_options(args)

            inherit_option = self._get_inherit_option(args)

            # add basic options
            cmake_command = "cmake" \
                        + " -DDERIVED_CONFIG=" + args[_CONFIG_NAME_KEY] \
                        + " -DPARENT_CONFIG=" + inherit_option \

            # Get the variable definitions
            definitions = args["-D"]
            if definitions:
                cmake_arg_definitions = []
                for definition in definitions:
                    cmake_arg_definitions.append("-D" + definition)
                cmake_command += " " + " ".join(cmake_arg_definitions)

            cmake_command += " -P " + _quotes(
                self.m_file_locations.get_full_path_cpf_root() /
                self.m_file_locations.GENERATE_CONFIG_FILE_SCRIPT)

            return self.m_os_access.execute_command(cmake_command)

        except BaseException as exception:
            return self._print_exception(exception)


    def generate_make_files(self, args):
        """
        Runs the cmake to create the makefiles.
        """
        try:
            start_time = time.perf_counter()

            # Use the explicit config name or try to find an existing one.
            config_name = self._get_config_name_from_arguments(args)
            if not config_name:
                config_name = self._get_first_existing_config_name()

            # Clean the build-tree if demanded
            if args[_CLEAN_KEY]:
                self._clear_makefile_dir(config_name)

            if self._has_existing_cache_file(config_name):
                # Do the incremental generate if possible
                self._call_cmake_for_existing_cache_file(config_name)
            else:
                # Do the full generate if no cache file is available.
                self._call_cmake_with_full_arguments(config_name)

            _print_elapsed_time(start_time, "Generating the make-files took")
            
            return True

        except BaseException as exception:
            return self._print_exception(exception)



    def make(self, args):
        """
        Uses CMake to make the code-base using the given make configuration.
        """
        try:
            start_time = time.perf_counter()

            config_name = self._get_config_name_from_arguments(args)
            if not config_name:
                config_name = self._get_first_config_that_has_cache_file()

            if not config_name:
                self.m_os_access.print_console("No existing CMakeCache.txt file found. You need to run 2_Generate.py before running 3_Make.py")
                return False

            cmake_build_command = self._get_cmake_build_command(config_name, args)
            return_value = self.m_os_access.execute_command(cmake_build_command)

            _print_elapsed_time(start_time, "The build took")

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
        self.m_os_access.print_console(str(exception))
        return False


    def _get_config_name_from_arguments(self, args):
        config_name = args[_CONFIG_NAME_KEY]
        if config_name: # config option was given
            config_file = self.m_file_locations.get_full_path_config_file(config_name)
            if not self.m_fs_access.exists(config_file):
                raise Exception('error: There is no configuration file "' + str(config_file) + '". Did you forget to run 1_Configure.py?')
            return config_name
        return None


    def _get_first_existing_config_name(self):
        """
        The function will return the first config for which a config file and a CMakeCache.txt file exists.
        If there is no config for which a CMakeCache.txt exists, it will return the first config in the
        Configurations directory.
        """
        config_file_configs = self._get_existing_config_file_configs()
        if not config_file_configs:
            raise Exception('error: There is no existing configuration file. Run 1_Configure.py to create one.')
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


    def _get_first_config_that_has_cache_file(self):
        config_file_configs = self._get_existing_config_file_configs()
        for config in config_file_configs:
            if self._has_existing_cache_file(config):
                return config
        return None


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

        # get command argument values
        is_clean_build = args[_CLEAN_KEY]
        target = args[_TARGET_KEY]
        config = args[_CONFIG_KEY]
        multicore_option = self._get_build_tool_multicore_option(config_name, args[_CPUS_KEY])

        # now assemble the command
        makefile_directory = self.m_file_locations.get_full_path_config_makefile_folder(config_name)
        command = 'cmake --build ' + _quotes(makefile_directory)

        if target:
            command += ' --target ' + target

        if config:
            command += ' --config ' + config

        if is_clean_build:
            command += ' --clean-first'

        if multicore_option:
            command +=' -- ' + multicore_option

        return command


    def _get_build_tool_multicore_option(self, config_name, nr_cpus):
        """
        In order to get the right option we need to introspect the used CMAKE_GENERATOR
        of the configuration.
        """
        generator = self._get_cmake_generator_of_config(config_name)

        if not nr_cpus:
            nr_cpus = str(self.m_os_access.cpu_count())

        if 'Visual Studio' in generator:
            return "/maxcpucount:"+ nr_cpus
        elif generator == 'Unix Makefiles':
            return '-j' + nr_cpus
        elif generator == 'Ninja':
            return '-j' + nr_cpus
        else:
            return None


    def _get_cmake_generator_of_config(self, config_name):
        # get the name of the used generator
        makefile_directory = self.m_file_locations.get_full_path_config_makefile_folder(config_name)
        cmake_introspection_command = []
        cmake_introspection_command.append('cmake -L -B' + _quotes(makefile_directory))
        output = self.m_os_access.execute_commands_in_parallel(cmake_introspection_command, None, False)[0]['stdout']
        lines = output.split('\n')
        for line in lines:
            if 'CMAKE_GENERATOR:STRING=' in line:
                generator_name = line[23:]
                return generator_name
        return None


########### free functions #########################################################################
def _quotes(string):
    return '"' + str(string) + '"'


def _get_option_from_args(args, possible_options):
    for option in possible_options:
        option_arg = '--' + option
        if option_arg in args and args[option_arg] is True:
            return option
    return None


def _print_elapsed_time(start_time, prefix_string):
    """Prints the time that has elapsed between the given start time and the call of this function."""
    end_time = time.perf_counter()
    time_rounded_seconds = round(end_time - start_time)
    time_string = str(datetime.timedelta(seconds=time_rounded_seconds))
    print("{0} {1} h:m:s or {2} s".format(prefix_string, time_string, time_rounded_seconds))
