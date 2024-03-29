﻿"""
This module contains unit tests for the BuildAutomat class.
"""
#!/usr/bin/python3

import unittest
from unittest.mock import patch

from . import buildautomat
from . import miscosaccess
from . import filesystemaccess
from . import filelocations


_WINDOWS = "Windows"
_LINUX = "Linux"

class TestBuildAutomat(unittest.TestCase):
    """
    The test fixture for the BuildAutomat tests.
    """
    def setUp(self):

        # define some constants
        self.cpf_root = "/MyCPFProject"
        self.CPFCMake_DIR = "/MyCPFProject/Sources/external/CPFCMake"
        self.CIBuildConfigurations_DIR = "/MyCPFProject/Sources/CIBuildConfigurations"
        self.path_to_common_tools = "C:\\path\\to\\CommonTools\\"
        self.cpu_count = 4


        # Replace the FileSystemAccess with a fake implementation that contains
        # The basic folder and file structure.
        self.locations = filelocations.FileLocations(self.cpf_root, self.CPFCMake_DIR, self.CIBuildConfigurations_DIR)
        
        fs_access = filesystemaccess.FakeFileSystemAccess()
        # fs_access.mkdirs(self.locations.getFullPathInfrastructureFolder())
        fs_access.mkdirs(self.locations.get_full_path_source_folder())
        fs_access.mkdirs(self.locations.get_full_path_source_folder())

        # add some source files
        # Module1
        fs_access.addfile(
            self.locations.get_full_path_source_folder() / "Module1/bla.h",
            "content")
        fs_access.addfile(
            self.locations.get_full_path_source_folder() / "Module1/bla.cpp",
            "content")
        fs_access.addfile(
            self.locations.get_full_path_source_folder() / "Module1/bla.ui",
            "content")
        # Module2
        fs_access.addfile(
            self.locations.get_full_path_source_folder() / "Module2/blub.h",
            "content")
        # Module3
        fs_access.addfile(
            self.locations.get_full_path_source_folder() / "Module3/blar.cpp",
            "content")
        # cmake
        fs_access.mkdirs(self.locations.get_full_path_source_folder() / "cmake")
        # CPFCMake and CIBuildConfigurations directories.
        fs_access.mkdirs(self.locations.get_full_path_source_folder() / "external/CPFCMake")
        fs_access.mkdirs(self.locations.get_full_path_source_folder() / "CIBuildConfigurations")

        # Setup the system under test
        self.sut = buildautomat.BuildAutomat(self.cpf_root, self.CPFCMake_DIR, self.CIBuildConfigurations_DIR, filesystemaccess=fs_access)
        self.sut.m_file_locations = self.locations

        # use the windows os access as default
        self.sut.m_os_access = self._get_fake_os_access(_WINDOWS)


    def _get_fake_os_access(self, operating_system):
        return miscosaccess.FakeMiscOsAccess(
            self.sut.m_fs_access,
            self.cpf_root,
            {},
            operating_system,
            self.cpu_count)


####################################################################################################

    def test_configure_with_major_arguments(self):
        # setup
        self.maxDiff = None
        self.sut.m_os_access = self._get_fake_os_access(_WINDOWS)
        args = {
            "<config_name>" : "MyConfig",
            "--inherits" : "MyProjectConfig",
            "-D" : [
                'CMAKE_GENERATOR=Visual Studio 14 2015 Amd64',
                'CPF_TEST_FILES_DIR=C:/Temp bla/Tests'],    # Note that argument values do not
                                                            # have quotes when they come in
                                                            # from docopt
            "--list" : False
            }

        # execute
        self.assertTrue(self.sut.configure(args))

        # verify
        expected_command = (
            'cmake '
            '-DDERIVED_CONFIG=MyConfig '
            '-DPARENT_CONFIG=MyProjectConfig '
            '-DCPF_ROOT_DIR="/MyCPFProject" '
            '-DCPFCMake_DIR="/MyCPFProject/Sources/external/CPFCMake" '
            '-DCIBuildConfigurations_DIR="/MyCPFProject/Sources/CIBuildConfigurations" '
            '-DCMAKE_GENERATOR="Visual Studio 14 2015 Amd64" '
            '-DCPF_TEST_FILES_DIR="C:/Temp bla/Tests" '
            '-P "/MyCPFProject/Sources/external/CPFCMake/Scripts/createConfigFile.cmake"'
            )
        self.assertEqual(
            self.sut.m_os_access.execute_command_arg[0][1],
            expected_command)

    def test_configure_short_call(self):
        # setup
        self.maxDiff = None
        self.sut.m_os_access = self._get_fake_os_access(_WINDOWS)
        args = {
            "<config_name>" : "MyConfig",
            "--inherits" : None,
            "-D" : [],
            "--list" : False
            }

        # execute
        self.assertTrue(self.sut.configure(args))

        # verify
        expected_command = (
            'cmake '
            '-DDERIVED_CONFIG=MyConfig '
            '-DPARENT_CONFIG=MyConfig '
            '-DCPF_ROOT_DIR="/MyCPFProject" '
            '-DCPFCMake_DIR="/MyCPFProject/Sources/external/CPFCMake" '
            '-DCIBuildConfigurations_DIR="/MyCPFProject/Sources/CIBuildConfigurations" '
            '-P "/MyCPFProject/Sources/external/CPFCMake/Scripts/createConfigFile.cmake"'
            )
        self.assertEqual(
            self.sut.m_os_access.execute_command_arg[0][1],
            expected_command)

    def test_configure_with_list_argument(self):
        # setup
        self.maxDiff = None
        self.sut.m_os_access = self._get_fake_os_access(_LINUX)
        args = {
            "<config_name>" : None,
            "--inherits" : None,
            "-D" : [],
            "--list" : True
            }

        # execute
        self.assertTrue(self.sut.configure(args))

        # verify
        expected_command = (
            'cmake '
            '-DLIST_CONFIGURATIONS=TRUE '
            '-DCPF_ROOT_DIR="/MyCPFProject" '
            '-DCPFCMake_DIR="/MyCPFProject/Sources/external/CPFCMake" '
            '-DCIBuildConfigurations_DIR="/MyCPFProject/Sources/CIBuildConfigurations" '
            '-P "/MyCPFProject/Sources/external/CPFCMake/Scripts/createConfigFile.cmake"'
            )
        self.assertEqual(
            self.sut.m_os_access.execute_command_arg[0][1],
            expected_command)


####################################################################################################

    def test_generate_make_files_test_clean_generate(self):

        # setup
        self.maxDiff = None
        self.sut.m_os_access = self._get_fake_os_access(_LINUX)
        self.sut.m_fs_access.addfile(self.locations.get_full_path_config_file('MyConfig'), "content")
        self.sut.m_fs_access.addfile(self.locations.get_full_path_generated_folder() / "MyConfig/CMakeCache.txt", "content")
        # add an extra directory in the makefile directory so we can check that the folder was cleared
        path_in_make_file_folder = self.locations.get_full_path_generated_folder() / "MyConfig/blib"
        self.sut.m_fs_access.mkdirs(path_in_make_file_folder)

        argv = {"<config_name>" : "MyConfig", "--clean" : True}

        # execute
        self.assertTrue(self.sut.generate_make_files(argv))

        # verify
        # makefile folder was cleared
        self.assertFalse(self.sut.m_fs_access.isdir(path_in_make_file_folder))

        # cmake is called with correct arguments
        expected_command = (
            'cmake '
            '-H"/MyCPFProject/Sources" '
            '-B"/MyCPFProject/Generated/MyConfig" '
            '-C"/MyCPFProject/Configuration/MyConfig.config.cmake" '
            '--graphviz="/MyCPFProject/Generated/MyConfig/CPFDependencies.dot"'
            )

        self.assertEqual(self.sut.m_os_access.execute_command_arg[0][1], expected_command)


    def test_generate_make_files_executes_incremental_generate_when_a_configfile_and_a_cachefile_exist(self):

        # setup
        self.maxDiff = None
        self.sut.m_os_access = self._get_fake_os_access(_LINUX)

        self.sut.m_fs_access.addfile(self.locations.get_full_path_config_file('MyConfig'), "content")
        self.sut.m_fs_access.addfile(self.locations.get_full_path_generated_folder() / "MyConfig/CMakeCache.txt", "content")
        # add an extra directory in the makefile directory so we can check that the folder was not cleared
        path_in_make_file_folder = self.locations.get_full_path_generated_folder() / "MyConfig/blib"
        self.sut.m_fs_access.mkdirs(path_in_make_file_folder)

        argv = {"<config_name>" : "MyConfig", "--clean" : False}

        # execute
        self.assertTrue(self.sut.generate_make_files(argv))

        # verify
        # makefile folder was not cleared
        self.assertTrue(self.sut.m_fs_access.isdir(path_in_make_file_folder))

        # cmake is called with correct arguments
        expected_command = (
            'cmake '
            '"/MyCPFProject/Generated/MyConfig" '
            '--graphviz="/MyCPFProject/Generated/MyConfig/CPFDependencies.dot"'
            )

        self.assertEqual(self.sut.m_os_access.execute_command_arg[0][1], expected_command)


    def test_generate_make_files_executes_fresh_generate_when_no_cache_file_exists(self):

        # Setup
        self.sut.m_os_access = self._get_fake_os_access(_WINDOWS)
        self.sut.m_fs_access.addfile(self.locations.get_full_path_config_file('MyConfig'), "content")
        argv = {"<config_name>" : "MyConfig", "--clean" : False}

        # execute
        self.assertTrue(self.sut.generate_make_files(argv))

        # verify
        expected_command = (
            'cmake '
            '-H"/MyCPFProject/Sources" '
            '-B"/MyCPFProject/Generated/MyConfig" '
            '-C"/MyCPFProject/Configuration/MyConfig.config.cmake" '
            '--graphviz="/MyCPFProject/Generated/MyConfig/CPFDependencies.dot"'
            )
        self.assertEqual(self.sut.m_os_access.execute_command_arg[0][1], expected_command)


    def test_generate_make_files_picks_the_first_available_config_if_none_is_given_and_executes_an_incremental_generate_if_cache_exists(self):

        # Setup
        self.sut.m_os_access = self._get_fake_os_access(_WINDOWS)
        self.sut.m_fs_access.addfile(self.locations.get_full_path_config_file('MyConfig1'), "content")
        self.sut.m_fs_access.addfile(self.locations.get_full_path_config_file('MyConfig2'), "content")  
        self.sut.m_fs_access.addfile(self.locations.get_full_path_generated_folder() / "MyConfig1/CMakeCache.txt", "content")
        argv = {"<config_name>" : None, "--clean" : False}

        # execute
        self.assertTrue(self.sut.generate_make_files(argv))

        # verify
        expected_command = (
            'cmake '
            '"/MyCPFProject/Generated/MyConfig1" '
            '--graphviz="/MyCPFProject/Generated/MyConfig1/CPFDependencies.dot"'
            )
        self.assertEqual(self.sut.m_os_access.execute_command_arg[0][1], expected_command)


    def test_generate_make_files_picks_the_first_available_config_if_none_is_given_and_executes_a_fresh_generate_if_no_cache_exists(self):

        # Setup
        self.sut.m_os_access = self._get_fake_os_access(_WINDOWS)
        self.sut.m_fs_access.addfile(self.locations.get_full_path_config_file('MyConfig1'), "content")
        self.sut.m_fs_access.addfile(self.locations.get_full_path_config_file('MyConfig2'), "content")  
        self.sut.m_fs_access.addfile(self.locations.get_full_path_generated_folder() / "MyConfig2/CMakeCache.txt", "content")
        argv = {"<config_name>" : None, "--clean" : False}

        # execute
        self.assertTrue(self.sut.generate_make_files(argv))

        # verify
        expected_command = (
            'cmake '
            '-H"/MyCPFProject/Sources" '
            '-B"/MyCPFProject/Generated/MyConfig1" '
            '-C"/MyCPFProject/Configuration/MyConfig1.config.cmake" '
            '--graphviz="/MyCPFProject/Generated/MyConfig1/CPFDependencies.dot"'
            )
        self.assertEqual(self.sut.m_os_access.execute_command_arg[0][1], expected_command)


    def mock_config(self):
        """
        Creates a file in the configuration directory.
        """
        self.sut.m_fs_access.addfile(self.locations.get_full_path_config_file("MyConfig"), "content")
        return True


    @patch('python.buildautomat.BuildAutomat.configure', return_value=True)
    def test_generate_make_files_runs_configure_step_if_config_does_not_exist(self, mock_configure):

        # setup
        self.maxDiff = None
        self.sut.m_os_access = self._get_fake_os_access(_LINUX)
        argv = {"<config_name>" : "MyConfig", "--clean" : False}
        mock_configure.side_effect = self.mock_config()

        # execute
        self.assertTrue(self.sut.generate_make_files(argv))


    @patch('python.buildautomat.BuildAutomat.configure', return_value=False)
    def test_generate_make_files_returns_false_when_no_config_option_is_given_and_no_config_file_exists(self, mock_configure):
       
        # setup
        self.sut.m_os_access = self._get_fake_os_access(_LINUX)
        argv = {"<config_name>" : None, "--clean" : False}

        # execute
        self.assertFalse(self.sut.generate_make_files(argv))

        # verify
        # make sure an error message was issued
        self.assertTrue("Error:" in self.sut.m_os_access.console_output)


    @patch('python.miscosaccess.FakeMiscOsAccess.execute_command', return_value=False)
    def test_generate_make_files_returns_false_if_cmake_call_fails(self, mock_executeCommandAndPrintResult):
        # setup
        argv = {"<config_name>" : "MyConfig", "--clean" : False}

        # execute
        self.assertFalse(self.sut.generate_make_files(argv))


####################################################################################################

    def test_make_makes_the_correct_cmake_call_when_all_options_are_given(self):
        # setup
        self.sut.m_os_access = self._get_fake_os_access(_WINDOWS)
        self.sut.m_fs_access.addfile(self.locations.get_full_path_config_file('MyConfig'), "content")
        self.sut.m_fs_access.addfile(self.locations.get_full_path_config_makefile_folder('MyConfig') / 'CMakeCache.txt', "content")
        cpu_count = 1
        argv = {"<config_name>" : "MyConfig", "--target" : "myTarget", "--config" : "Debug", "--clean" : True, "--cpus" : str(cpu_count)}

        # execute
        self.assertTrue(self.sut.make(argv))

        #verify
        expected_cmake_call = (
            'cmake'
            ' --build "/MyCPFProject/Generated/MyConfig"'
            ' --target myTarget'
            ' --config Debug'
            ' --clean-first'
            ' --parallel ' + str(cpu_count)
            )
        self.assertEqual(self.sut.m_os_access.execute_command_arg[0][1], expected_cmake_call)


    def test_make_makes_the_correct_incremental_cmake_call_when_no_options_are_given(self):

        # Setup
        # note that the function should pick the config that has a cachefile
        self.sut.m_fs_access.addfile(self.locations.get_full_path_config_file('A_Config'), "content")
        self.sut.m_fs_access.addfile(self.locations.get_full_path_config_file('B_Config'), "content")
        self.sut.m_fs_access.addfile(self.locations.get_full_path_config_file('C_Config'), "content")
        self.sut.m_fs_access.addfile(self.locations.get_full_path_generated_folder() / "B_Config/CMakeCache.txt", "content")
        argv = {"<config_name>" : None, "--target" : None, "--config" : None, "--clean" : False, "--cpus" : None}

        # execute
        self.assertTrue(self.sut.make(argv))

        #verify
        expected_cmake_call = (
            'cmake'
            ' --build "/MyCPFProject/Generated/B_Config"'
            ' --parallel ' + str(self.cpu_count)
            )
        self.assertEqual(self.sut.m_os_access.execute_command_arg[0][1], expected_cmake_call)


    def mock_configure_impl(self, argv):
        self.mock_configure_called = True
        # create the config file
        self.sut.m_fs_access.addfile(self.locations.get_full_path_config_file('MyConfig'), "content")
        return True


    def mock_generate_make_files_impl(self, argv):
        self.mock_generate_args = argv
        self.mock_generate_called = True
        
        # create the cache file
        self.sut.m_fs_access.addfile(self.locations.get_full_path_generated_folder() / "MyConfig/CMakeCache.txt", "content")
        return True


    @patch('python.buildautomat.BuildAutomat.generate_make_files')
    #@mock.patch('Sources.CPFBuildscripts.python.buildautomat.BuildAutomat.configure')
    def test_make_calls_generate_if_no_cache_file_exists(self, mock_generate_make_files):
        # setup
        self.sut.m_fs_access.addfile(self.locations.get_full_path_config_file('MyConfig'), "content")

        self.mock_generate_called = []
        mock_generate_make_files.side_effect = self.mock_generate_make_files_impl

        argv = {
            "<config_name>" : 'MyConfig',
            "--target" : None,
            "--config" : None,
            "--clean" : False,
            "--cpus" : None
            }

        # execute
        self.assertTrue(self.sut.make(argv))

        # verify
        self.assertTrue(self.sut.m_fs_access.exists(self.locations.get_full_path_generated_folder() / "MyConfig/CMakeCache.txt"))
        self.assertTrue(self.mock_generate_called)
        

    @patch('python.buildautomat.BuildAutomat.configure')
    @patch('python.buildautomat.BuildAutomat._call_cmake_for_existing_cache_file')
    def test_make_calls_configure_if_no_config_file_exists(self, mock_generate_make_files, mock_configure):
        # setup
        self.sut.m_fs_access.addfile(self.locations.get_full_path_generated_folder() / "MyConfig/CMakeCache.txt", "content")
        
        self.mock_configure_called = False
        mock_configure.side_effect = self.mock_configure_impl

        argv = {
            "<config_name>" : 'MyConfig',
            "--target" : None,
            "--config" : None,
            "--clean" : False,
            "--cpus" : None
            }

        # execute
        self.assertTrue(self.sut.make(argv))

        # verify
        self.assertTrue(self.mock_configure_called)
        self.sut.m_fs_access.exists(self.locations.get_full_path_config_file('MyConfig'))

