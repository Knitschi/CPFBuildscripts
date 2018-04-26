#!/usr/bin/python3

import subprocess
import platform
import os
import multiprocessing
import locale

from . import filesystemaccess
from enum import Enum

############################################################################
class CalledProcessError(Exception):
    """
    Holds information about a failed subprocess call.
    """
    def __init__(self, returncode, cmd, stdout, cwd):
        self.returncode = returncode
        self.cmd = cmd
        self.stdout = stdout
        self.cwd = cwd

    def __str__(self):
        return 'Error! Failed to execute command:\n{0}\nin directory:\n{1}\nreturncode: {2}'.format(self.cmd, self.cwd, str(self.returncode))


############################################################################
class OutputMode(Enum):
    """
    Defines how the output of a subprocess calls is propagated to the
    output of the calling process.
    """
    ALWAYS = 0      # Print everything the subprocess prints
    ON_ERROR = 1    # Only print the output of the subprocess if it fails.
    NEVER = 2       # Never print the output of the subprocess.

############################################################################
class MiscOsAccess:
    """
    Wraps some miscellaneous functions that access the functionality of the operating system.
    This allows replacing the calls to these functions in tests.
    """

    def execute_command(self, command, cwd=None):
        """
        Executes the command and prints the result. Returns true if the errorcode was 0.
        Use this version when you do not need the output string and only run one command
        in parallel.
        """
        try:
            self.execute_command_output(command, cwd=cwd, print_output=OutputMode.ALWAYS, print_command=True)
            return True

        except CalledProcessError as err:
            print(str(err))
            return False


    def execute_command_output(self, command, cwd=None, print_output=OutputMode.ALWAYS, print_command=False):
        """
        Executes the given command and returns a list with that contains the output lines of the process.
        The function will print output as soon as it is created when setting the print_output option.
        Note that when your command runs a python script, you have to add the python -u option to make
        sure the output is displayed immediately.

        The function throws a CalledProcessError when the command fails.

        The function currently only uses utf-8 encoded output strings. Other variants caused errors
        when calling python scripts that also call this function.
        """
        if cwd:
            working_dir = str(cwd)
        else:
            working_dir = os.getcwd()

        printed_command = self._get_printed_command(command, cwd=working_dir)
        if print_command:
            print(printed_command)

        stdoutstrings = []
        # The shell=True argument makes sure we can call commands in one string on linux
        # The pipes are required to enable us polling output while it is produced.
        # We need to pipe raw bite-streams here instead of using the encoding argument
        # because of the troubles that are described below.
        with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=-1, cwd=working_dir, shell=True ) as p:
        #with subprocess.Popen(command, bufsize=1, cwd=working_dir, shell=True ) as p:
            # poll output as it comes in
            for line in p.stdout:
                # Decoding with utf8 will throw exceptions if ignore is not set.
                # Forcing this will remove characters like german umlaute from the output.
                # This was the only codec I could find that worked when doing nested calls of the function
                # by calling another python script that uses it.
                lineString = line.decode('utf-8', errors="ignore").rstrip()
                if print_output == OutputMode.ALWAYS:
                    print(lineString)
                stdoutstrings.append(lineString)


        if p.returncode != 0:
            # print output in any case if an error occurred
            if print_output == OutputMode.ON_ERROR:
                print('\n'.join(stdoutstrings))

            raise CalledProcessError(p.returncode, command, '\n'.join(stdoutstrings), working_dir)

        return stdoutstrings


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

            output = self._get_printed_command(process[1], cwd=cwd)
            output += out.decode("utf-8")
            err_output = err.decode("utf-8")
            ret_code = process[0].returncode

            if printOutput:
                print(output)
                print(err_output)

            results.append({'returncode':ret_code, 'stdout':output, 'stderr':err_output})

        return results


    def _remove_line_separators(self, stringlist):
        new_list = []
        for string in stringlist:
            new_list.append(string.rstrip())
        return new_list


    def _get_printed_command(self, command, cwd=None):
        working_dir = ''
        if cwd:
            working_dir = cwd
        else:
            working_dir = os.getcwd()

        return '\n-------------- Execute command in directory ' + str(working_dir) + ':\n' + command + '\n'


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
