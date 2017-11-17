#!/usr/bin/python3


import os.path

# ours
from . import docopt

from . import filelocations
from . import miscosaccess
from . import filesystemaccess

_configNameKey = '<config_name>'
_targetKey = '--target'
_configKey = '--config'

class BuildAutomat:
    """
    The entry point for running the various steps of the make-pipeline.
    """
    def __init__(self):
        self.m_fileLocations = filelocations.FileLocations(filelocations.getCppCodeBaseRootDirFromScriptDir())  # Get information about where is what in the codebase
        self.m_fsAccess = filesystemaccess.FileSystemAccess()                   # Object to operate on the file-system
        self.m_osAccess = miscosaccess.MiscOsAccess()                           # Object to access other os functionality


    def configure(self, args):
        """
        Runs a cmake script in order to generate the developer cmake configuration file.
        """
        try:
            args = self._addQuotesToDOptions(args)

            inheritOption = self._getInheritOption(args)

            # add basic options
            cmakeCommand = "cmake" \
                        + " -DCPPCODEBASE_CONFIG=" + args[_configNameKey] \
                        + " -DPARENT_CONFIG=" + inheritOption \

            # Get the variable definitions
            definitions = args["-D"]
            if definitions:
                cmakeArgDefinitions = []
                for definition in definitions:
                     cmakeArgDefinitions.append( "-D" + definition)
                cmakeCommand += " " + " ".join(cmakeArgDefinitions)            
                    
            cmakeCommand += " -P " + _quotes(self.m_fileLocations.getFullPathCppCodeBaseRoot() + self.m_fileLocations.GENERATE_CONFIG_FILE_SCRIPT)

            return self.m_osAccess.executeCommandAndPrintResult(cmakeCommand)

        except BaseException as e:
            return self._printOrRethrow(e)


    def generateMakefiles(self, args):
        """
        Runs the cmake to create the makefiles.
        """
        try:
            configName = self._getConfigNameFromArguments(args)
            if configName:
                self._clearMakefileDir(configName)

            else: # check for an existing configuration file
                configName = self._getExistingConfigName()
                if self._hasExistingCacheFile(configName):
                    self._callCMakeForExistingCacheFile(configName)
                    return True

            self._callCMakeWithFullArguments(configName)
            return True

        except BaseException as e:
            return self._printOrRethrow(e)


    def make(self, args):
        """
        Uses CMake to make the code-base using the given make configuration.
        """
        try:

            configName = self._getConfigNameFromArguments(args)
            if not configName:
                configName = self._getExistingConfigName()

            if not self._hasExistingCacheFile(configName):
                self.m_osAccess.printConsole("No existing CMakeCache.txt file found. You need to run 1_Generate.py before running 2_Make.py");
                return False

            cmakeBuildCommand = self._getCMakeBuildCommand(configName, args)

            return self.m_osAccess.executeCommandAndPrintResult(cmakeBuildCommand )

        except BaseException as e:
            return self._printOrRethrow(e)


    ###############################################################################################################

    def _addQuotesToDOptions(self, args):
        """
        This is necessary because docopt will loose quotes around definitions that contain spaces.
        """
        dOptions = args['-D']
        if dOptions:
            for index, option in enumerate(dOptions):
                if '=' not in option:
                    raise Exception('-D option "' + option + '" does not seem to be a valid definition because of a missing "=" character.')
                definition = option.split('=')[1]
                if ' ' in definition:
                    cmakeVariable = option.split('=')[0]
                    dOptions[index] = cmakeVariable + '=' + _quotes(definition)
        args['-D'] = dOptions
        return args

    def _getInheritOption(self,args):
        """
        Returns the argument or the default inheritance depending on the system.
        """
        inheritOption = args['--inherits']
        if not inheritOption:
            inheritOption = self.m_osAccess.system()
        return inheritOption

    def _printOrRethrow(self, exception):
        if exception:
            self.m_osAccess.printConsole(str(exception))
        else:
            raise
        return False


    def _getConfigNameFromArguments(self, args):
        configName = args[_configNameKey]
        if configName: # config option was given
            configFile = self.m_fileLocations.getFullPathToConfigFile(configName)
            if not self.m_fsAccess.exists(configFile):
                raise Exception('error: There is no configuration file "' + configFile + '". Did you forget to run 0_Configure.py?')
            return configName
        return None


    def _getExistingConfigName(self):
        """ 
        The function will return the first config for which a config file and a CMakeCache.txt file exists.
        If there is no config for which a CMakeCache.txt exists, it will return the first config in the
        Configurations directory.
        """
        configFileConfigs = self._getExistingConfigFileConfigs()
        if not configFileConfigs:
            raise Exception('error: There is no existing configuration file. Run 0_Configure.py to create one.')
        configWithCacheFile = self._getFirstConfigThatHasChacheFile(configFileConfigs)
        if configWithCacheFile:
            return configWithCacheFile
        else:
            return configFileConfigs[0]

    def _getExistingConfigFileConfigs(self):
        configs = []
        if self.m_fsAccess.isdir(self.m_fileLocations.getFullPathConfigurationFolder()):
            entries = self.m_fsAccess.listdir( self.m_fileLocations.getFullPathConfigurationFolder() )
            for entry in entries:
                fullEntryPath = self.m_fileLocations.getFullPathConfigurationFolder() + "/" + entry
                configFileEnding = self.m_fileLocations.getConfigFileEnding()
                lengthEnding = len(configFileEnding)
                ending =entry[-lengthEnding:]
                if self.m_fsAccess.isfile(fullEntryPath) and ending == configFileEnding:
                    length = len(entry)
                    configs.append(entry[:(length - lengthEnding)])
        return configs


    def _getFirstConfigThatHasChacheFile(self, configs):
        for config in configs:
            if self._hasExistingCacheFile(config):
                return config
        return None


    def _hasExistingCacheFile(self, configName):
        cacheFilePath = self.m_fileLocations.getFullPathGeneratedFolder() + "/" + configName + "/CMakeCache.txt"
        return self.m_fsAccess.isfile(cacheFilePath)


    def _clearMakefileDir(self, configName):
        """
        Deletes the make folder to make sure that we start from scratch.
        """
        fullConfigPath = self.m_fileLocations.getFullPathToConfigMakeFileDirectory(configName)
        if self.m_fsAccess.exists(fullConfigPath):
            self.m_fsAccess.rmtree(fullConfigPath)


    def _callCMakeWithFullArguments(self, configName):
        """
        Assembles the correct arguments for cmake and executes the cmake generate step
        """

        makeFileDirectory = self.m_fileLocations.getFullPathToConfigMakeFileDirectory(configName)
        sourcesDirectory = self.m_fileLocations.getFullPathToSourceFolder()
        fullPathConfigFile = self.m_fileLocations.getFullPathToConfigFile(configName)

        command = ( 
                        "cmake"
                        " -H" + _quotes(sourcesDirectory) +        # set the cmakelists root directory
                        " -B" + _quotes(makeFileDirectory) +       # set the folder for the generated make files
                        " -C" + _quotes(fullPathConfigFile) +  # set the generator (makefileType)
                        " --graphviz="+ _quotes( makeFileDirectory  + "/" + self.m_fileLocations.TARGET_DEPENDENCIES_DOT_FILE_NAME)          # Generate the .dot file that is used to document the target dependencies.
                        )

        if not self.m_osAccess.executeCommandAndPrintResult(command):
            raise Exception("The python script failed because the call to cmake failed!")


    def _callCMakeForExistingCacheFile(self, configName):
        """
        runs CMake and uses the cached variables from the CMakeCache file.
        """
        makeFileDirectory = self.m_fileLocations.getFullPathToConfigMakeFileDirectory(configName)
        fullCommand = (
            "cmake " + _quotes(makeFileDirectory) + 
            " --graphviz="+ _quotes(makeFileDirectory + "/" + self.m_fileLocations.TARGET_DEPENDENCIES_DOT_FILE_NAME)
            )
    
        if not self.m_osAccess.executeCommandAndPrintResult(fullCommand):
            raise Exception("The python script failed because the call to cmake failed!")


    def _getCMakeBuildCommand(self, configName, args):

        # get command argument values
        isIncrementalBuild = args[_configNameKey] is None
        target = args[_targetKey]
        config = args[_configKey]
        multicoreOption = self._getBuildToolMulticoreOption(configName)

        # now assemble the command
        makeFileDirectory = self.m_fileLocations.getFullPathToConfigMakeFileDirectory(configName)
        command = 'cmake --build ' + _quotes(makeFileDirectory)

        if target:
            command += ' --target ' + target

        if config:
            command += ' --config ' + config

        if not isIncrementalBuild:
            command += ' --clean-first'

        if multicoreOption:
            command +=' -- ' + multicoreOption

        return command


    def _getBuildToolMulticoreOption(self, configName):
        """
        In order to get the right option we need to introspect the used CMAKE_GENERATOR
        of the configuration.
        """
        generator = self._getCMakeGeneratorOfConfig(configName)

        nrCpus = str(self.m_osAccess.cpu_count())

        if 'Visual Studio' in generator:
            return "/maxcpucount:"+ nrCpus
        elif generator == 'Unix Makefiles':
            return '-j' + nrCpus
        else:
            return None


    def _getCMakeGeneratorOfConfig(self, configName):
        # get the name of the used generator
        makeFileDirectory = self.m_fileLocations.getFullPathToConfigMakeFileDirectory(configName)
        cmakeIntrospectionCommand = []
        cmakeIntrospectionCommand.append( 'cmake -L -B' + _quotes(makeFileDirectory))
        output = self.m_osAccess.runCommandsInMultipleProcesses(cmakeIntrospectionCommand, None, False)[0]['stdout']
        lines = output.split('\n')
        for line in lines:
            if 'CMAKE_GENERATOR:STRING=' in line:
                generatorName = line[23:]
                return generatorName
        return None




########### free functions ###################################################################################


def _quotes(string):
    return '"' + string + '"'


def _getOptionFromArgs(args,possibleOptions):
    for option in possibleOptions:
        optionArg = '--' + option
        if optionArg in args and args[optionArg] is True:
            return option
    return None




"""
Example for implementing a thread

def _runCommandsInMultipleThreads(commands):
    
    # Setup and start one thread for each command.
    threads = [] 

    for command in commands: 
        thread = CommandRunnerThread(command) 
        threads.append(thread) 
        thread.start() 

    # Wait until all threads have finished.
    for thread in threads: 
        thread.join()

    # Collect and return the results.
    results = [];
    for thread in threads: 
        results.append( thread.result)
        
    return results

# ---------------------------------------------------------------------------------------
class CommandRunnerThread(threading.Thread):
    
    def __init__(self, command):
        threading.Thread.__init__(self)
        self.command = command
        self.result = None
        
    def run(self):
        self.result = self.m_osAccess.executeCommand(self.command)
        #self.m_osAccess.printConsole(self.result['stdout'])
        #self.m_osAccess.printConsole(self.result['stderr'])
"""
