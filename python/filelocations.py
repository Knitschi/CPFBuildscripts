#!/usr/bin/python3

import os
from pathlib import PurePosixPath

def get_cpf_root_dir_from_script_dir():
    """ This should be the only entry point for defining absolute pathes """
    head = os.path.split(os.path.abspath(__file__))[0]
    head = os.path.split(head)[0]
    head = os.path.split(head)[0]
    head = os.path.split(head)[0]
    head = head.replace("\\", "/")
    return PurePosixPath(head)


class FileLocations:
    """
    This class knows where to find what in the CMakeProjectFramework directory structure.
    Note that this knowledge is partially duplicated in the jenkins pipeline script.
    """

    def __init__(self, cpf_root_dir):
        self.cpf_root_dir = PurePosixPath(cpf_root_dir)
        self.CMAKELISTS_ROOT_DIR = "Sources"
        self.GENERATED_FILES_DIR = "Generated"
        self.CONFIGURATION_FILES_DIR = "Configuration"
        self.DEFAULT_INSTALL_DIR = "install"
        self.TARGET_DEPENDENCIES_DOT_FILE_NAME = "CPFDependencies.dot"
        self.GENERATE_CONFIG_FILE_SCRIPT = "Sources/CPFCMake/Scripts/createConfigFile.cmake"
        self.CONFIG_FILE_TEMPLATE = "Sources/CPFCMake/Templates/DeveloperConfigTemplate.cmake.in"
        self.CONAN_FILE = "conanfile.txt"

    def get_full_path_cpf_root(self):
        return self.cpf_root_dir

    def get_full_path_generated_folder(self):
        return self.get_full_path_cpf_root() / self.GENERATED_FILES_DIR

    def get_full_path_configuration_folder(self):
        return self.get_full_path_cpf_root() / self.CONFIGURATION_FILES_DIR

    def get_full_path_conan_generated_cmake_files_dir(self, configName):
        return self.get_full_path_configuration_folder() / configName

    def get_full_path_source_folder(self):
        return self.get_full_path_cpf_root() / self.CMAKELISTS_ROOT_DIR

    def get_full_path_config_makefile_folder(self, configName):
        makefile_directory = self.get_full_path_generated_folder().joinpath(configName)
        return makefile_directory

    def get_full_path_binary_output_folder(self, package, configName, compilerConfig):
        return self.get_full_path_config_makefile_folder(configName) / "BuildStage" / compilerConfig / package

    def get_config_file_ending(self):
        return ".config.cmake"

    def get_full_path_config_file(self, configName):
        return self.get_full_path_configuration_folder().joinpath(configName + self.get_config_file_ending())

    def get_full_path_default_install_folder(self):
        return self.get_full_path_cpf_root() / self.DEFAULT_INSTALL_DIR

    def get_full_path_conan_file(self):
        return self.get_full_path_source_folder() / self.CONAN_FILE
