#!/usr/bin/python3

import os

def getCppCodeBaseRootDirFromScriptDir():
    """ This should be the only entry point for defining absolute pathes """
    head, tail = os.path.split(os.path.abspath(__file__))
    head, tail = os.path.split(head)
    head, tail = os.path.split(head)
    head = head.replace("\\", "/")
    return head


class FileLocations:
    """
    This class knows where to find what in the CppCodeBase directory structure.
    Note that this knowledge is partially duplicated in the jenkins pipeline script.
    """

    def __init__(self, cppCodeBaseRootDir):
        self.CppCodeBaseRootDir = cppCodeBaseRootDir
        self.CMAKELISTS_ROOT_DIR = "/Sources"
        self.GENERATED_FILES_DIR = "/Generated"
        self.CONFIGURATION_FILES_DIR = "/Configuration"
        self.INFRASTRUCTURE_DIR = "/Infrastructure"
        self.TARGET_DEPENDENCIES_DOT_FILE_NAME = "CppCodeBaseDependencies.dot"
        self.GENERATE_CONFIG_FILE_SCRIPT = "/Sources/CppCodeBase/Scripts/createConfigFile.cmake"
        self.CONFIG_FILE_TEMPLATE = "/Sources/CppCodeBase/Templates/DeveloperConfigTemplate.cmake.in"

    def getFullPathCppCodeBaseRoot(self):
        return self.CppCodeBaseRootDir

    def getFullPathInfrastructureFolder(self):
        return self.getFullPathCppCodeBaseRoot() + self.INFRASTRUCTURE_DIR

    def getFullPathGeneratedFolder(self):
        return self.getFullPathCppCodeBaseRoot() + self.GENERATED_FILES_DIR

    def getFullPathConfigurationFolder(self):
        return self.getFullPathCppCodeBaseRoot() + self.CONFIGURATION_FILES_DIR

    def getFullPathToSourceFolder(self):
        return self.getFullPathCppCodeBaseRoot() + self.CMAKELISTS_ROOT_DIR

    def getFullPathToConfigMakeFileDirectory(self, configName):
        makeFileDirectory = self.getFullPathGeneratedFolder() + "/" + configName
        return makeFileDirectory

    def getConfigFileEnding(self):
        return ".config.cmake"

    def getFullPathToConfigFile(self, configName):
        return self.getFullPathConfigurationFolder() + "/" + configName + self.getConfigFileEnding()

