"""
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
        self.codebase_root = "/MyCppCodeBase"
        self.path_to_common_tools = "C:\\path\\to\\CommonTools\\"
        self.cpu_count = 4

        # Setup the system under test
        self.sut = buildautomat.BuildAutomat()

        # Replace the FileSystemAccess with a fake implementation that contains
        # The basic folder and file structure.
        self.locations = filelocations.FileLocations(self.codebase_root)
        self.sut.m_file_locations = self.locations
        self.sut.m_fs_access = filesystemaccess.FakeFileSystemAccess()
        # self.sut.m_fs_access.mkdirs(self.locations.getFullPathInfrastructureFolder())
        self.sut.m_fs_access.mkdirs(self.locations.get_full_path_source_folder())
        self.sut.m_fs_access.mkdirs(self.locations.get_full_path_source_folder())

        # add some source files
        # Module1
        self.sut.m_fs_access.addfile(
            self.locations.get_full_path_source_folder() + "/Module1/bla.h",
            "content")
        self.sut.m_fs_access.addfile(
            self.locations.get_full_path_source_folder() + "/Module1/bla.cpp",
            "content")
        self.sut.m_fs_access.addfile(
            self.locations.get_full_path_source_folder() + "/Module1/bla.ui",
            "content")
        # Module2
        self.sut.m_fs_access.addfile(
            self.locations.get_full_path_source_folder() + "/Module2/blub.h",
            "content")
        # Module3
        self.sut.m_fs_access.addfile(
            self.locations.get_full_path_source_folder() + "/Module3/blar.cpp",
            "content")
        # cmake
        self.sut.m_fs_access.mkdirs(self.locations.get_full_path_source_folder() + "/cmake")

        # use the windows os access as default
        self.sut.m_os_access = self._get_fake_os_access(_WINDOWS)


    def _get_fake_os_access(self, operating_system):
        return miscosaccess.FakeMiscOsAccess(
            self.sut.m_fs_access,
            self.codebase_root,
            {},
            operating_system,
            self.cpu_count)


####################################################################################################

    def test_configure_executes_the_correct_cmake_command(self):
        # setup
        self.maxDiff = None
        self.sut.m_os_access = self._get_fake_os_access(_WINDOWS)
        args = {
            "<config_name>" : "MyConfig",
            "--inherits" : "MyProjectConfig",
            "-D" : [
                'CMAKE_GENERATOR=Visual Studio 14 2015 Amd64',
                'CCB_TEST_FILES_DIR=C:/Temp bla/Tests'] # note that argument values do not
                                                                # have quotes when they come in
                                                                # from docopt
            }

        # execute
        self.assertTrue(self.sut.configure(args))

        # verify
        expected_command = (
            'cmake '
            '-DCCB_CONFIG=MyConfig '
            '-DPARENT_CONFIG=MyProjectConfig '
            '-DCMAKE_GENERATOR="Visual Studio 14 2015 Amd64" '
            '-DCCB_TEST_FILES_DIR="C:/Temp bla/Tests" '
            '-P "/MyCppCodeBase/Sources/CppCodeBaseCMake/Scripts/createConfigFile.cmake"'
            )
        self.assertEqual(
            self.sut.m_os_access.execute_command_arg[0][1],
            expected_command)

    def test_configure_sets_correct_default_inheritance_on_windows(self):
        # setup
        self.maxDiff = None
        self.sut.m_os_access = self._get_fake_os_access(_WINDOWS)
        args = {
            "<config_name>" : "MyConfig",
            "--inherits" : None,
            "-D" : []
            }

        # execute
        self.assertTrue(self.sut.configure(args))

        # verify
        expected_command = (
            'cmake '
            '-DCCB_CONFIG=MyConfig '
            '-DPARENT_CONFIG=Windows '
            '-P "/MyCppCodeBase/Sources/CppCodeBaseCMake/Scripts/createConfigFile.cmake"'
            )
        self.assertEqual(
            self.sut.m_os_access.execute_command_arg[0][1],
            expected_command)

    def test_configure_sets_correct_default_inheritance_on_linux(self):
        # setup
        self.maxDiff = None
        self.sut.m_os_access = self._get_fake_os_access(_LINUX)
        args = {
            "<config_name>" : "MyConfig",
            "--inherits" : None,
            "-D" : []
            }

        # execute
        self.assertTrue(self.sut.configure(args))

        # verify
        expected_command = (
            'cmake '
            '-DCCB_CONFIG=MyConfig '
            '-DPARENT_CONFIG=Linux '
            '-P "/MyCppCodeBase/Sources/CppCodeBaseCMake/Scripts/createConfigFile.cmake"'
            )
        self.assertEqual(
            self.sut.m_os_access.execute_command_arg[0][1],
            expected_command)


####################################################################################################

    def test_generate_make_files_executes_the_correct_calls_when_config_option_is_given(self):

        # setup
        self.maxDiff = None
        self.sut.m_os_access = self._get_fake_os_access(_LINUX)
        path_in_make_file_folder = self.locations.get_full_path_generated_folder() + "/MyConfig/blib"
        # add an extra directory in the makefile directory so we can check that
        # the folder was cleared
        self.sut.m_fs_access.mkdirs(path_in_make_file_folder)
        self.sut.m_fs_access.addfile(self.locations.get_full_path_config_file('MyConfig'), "content")
        argv = {"<config_name>" : "MyConfig"}

        # execute
        self.assertTrue(self.sut.generate_make_files(argv))

        # verify
        # makefile folder is cleared when the <config_name> argument is given
        self.assertFalse(self.sut.m_fs_access.isdir(path_in_make_file_folder))

        # cmake is called with correct arguments
        expected_command = (
            'cmake '
            '-H"/MyCppCodeBase/Sources" '
            '-B"/MyCppCodeBase/Generated/MyConfig" '
            '-C"/MyCppCodeBase/Configuration/MyConfig.config.cmake" '
            '--graphviz="/MyCppCodeBase/Generated/MyConfig/CppCodeBaseDependencies.dot"'
            )

        self.assertEqual(self.sut.m_os_access.execute_command_arg[0][1], expected_command)


    def test_generate_make_files_executes_the_correct_calls_when_no_config_option_is_given_and_only_a_config_file_exists(self):

        # Setup
        self.sut.m_os_access = self._get_fake_os_access(_WINDOWS)
        self.sut.m_fs_access.addfile(self.locations.get_full_path_config_file('MyConfig'), "content")
        argv = {"<config_name>" : None}


        # execute
        self.assertTrue(self.sut.generate_make_files(argv))

        # verify
        expected_command = (
            'cmake '
            '-H"/MyCppCodeBase/Sources" '
            '-B"/MyCppCodeBase/Generated/MyConfig" '
            '-C"/MyCppCodeBase/Configuration/MyConfig.config.cmake" '
            '--graphviz="/MyCppCodeBase/Generated/MyConfig/CppCodeBaseDependencies.dot"'
            )
        self.assertEqual(self.sut.m_os_access.execute_command_arg[0][1], expected_command)


    def test_generate_make_files_executes_the_correct_calls_when_no_config_option_is_given_and_a_config_file_and_a_cachefile_exists(self):

        # Setup
        self.sut.m_os_access = self._get_fake_os_access(_WINDOWS)
        self.sut.m_fs_access.addfile(self.locations.get_full_path_config_file('MyConfig'), "content")
        self.sut.m_fs_access.addfile(self.locations.get_full_path_generated_folder() + "/MyConfig/CMakeCache.txt", "content")
        argv = {"<config_name>" : None}

        # execute
        self.assertTrue(self.sut.generate_make_files(argv))

        # verify
        expected_command = (
            'cmake '
            '"/MyCppCodeBase/Generated/MyConfig" '
            '--graphviz="/MyCppCodeBase/Generated/MyConfig/CppCodeBaseDependencies.dot"'
            )
        self.assertEqual(self.sut.m_os_access.execute_command_arg[0][1], expected_command)


    def test_generate_make_files_returns_false_when_config_option_is_given_but_config_file_does_not_exist(self):

        # setup
        self.maxDiff = None
        self.sut.m_os_access = self._get_fake_os_access(_LINUX)
        argv = {"<config_name>" : "MyConfig"}

        # execute
        self.assertFalse(self.sut.generate_make_files(argv))

        # verify
        # make sure an error message was issued
        self.assertTrue("error:" in self.sut.m_os_access.console_output)


    def test_generate_make_files_returns_false_when_no_config_option_is_given_and_no_config_file_exists(self):
        # setup
        self.sut.m_os_access = self._get_fake_os_access(_LINUX)
        argv = {"<config_name>" : None}

        # execute
        self.assertFalse(self.sut.generate_make_files(argv))

        # verify
        # make sure an error message was issued
        self.assertTrue("error:" in self.sut.m_os_access.console_output)
        # make sure cmake was never executed
        self.assertTrue("cmake" not in self.sut.m_os_access.console_output)


    @patch('cppcodebasebuildscripts.miscosaccess.FakeMiscOsAccess.execute_command', return_value=False)
    def test_generate_make_files_returns_false_if_cmake_call_fails(self, mock_executeCommandAndPrintResult):
        # setup
        argv = {"<config_name>" : "MyConfig"}

        # execute
        self.assertFalse(self.sut.generate_make_files(argv))


####################################################################################################

    def test_make_makes_the_correct_cmake_call_when_all_options_are_given(self):
        # setup
        self.sut.m_os_access = self._get_fake_os_access(_WINDOWS)
        self.sut.m_fs_access.addfile(self.locations.get_full_path_config_file('MyConfig'), "content")
        self.sut.m_fs_access.addfile(self.locations.get_full_path_config_makefile_folder('MyConfig') + '/CMakeCache.txt', "content")

        cmake_inspection_call_stdout = (
            "CMAKE_C_COMPILER:FILEPATH=C:/Program Files (x86)/Microsoft Visual Studio 14.0/Common7/Tools/../../VC/bin/x86_amd64/cl.exe\n"
            "CMAKE_GENERATOR:STRING=Visual Studio 14 2015 Win64\n"
            "CMAKE_INSTALL_PREFIX:PATH=C:/Program Files/CppCodeBase\n"
        )
        self.sut.m_os_access.execute_commands_in_parallel_results = [[{'returncode':0, 'stdout' : cmake_inspection_call_stdout}]]
        cpu_count = 1
        argv = {"<config_name>" : "MyConfig", "--target" : "myTarget", "--config" : "Debug", "--cpus" : str(cpu_count)}

        # execute
        self.assertTrue(self.sut.make(argv))

        #verify
        expected_cmake_call = (
            'cmake'
            ' --build "/MyCppCodeBase/Generated/MyConfig"'
            ' --target myTarget'
            ' --config Debug'
            ' --clean-first'
            ' -- /maxcpucount:' + str(cpu_count)
            )
        self.assertEqual(self.sut.m_os_access.execute_command_arg[0][1], expected_cmake_call)


    def test_make_makes_the_correct_incremental_cmake_call_when_no_options_are_given(self):

        # Setup
        # note that the function should pick the config that has a cachefile
        self.sut.m_fs_access.addfile(self.locations.get_full_path_config_file('A_Config'), "content")
        self.sut.m_fs_access.addfile(self.locations.get_full_path_config_file('B_Config'), "content")
        self.sut.m_fs_access.addfile(self.locations.get_full_path_config_file('C_Config'), "content")
        self.sut.m_fs_access.addfile(self.locations.get_full_path_generated_folder() + "/B_Config/CMakeCache.txt", "content")
        self.sut.m_os_access.execute_commands_in_parallel_results = [[{'returncode':0, 'stdout' : "CMAKE_GENERATOR:STRING=Visual Studio 14 2015 Win64\n"}]]
        argv = {"<config_name>" : None, "--target" : None, "--config" : None, "--cpus" : None}

        # execute
        self.assertTrue(self.sut.make(argv))

        #verify
        expected_cmake_call = (
            'cmake'
            ' --build "/MyCppCodeBase/Generated/B_Config"'
            ' -- /maxcpucount:' + str(self.cpu_count)
            )
        self.assertEqual(self.sut.m_os_access.execute_command_arg[0][1], expected_cmake_call)


    def test_make_uses_the_correct_multicpuoption_for_unix_makefiles(self):
        # setup
        self.sut.m_fs_access.addfile(self.locations.get_full_path_config_file('MyConfig'), "content")
        self.sut.m_fs_access.addfile(self.locations.get_full_path_generated_folder() + "/MyConfig/CMakeCache.txt", "content")
        self.sut.m_os_access.execute_commands_in_parallel_results = [[{'returncode':0, 'stdout' : "CMAKE_GENERATOR:STRING=Unix Makefiles\n"}]]
        argv = {"<config_name>" : None, "--target" : None, "--config" : None, "--cpus" : None}

        # execute
        self.assertTrue(self.sut.make(argv))
        
        #verify
        expected_cmake_call = (
            'cmake'
            ' --build "/MyCppCodeBase/Generated/MyConfig"'
            ' -- -j' + str(self.cpu_count)
            )
        self.assertEqual(self.sut.m_os_access.execute_command_arg[0][1] , expected_cmake_call)


    def test_make_uses_the_correct_multicpuoption_for_ninja(self):
        # setup
        self.sut.m_fs_access.addfile(self.locations.get_full_path_config_file('MyConfig'), "content")
        self.sut.m_fs_access.addfile(self.locations.get_full_path_generated_folder() + "/MyConfig/CMakeCache.txt", "content")
        self.sut.m_os_access.execute_commands_in_parallel_results = [[{'returncode':0, 'stdout' : "CMAKE_GENERATOR:STRING=Ninja\n"}]]
        argv = {"<config_name>" : None, "--target" : None, "--config" : None, "--cpus" : None}

        # execute
        self.assertTrue(self.sut.make(argv))
        
        #verify
        expected_cmake_call = (
            'cmake'
            ' --build "/MyCppCodeBase/Generated/MyConfig"'
            ' -- -j' + str(self.cpu_count)
            )
        self.assertEqual(self.sut.m_os_access.execute_command_arg[0][1] , expected_cmake_call)
