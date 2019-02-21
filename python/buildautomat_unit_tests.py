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
        self.cpf_root = "/MyCPFProject"
        self.path_to_common_tools = "C:\\path\\to\\CommonTools\\"
        self.cpu_count = 4

        # Setup the system under test
        self.sut = buildautomat.BuildAutomat()

        # Replace the FileSystemAccess with a fake implementation that contains
        # The basic folder and file structure.
        self.locations = filelocations.FileLocations(self.cpf_root)
        self.sut.m_file_locations = self.locations
        self.sut.m_fs_access = filesystemaccess.FakeFileSystemAccess()
        # self.sut.m_fs_access.mkdirs(self.locations.getFullPathInfrastructureFolder())
        self.sut.m_fs_access.mkdirs(self.locations.get_full_path_source_folder())
        self.sut.m_fs_access.mkdirs(self.locations.get_full_path_source_folder())

        # add some source files
        # Module1
        self.sut.m_fs_access.addfile(
            self.locations.get_full_path_source_folder() / "Module1/bla.h",
            "content")
        self.sut.m_fs_access.addfile(
            self.locations.get_full_path_source_folder() / "Module1/bla.cpp",
            "content")
        self.sut.m_fs_access.addfile(
            self.locations.get_full_path_source_folder() / "Module1/bla.ui",
            "content")
        # Module2
        self.sut.m_fs_access.addfile(
            self.locations.get_full_path_source_folder() / "Module2/blub.h",
            "content")
        # Module3
        self.sut.m_fs_access.addfile(
            self.locations.get_full_path_source_folder() / "Module3/blar.cpp",
            "content")
        # cmake
        self.sut.m_fs_access.mkdirs(self.locations.get_full_path_source_folder() / "cmake")

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

    def test_configure_executes_the_correct_cmake_command(self):
        # setup
        self.maxDiff = None
        self.sut.m_os_access = self._get_fake_os_access(_WINDOWS)
        args = {
            "<config_name>" : "MyConfig",
            "--inherits" : "MyProjectConfig",
            "-D" : [
                'CMAKE_GENERATOR=Visual Studio 14 2015 Amd64',
                'CPF_TEST_FILES_DIR=C:/Temp bla/Tests'] # note that argument values do not
                                                                # have quotes when they come in
                                                                # from docopt
            }

        # execute
        self.assertTrue(self.sut.configure(args))

        # verify
        expected_command = (
            'cmake '
            '-DDERIVED_CONFIG=MyConfig '
            '-DPARENT_CONFIG=MyProjectConfig '
            '-DCMAKE_GENERATOR="Visual Studio 14 2015 Amd64" '
            '-DCPF_TEST_FILES_DIR="C:/Temp bla/Tests" '
            '-P "/MyCPFProject/Sources/CPFCMake/Scripts/createConfigFile.cmake"'
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
            '-DDERIVED_CONFIG=MyConfig '
            '-DPARENT_CONFIG=Windows '
            '-P "/MyCPFProject/Sources/CPFCMake/Scripts/createConfigFile.cmake"'
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
            '-DDERIVED_CONFIG=MyConfig '
            '-DPARENT_CONFIG=Linux '
            '-P "/MyCPFProject/Sources/CPFCMake/Scripts/createConfigFile.cmake"'
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


    def test_generate_make_files_returns_false_when_config_option_is_given_but_config_file_does_not_exist(self):

        # setup
        self.maxDiff = None
        self.sut.m_os_access = self._get_fake_os_access(_LINUX)
        argv = {"<config_name>" : "MyConfig", "--clean" : False}

        # execute
        self.assertFalse(self.sut.generate_make_files(argv))

        # verify
        # make sure an error message was issued
        self.assertTrue("error:" in self.sut.m_os_access.console_output)


    def test_generate_make_files_returns_false_when_no_config_option_is_given_and_no_config_file_exists(self):
        # setup
        self.sut.m_os_access = self._get_fake_os_access(_LINUX)
        argv = {"<config_name>" : None, "--clean" : False}

        # execute
        self.assertFalse(self.sut.generate_make_files(argv))

        # verify
        # make sure an error message was issued
        self.assertTrue("error:" in self.sut.m_os_access.console_output)
        # make sure cmake was never executed
        self.assertTrue("cmake" not in self.sut.m_os_access.console_output)


    @patch('Sources.CPFBuildscripts.python.miscosaccess.FakeMiscOsAccess.execute_command', return_value=False)
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

        cmake_inspection_call_stdout = (
            "CMAKE_C_COMPILER:FILEPATH=C:/Program Files (x86)/Microsoft Visual Studio 14.0/Common7/Tools/../../VC/bin/x86_amd64/cl.exe\n"
            "CMAKE_GENERATOR:STRING=Visual Studio 14 2015 Win64\n"
            "CMAKE_INSTALL_PREFIX:PATH=C:/Program Files/CMakeProjectFramework\n"
        )
        self.sut.m_os_access.execute_commands_in_parallel_results = [[{'returncode':0, 'stdout' : cmake_inspection_call_stdout}]]
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
            ' -- /maxcpucount:' + str(cpu_count)
            )
        self.assertEqual(self.sut.m_os_access.execute_command_arg[0][1], expected_cmake_call)


    def test_make_makes_the_correct_incremental_cmake_call_when_no_options_are_given(self):

        # Setup
        # note that the function should pick the config that has a cachefile
        self.sut.m_fs_access.addfile(self.locations.get_full_path_config_file('A_Config'), "content")
        self.sut.m_fs_access.addfile(self.locations.get_full_path_config_file('B_Config'), "content")
        self.sut.m_fs_access.addfile(self.locations.get_full_path_config_file('C_Config'), "content")
        self.sut.m_fs_access.addfile(self.locations.get_full_path_generated_folder() / "B_Config/CMakeCache.txt", "content")
        self.sut.m_os_access.execute_commands_in_parallel_results = [[{'returncode':0, 'stdout' : "CMAKE_GENERATOR:STRING=Visual Studio 14 2015 Win64\n"}]]
        argv = {"<config_name>" : None, "--target" : None, "--config" : None, "--clean" : False, "--cpus" : None}

        # execute
        self.assertTrue(self.sut.make(argv))

        #verify
        expected_cmake_call = (
            'cmake'
            ' --build "/MyCPFProject/Generated/B_Config"'
            ' -- /maxcpucount:' + str(self.cpu_count)
            )
        self.assertEqual(self.sut.m_os_access.execute_command_arg[0][1], expected_cmake_call)


    def test_make_uses_the_correct_multicpuoption_for_unix_makefiles(self):
        # setup
        self.sut.m_fs_access.addfile(self.locations.get_full_path_config_file('MyConfig'), "content")
        self.sut.m_fs_access.addfile(self.locations.get_full_path_generated_folder() / "MyConfig/CMakeCache.txt", "content")
        self.sut.m_os_access.execute_commands_in_parallel_results = [[{'returncode':0, 'stdout' : "CMAKE_GENERATOR:STRING=Unix Makefiles\n"}]]
        argv = {"<config_name>" : 'MyConfig', "--target" : None, "--config" : None, "--clean" : False, "--cpus" : None}

        # execute
        self.assertTrue(self.sut.make(argv))
        
        #verify
        expected_cmake_call = (
            'cmake'
            ' --build "/MyCPFProject/Generated/MyConfig"'
            ' -- -j' + str(self.cpu_count)
            )
        self.assertEqual(self.sut.m_os_access.execute_command_arg[0][1] , expected_cmake_call)


    def test_make_uses_the_correct_multicpuoption_for_ninja(self):
        # setup
        self.sut.m_fs_access.addfile(self.locations.get_full_path_config_file('MyConfig'), "content")
        self.sut.m_fs_access.addfile(self.locations.get_full_path_generated_folder() / "MyConfig/CMakeCache.txt", "content")
        self.sut.m_os_access.execute_commands_in_parallel_results = [[{'returncode':0, 'stdout' : "CMAKE_GENERATOR:STRING=Ninja\n"}]]
        argv = {"<config_name>" : None, "--target" : None, "--config" : None, "--clean" : False, "--cpus" : None}

        # execute
        self.assertTrue(self.sut.make(argv))
        
        #verify
        expected_cmake_call = (
            'cmake'
            ' --build "/MyCPFProject/Generated/MyConfig"'
            ' -- -j' + str(self.cpu_count)
            )
        self.assertEqual(self.sut.m_os_access.execute_command_arg[0][1] , expected_cmake_call)
