#!/usr/bin/python3

import subprocess
import platform
import os
import multiprocessing

from . import filesystemaccess


class MiscOsAccess:
    """
    Wraps some miscellaneous functions that access the functionality of the operating system.
    This allows replacing the calls to these functions in tests.
    """
    def execute_command(self, command):
        """
        Executes the command and prints the result. Returns true if the errorcode was 0.
        Use this version when you do not need the output string and only run one command
        in parallel.
        """
        try:
            print(self._get_printed_command(command))
            return subprocess.check_call(command, shell=True) == 0

        except subprocess.CalledProcessError as exception:
            print(exception.output)
            return False


    def execute_commands_in_parallel(self, commands, cwd=None, printOutput=True):
        """
        Executes multiple command-line commands in parallel.
        The commands should be given in one string, like it would be typed into the command line.
        The return code, standard output and error output can be retrieved from the returned list of dictionaries.
        """

        # Start one process for each command
        processes = [[subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=cwd), cmd] for cmd in commands]

        # Wait for the porcesses to finish and collect the results
        results = []
        for process in processes:

            # wait for process to finish and get output
            out, err = process[0].communicate()

            output = self._get_printed_command(process[1])
            output += out.decode("utf-8")
            err_output = err.decode("utf-8")
            ret_code = process[0].returncode

            if printOutput:
                print(output)
                print(err_output)

            results.append({'returncode':ret_code, 'stdout':output, 'stderr':err_output})

        return results


    def _get_printed_command(self, command, cwd=None):
        working_dir = ''
        if cwd:
            working_dir = cwd
        else:
            working_dir = os.getcwd()

        return '\n-------------- Execute command in directory ' + working_dir + ':\n' + command + '\n'


    # allow mocking of print
    def print_console(self, string):
        print(string)

    def chdir(self, path):
        """Change the current directory"""
        os.chdir(path)

    def system(self):
        """Return the name of the platform (Linux or Windows in our case)"""
        return platform.system()

    def cpu_count(self):
        return multiprocessing.cpu_count()



class FakeMiscOsAccess(MiscOsAccess):
    """This class can be used to prevent calls to os dependent functions in tests"""
    def __init__(self, fakeFileSystemAccess, current_dir, environmentVariables, system, cpu_count):
        """
        current_dir is the currentDirectory before any calls to chdir() are made.
        system (linux of windows)
        """
        self.fake_file_system = fakeFileSystemAccess  # Needed to check if chdir does anything.
        self.current_dir = current_dir
        self.env_vars = environmentVariables
        self.execute_command_arg = []  # a list of lists that contains
        self.console_output = "" # This will contain a concatenation of printed strings separated by \n
        self.m_system = system
        self.m_cpu_count = cpu_count
        self.execute_commands_in_parallel_args = []
        self.execute_commands_in_parallel_results = []


    def execute_command(self, command):
        self.print_console(self._get_printed_command(command))
        self.execute_command_arg.append( [self.current_dir, command])
        return True


    def execute_commands_in_parallel(self, commands, pwd=None, printOutput=True):
        self.execute_commands_in_parallel_args.append([self.current_dir,commands])
        for command in commands:
            if printOutput:
                self.print_console(self._get_printed_command(command))
        return self.execute_commands_in_parallel_results[len(self.execute_commands_in_parallel_args)-1]

    def print_console(self, string):
        self.console_output = self.console_output + string + "\n"

    def chdir(self, path):
        if self.fake_file_system.isdir(path):
            self.current_dir = path
        else:
            self.print_console("Could not change to the given path \"" + path + "\".")

    def mkdir(self, path):
        if self._is_relative_path(path):
            path = self.current_dir + "/" + path
        self.fake_file_system.mkdir(path)

    def system(self):
        return self.m_system

    def cpu_count(self):
        return self.m_cpu_count

    def _is_relative_path(self, path):
        if self.m_system == "Windows":
            return ":" in path
        elif self.m_system == "Linux":
            return path[0] != "/"
        assert False
