#!/usr/bin/python3

#import os
#import subprocess
#import getopt
#import shutil
#import platform
#import multiprocessing
#import shlex
#from subprocess import *

import unittest
from unittest.mock import patch

#from unittest.mock import Mock
#from unittest.mock import MagicMock
#from unittest.mock import create_autospec

#from unittest.mock import ANY

from . import buildautomat
from . import miscosaccess
from . import filesystemaccess
from . import filelocations
from . import miscosaccess


class TestBuildAutomat(unittest.TestCase):
          
 
    def setUp(self):
        
        # define some constants
        self.codeBaseRoot = "/MyCppCodeBase"
        self.WINDOWS = "Windows"
        self.LINUX = "Linux"
        self.pathToCommonTools = "C:\\path\\to\\CommonTools\\"
        self.cpu_count = 4

        # Setup the system under test
        self.sut = buildautomat.BuildAutomat()
        
        # Replace the FileSystemAccess with a fake implementation that contains
        # The basic folder and file structure.
        self.locations = filelocations.FileLocations(self.codeBaseRoot)
        self.sut.m_fileLocations = self.locations
        self.sut.m_fsAccess = filesystemaccess.FakeFileSystemAccess()
        # self.sut.m_fsAccess.mkdirs(self.locations.getFullPathInfrastructureFolder())
        self.sut.m_fsAccess.mkdirs(self.locations.getFullPathToSourceFolder())
        self.sut.m_fsAccess.mkdirs(self.locations.getFullPathToSourceFolder())

        # add some source files
        # Module1
        self.sut.m_fsAccess.addfile(self.locations.getFullPathToSourceFolder() + "/Module1/bla.h", "content")
        self.sut.m_fsAccess.addfile(self.locations.getFullPathToSourceFolder() + "/Module1/bla.cpp", "content")
        self.sut.m_fsAccess.addfile(self.locations.getFullPathToSourceFolder() + "/Module1/bla.ui", "content")
        # Module2
        self.sut.m_fsAccess.addfile(self.locations.getFullPathToSourceFolder() + "/Module2/blub.h", "content")
        # Module3
        self.sut.m_fsAccess.addfile(self.locations.getFullPathToSourceFolder() + "/Module3/blar.cpp", "content")
        # cmake
        self.sut.m_fsAccess.mkdirs(self.locations.getFullPathToSourceFolder() + "/cmake")

        # use the windows os access as default
        self.sut.m_osAccess = self.getFakeOsAccess(self.WINDOWS)


    def getFakeOsAccess(self, os):
        return miscosaccess.FakeMiscOsAccess(self.sut.m_fsAccess, self.codeBaseRoot, {}, os, self.cpu_count)


#######################################################################################################

    def test_configure_executes_the_correct_cmake_command(self):
        # setup
        self.maxDiff = None
        self.sut.m_osAccess = self.getFakeOsAccess(self.WINDOWS)
        args = {
            "<config_name>" : "MyConfig", 
            "--inherits" : "MyProjectConfig" ,
            "-D" : ['CMAKE_GENERATOR=Visual Studio 14 2015 Amd64','CPPCODEBASE_TEST_FILES_DIR=C:/Temp bla/Tests'] # note that argument values do not have quotes when they come in from docopt
            }

        # execute
        self.assertTrue(self.sut.configure(args))

        # verify
        expectedCommand = (
                    'cmake '
                    '-DCPPCODEBASE_CONFIG=MyConfig '
                    '-DPARENT_CONFIG=MyProjectConfig '
                    '-DCMAKE_GENERATOR="Visual Studio 14 2015 Amd64" '
                    '-DCPPCODEBASE_TEST_FILES_DIR="C:/Temp bla/Tests" '
                    '-P "/MyCppCodeBase/Sources/CppCodeBase/Scripts/createConfigFile.cmake"'
                    )
        self.assertEqual(self.sut.m_osAccess.executeCommandAndPrintResultArg[0][1] , expectedCommand)

    def test_configure_sets_correct_default_inheritance_on_windows(self):
        # setup
        self.maxDiff = None
        self.sut.m_osAccess = self.getFakeOsAccess(self.WINDOWS)
        args = {
            "<config_name>" : "MyConfig", 
            "--inherits" : None ,
            "-D" : []
            }

        # execute
        self.assertTrue(self.sut.configure(args))

        # verify
        expectedCommand = (
                    'cmake '
                    '-DCPPCODEBASE_CONFIG=MyConfig '
                    '-DPARENT_CONFIG=Windows '
                    '-P "/MyCppCodeBase/Sources/CppCodeBase/Scripts/createConfigFile.cmake"'
                    )
        self.assertEqual(self.sut.m_osAccess.executeCommandAndPrintResultArg[0][1] , expectedCommand)

    def test_configure_sets_correct_default_inheritance_on_linux(self):
        # setup
        self.maxDiff = None
        self.sut.m_osAccess = self.getFakeOsAccess(self.LINUX)
        args = {
            "<config_name>" : "MyConfig", 
            "--inherits" : None ,
            "-D" : []
            }

        # execute
        self.assertTrue(self.sut.configure(args))

        # verify
        expectedCommand = (
                    'cmake '
                    '-DCPPCODEBASE_CONFIG=MyConfig '
                    '-DPARENT_CONFIG=Linux '
                    '-P "/MyCppCodeBase/Sources/CppCodeBase/Scripts/createConfigFile.cmake"'
                    )
        self.assertEqual(self.sut.m_osAccess.executeCommandAndPrintResultArg[0][1] , expectedCommand)


#######################################################################################################

    def test_generateMakefiles_executes_the_correct_calls_when_config_option_is_given(self):

        # setup
        self.maxDiff = None
        self.sut.m_osAccess = self.getFakeOsAccess(self.LINUX)
        pathInMakeFileFolder = self.locations.getFullPathGeneratedFolder() + "/MyConfig/blib";
        self.sut.m_fsAccess.mkdirs(pathInMakeFileFolder) # add an extra directory in the makefile directory so we can check that the folder was cleared
        self.sut.m_fsAccess.addfile(self.locations.getFullPathToConfigFile('MyConfig'), "content")
        argv = {"<config_name>" : "MyConfig"}

        # execute
        self.assertTrue(self.sut.generateMakefiles(argv))

        # verify
        # makefile folder is cleared when the <config_name> argument is given
        self.assertFalse(self.sut.m_fsAccess.isdir(pathInMakeFileFolder))
              
        # cmake is called with correct arguments
        expectedCommand = (
                            'cmake '
                            '-H"/MyCppCodeBase/Sources" '
                            '-B"/MyCppCodeBase/Generated/MyConfig" '
                            '-C"/MyCppCodeBase/Configuration/MyConfig.config.cmake" '
                            '--graphviz="/MyCppCodeBase/Generated/MyConfig/CppCodeBaseDependencies.dot"'
                          )

        self.assertEqual(self.sut.m_osAccess.executeCommandAndPrintResultArg[0][1] , expectedCommand)


    def test_generateMakefiles_executes_the_correct_calls_when_no_config_option_is_given_and_only_a_config_file_exists(self):
        
        # Setup
        self.sut.m_osAccess = self.getFakeOsAccess(self.WINDOWS)
        self.sut.m_fsAccess.addfile(self.locations.getFullPathToConfigFile('MyConfig'), "content")
        argv = {"<config_name>" : None}
        

        # execute
        self.assertTrue(self.sut.generateMakefiles(argv))

        # verify
        expectedCommand = (
                            'cmake '
                            '-H"/MyCppCodeBase/Sources" '
                            '-B"/MyCppCodeBase/Generated/MyConfig" '
                            '-C"/MyCppCodeBase/Configuration/MyConfig.config.cmake" '
                            '--graphviz="/MyCppCodeBase/Generated/MyConfig/CppCodeBaseDependencies.dot"'
                            )
        self.assertEqual(self.sut.m_osAccess.executeCommandAndPrintResultArg[0][1] , expectedCommand)


    def test_generateMakefiles_executes_the_correct_calls_when_no_config_option_is_given_and_a_config_file_and_a_cachefile_exists(self):
        
        # Setup
        self.sut.m_osAccess = self.getFakeOsAccess(self.WINDOWS)
        self.sut.m_fsAccess.addfile(self.locations.getFullPathToConfigFile('MyConfig'), "content")
        self.sut.m_fsAccess.addfile(self.locations.getFullPathGeneratedFolder() + "/MyConfig/CMakeCache.txt", "content")
        argv = {"<config_name>" : None}

        # execute
        self.assertTrue(self.sut.generateMakefiles(argv))

        # verify
        expectedCommand = (
                            'cmake '
                            '"/MyCppCodeBase/Generated/MyConfig" '
                            '--graphviz="/MyCppCodeBase/Generated/MyConfig/CppCodeBaseDependencies.dot"'
                            )
        self.assertEqual(self.sut.m_osAccess.executeCommandAndPrintResultArg[0][1] , expectedCommand)


    def test_generateMakefiles_returns_false_when_config_option_is_given_but_config_file_does_not_exist(self):

        # setup
        self.maxDiff = None
        self.sut.m_osAccess = self.getFakeOsAccess(self.LINUX)
        argv = {"<config_name>" : "MyConfig"}

        # execute
        self.assertFalse(self.sut.generateMakefiles(argv))

        # verify
        # make sure an error message was issued
        self.assertTrue( "error:" in self.sut.m_osAccess.consoleOutput)


    def test_generateMakefiles_returns_false_when_no_config_option_is_given_and_no_config_file_exists(self):
        # setup
        self.sut.m_osAccess = self.getFakeOsAccess(self.LINUX)
        argv = {"<config_name>" : None}

        # execute
        self.assertFalse( self.sut.generateMakefiles(argv) )

        # verify
        # make sure an error message was issued
        self.assertTrue( "error:" in self.sut.m_osAccess.consoleOutput)
        # make sure cmake was never executed
        self.assertTrue( not "cmake" in self.sut.m_osAccess.consoleOutput)


    @patch('cppcodebasebuildscripts.miscosaccess.FakeMiscOsAccess.executeCommandAndPrintResult', return_value = False)
    def test_generateMakefiles_returns_false_if_cmake_call_fails(self, mock_executeCommandAndPrintResult):
        # setup
        argv = {"<config_name>" : "MyConfig"}

        # execute
        self.assertFalse(self.sut.generateMakefiles(argv))


      
#######################################################################################################

    def test_make_makes_the_correct_cmake_call_when_all_options_are_given(self):
        # setup
        self.sut.m_osAccess = self.getFakeOsAccess(self.WINDOWS)
        self.sut.m_fsAccess.addfile(self.locations.getFullPathToConfigFile('MyConfig'), "content")
        self.sut.m_fsAccess.addfile(self.locations.getFullPathToConfigMakeFileDirectory('MyConfig') + '/CMakeCache.txt', "content")
        
        cmakeInspectionCallStdOut = (
            "CMAKE_C_COMPILER:FILEPATH=C:/Program Files (x86)/Microsoft Visual Studio 14.0/Common7/Tools/../../VC/bin/x86_amd64/cl.exe\n"
            "CMAKE_GENERATOR:STRING=Visual Studio 14 2015 Win64\n"
            "CMAKE_INSTALL_PREFIX:PATH=C:/Program Files/CppCodeBase\n"
        )
        self.sut.m_osAccess.runCommandInMultipleProcessesResults = [[{'returncode':0, 'stdout' : cmakeInspectionCallStdOut}]]
        argv = {"<config_name>" : "MyConfig", "--target" : "myTarget", "--config" : "Debug"}
        
        # execute
        self.assertTrue(self.sut.make(argv))
        
        #verify
        expectedCmakeCall = (
                               'cmake'
                               ' --build "/MyCppCodeBase/Generated/MyConfig"'
                               ' --target myTarget'
                               ' --config Debug'
                               ' --clean-first'
                               ' -- /maxcpucount:' + str(self.cpu_count)
                               )
        self.assertEqual(self.sut.m_osAccess.executeCommandAndPrintResultArg[0][1] , expectedCmakeCall)

       
    def test_make_makes_the_correct_incremental_cmake_call_when_no_options_are_given(self):

        # Setup
        # note that the function should pick the config that has a cachefile
        self.sut.m_fsAccess.addfile(self.locations.getFullPathToConfigFile('A_Config'), "content")
        self.sut.m_fsAccess.addfile(self.locations.getFullPathToConfigFile('B_Config'), "content")
        self.sut.m_fsAccess.addfile(self.locations.getFullPathToConfigFile('C_Config'), "content")
        self.sut.m_fsAccess.addfile(self.locations.getFullPathGeneratedFolder() + "/B_Config/CMakeCache.txt", "content")
        self.sut.m_osAccess.runCommandInMultipleProcessesResults = [[{'returncode':0, 'stdout' : "CMAKE_GENERATOR:STRING=Visual Studio 14 2015 Win64\n"}]]
        argv = {"<config_name>" : None, "--target" : None, "--config" : None}

        # execute
        self.assertTrue(self.sut.make(argv))
        
        #verify
        expectedCmakeCall = (
                                'cmake'
                                ' --build "/MyCppCodeBase/Generated/B_Config"'
                                ' -- /maxcpucount:' + str(self.cpu_count)
                                )
        self.assertEqual(self.sut.m_osAccess.executeCommandAndPrintResultArg[0][1] , expectedCmakeCall)

  
    def test_make_uses_the_correct_multicpuoption_for_unix_makefiles(self):
        # setup
        self.sut.m_fsAccess.addfile(self.locations.getFullPathToConfigFile('MyConfig'), "content")
        self.sut.m_fsAccess.addfile(self.locations.getFullPathGeneratedFolder() + "/MyConfig/CMakeCache.txt", "content")
        self.sut.m_osAccess.runCommandInMultipleProcessesResults = [[{'returncode':0, 'stdout' : "CMAKE_GENERATOR:STRING=Unix Makefiles\n"}]]
        argv = {"<config_name>" : None, "--target" : None, "--config" : None}

        # execute
        self.assertTrue(self.sut.make(argv))
        
        #verify
        expectedCmakeCall = (
            'cmake'
            ' --build "/MyCppCodeBase/Generated/MyConfig"'
            ' -- -j' + str(self.cpu_count)
            )
        self.assertEqual(self.sut.m_osAccess.executeCommandAndPrintResultArg[0][1] , expectedCmakeCall)

 
