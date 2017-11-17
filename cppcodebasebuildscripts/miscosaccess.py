#!/usr/bin/python3

import subprocess
import platform
import sys
import os
import shutil
from shutil import copyfile
import shlex
import multiprocessing

from . import filesystemaccess


class MiscOsAccess:
    """
    Wraps some miscellaneous functions that access the functionality of the operating system.
    This allows replacing the calls to these functions in tests.
    """
    def executeCommandAndPrintResult(self, command):
        """
        Executes the command and prints the result. Returns true if the errorcode was 0.
        Use this version when you do not need the output string and only run one command
        in parallel.
        """
        try:
            print(self._getPrintedCommand(command))
            return subprocess.check_call(command, shell=True) == 0

        except subprocess.CalledProcessError as e:
            print(e.output)
            return False


    def runCommandsInMultipleProcesses(self, commands, cwd=None, printOutput=True):
        """
        Executes multiple command-line commands in parallel.
        The commands should be given in one string, like it would be typed into the command line.
        The return code, standard output and error output can be retrieved from the returned list of dictionaries.
        """

        # Start one process for each command
        #processes = [[subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE), cmd] for cmd in commands]
        processes = [[subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=cwd), cmd] for cmd in commands]
    
        # Wait for the porcesses to finish and collect the results
        results = []
        for process in processes:
        
            # wait for process to finish and get output
            out, err = process[0].communicate()
        
            output = self._getPrintedCommand(process[1])
            output += out.decode("utf-8")
            errOutput = err.decode("utf-8")
            retCode = process[0].returncode
    
            if printOutput:
                print(output)
                print(errOutput)
    
            results.append({'returncode':retCode, 'stdout':output, 'stderr':errOutput })

        return results


    def _getPrintedCommand(self, command, cwd=None):
        workingDir = ''
        if cwd:
            workingDir = cwd
        else:
            workingDir = os.getcwd()

        return '\n-------------- Execute command in directory ' + workingDir + ':\n' + command + '\n'


    # allow mocking of print
    def printConsole(self, string):
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
    def __init__(self, fakeFileSystemAccess, currentDir, environmentVariables, system, cpu_count):
        """
        currentDir is the currentDirectory before any calls to chdir() are made.
        system (linux of windows)
        """
        self.fakeFileSystem = fakeFileSystemAccess  # Needed to check if chdir does anything.
        self.currentDir = currentDir
        self.envVars = environmentVariables
        self.executeCommandAndPrintResultArg = []  # a list of lists that contains 
        self.consoleOutput = "" # This will contain a concatenation of printed strings separated by \n
        self.m_system = system
        self.m_cpu_count = cpu_count
        self.runCommandInMultipleProcessesArgs = []
        self.runCommandInMultipleProcessesResults = []
        
    def executeCommandAndPrintResult(self, command):
        self.printConsole(self._getPrintedCommand(command))
        self.executeCommandAndPrintResultArg.append( [self.currentDir,command])
        return True


    def runCommandsInMultipleProcesses(self, commands, pwd=None, printOutput=True):
        self.runCommandInMultipleProcessesArgs.append([self.currentDir,commands])
        for command in commands:
            if printOutput:
                self.printConsole(self._getPrintedCommand(command))
        return self.runCommandInMultipleProcessesResults[len(self.runCommandInMultipleProcessesArgs)-1]

    def printConsole(self, string):
        self.consoleOutput = self.consoleOutput + string + "\n"

    def chdir(self, path):
        if self.fakeFileSystem.isdir(path):
            self.currentDir = path
        else:
            self.printConsole("Could not change to the given path \"" + path + "\".")

    def mkdir(self, path):
        if self._isRelativePath(path):
            path = self.currentDir + "/" + path
        self.fakeFileSystem.mkdir(path)

    def system(self):
        return self.m_system

    def cpu_count(self):
        return self.m_cpu_count

    def _isRelativePath(self, path):
        if self.m_system == "Windows":
            return ":" in path
        elif self.m_system == "Linux":
            return path[0] != "/"
        assert False


        
        






