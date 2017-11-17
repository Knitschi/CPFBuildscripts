#!/usr/bin/python3

import os
import shutil


class FileSystemAccess:
    """
    This class wraps the accesses to the file-system to
    allow the usage of a fake file-system for tests.
    """

    def exists(self, path):
        """Returns true if the path exists."""
        return os.path.exists(path)

    def isfile(self, path):
        """Returns true if the path leads to a file."""
        return os.path.isfile(path)

    def isdir(self, path):
        """Returns true if the path leads to a directory."""
        return os.path.isdir(path)

    def mkdir(self,path):
        """Creates a directory. The parent directory must exist."""
        return os.mkdir(path)

    def mkdirs(self, path):
        """Creates multiple directories. This will not throw an error if a directory already exists."""
        return os.makedirs(path, 0o777,True)

    def listdir(self, path):
        """
        Returns all entries in the directory given by path except . and .. . 
        Throws when path does not exist?
        """
        return os.listdir(path)

    def rmtree(self, path):
        """Removes a directory and all of its content."""
        shutil.rmtree(path)

    def copyfile(self, pathFrom, pathTo):
        """Copies a file."""
        shutil.copyfile(pathFrom, pathTo)


class FakeFileSystemAccess():
    """
    An implementation of FileSystemAccess that does not access the actual file-system.
    Files are kept only in memory. 
    Currently files do not contain any data and have no access-right properties.
    The FakeFileSystemAccess is used to simplify mocking of file-system functions.    
    """

    def __init__(self):
        self.root = FakeFileSystemNode("root")

    def exists(self, path):
        return self._getDeepSubnodeWithPath(path) is not None

    def isfile(self, path):
        node = self._getDeepSubnodeWithPath(path)
        if node is not None:
            return not node.isDir
        return False

    def isdir(self, path):
        node = self._getDeepSubnodeWithPath(path)
        if node is not None:
            return node.isDir
        return False

    def listdir(self, path):
        node = self._getDeepSubnodeWithPath(path)
        if node is not None and node.isDir:
            return [x.name for x in node.children]
        raise Exception('Path "' + path + '" does not exist or is not a directory.')

    def rmtree(self, path):
        # check if path is valid
        if not self.isdir(path):
            raise Exception("The path \"" + path + "\" given to rmtree() does not lead to a directory.")     
           
        parentDirs, dir = _getPathAsHeadAndTailList(path)
        parentNode = self._getDeepSubnode(parentDirs)
        parentNode.children = [x for x in parentNode.children if x.name != dir]    # filter out the directory.
        return

    def copyfile(self, pathFrom, pathTo):
        if pathFrom == pathTo:
            raise Exception("Can not use the same source and destination path (\"" + pathFrom + "\") in filesystemaccess.copyfile()")
        # get fileFrom node
        fileNodeFrom = self._getDeepSubnodeWithPath(pathFrom)

        if fileNodeFrom is None:
            raise Exception("Source file \"" + pathFrom + "\" does not exist in filesystemaccess.copyfile()")

        if fileNodeFrom.isDir:
            raise Exception("Source \"" + pathFrom + "\" is a path to a directory but must be a path to a file in filesystemaccess.copyfile()")

        # get dirTo node
        dirsTo, filenameTo = _getPathAsHeadAndTailList(pathTo)
        dirToNode = self._getDeepSubnode(dirsTo)
        if dirToNode is None:
            raise Exception("The destination directory for file \"" + pathTo + "\" does not exist in filesystemaccess.copyfile()")        
        # copy file 
        fileToNode = dirToNode.getChild(filenameTo)
        if fileToNode is not None:  # overwrite existing one
            fileToNode.content = fileNodeFrom.content
        else:   # create new
            dirToNode.addChild(FakeFileSystemFileNode(filenameTo, fileNodeFrom.content))
        return

    #------------------------------------------------------------

    def hasfile(self,path,content):
        fileNode = self._getDeepSubnodeWithPath(path)
        if fileNode is None or fileNode.isDir or fileNode.content != content:
            return False
        return True

    def addfile(self, path, content):
        dirs, filename = _getPathAsHeadAndTailList(path)
        node = self._createDirectoryNodes(dirs)
        if not node.hasChild(filename):
            node.addChild(FakeFileSystemFileNode(filename,content))

    def mkdir(self,path):
        """ 
        Unlike mkdirs this behaves more like os.mkdir() which only can create one dir at a time.
        But path must be absolute.
        """
        subdirs, newDir = _getPathAsHeadAndTailList(path)
        if subdirs and self._getDeepSubnode(subdirs) is None:
            raise Exception("FakeFileSystemAccess.mkdir(): The parent directory of the created directory \"" + path + "\" must exist.")

        if self.exists(path):
            raise Exception("FakeFileSystemAccess.mkdir(): Path \"" + path + "\" points to an existing file or directory.")

        self.mkdirs(path)

    def mkdirs(self,path):
        dirs = _getPathAsList(path)
        self._createDirectoryNodes(dirs)

    def _getDeepSubnode(self, nodeList):
        node = self.root
        for nodeName in nodeList:
            if node.hasChild(nodeName):
                node = node.getChild(nodeName)
            else:
                return None
        return node

    def _getDeepSubnodeWithPath(self, path):
        nodes = _getPathAsList(path)
        return self._getDeepSubnode(nodes)

    def _createDirectoryNodes(self, nodeNameList):
        # create or get the directory nodes
        node = self.root
        for dir in nodeNameList:
            child = node.getChild(dir)
            if child is None:
                newNode = FakeFileSystemNode(dir)
                node.addChild(newNode)
                node = newNode
            else:
                node = child
        return node



class FakeFileSystemNode:
    """
    Represents a directory in the file-system tree.
    """
    def __init__(self, name):
       self.name = name
       self.isDir = True
       self.children = []

    def addChild(self, node):
        if not self.hasChild(node.name):
            self.children.append(node)
        else:
            raise Exception("Node \"" + self.name + "\" already has a child with name \"" + node.name + "\".")

    def hasChild(self, childName):
        return self.getChild(childName) is not None

    def getChild(self, childName):
        searchPredicate = lambda x: x.name == childName
        return next((x for x in self.children if searchPredicate(x)), None)


class FakeFileSystemFileNode(FakeFileSystemNode):
    """
    Represents a file in the file-system tree.
    """
    def __init__(self,name, content):
        FakeFileSystemNode.__init__(self, name)
        self.isDir = False
        self.content = content

    def addChild(self, node):
        raise Exception("Can not add sub-nodes to a filesystemaccess.FakeFileSystemFileNode.")


def _getPathAsList(path):
    # make sure path has unix format
    path = path.replace("\\", "/")
    
    # remove leading slashes at the end and beginning
    if(path.startswith("/")):
        path = path[1:]
    if(path.endswith("/")):
       path = path[:-1]

    return path.split("/")

def _getPathAsHeadAndTailList(path):

    pathList = _getPathAsList(path)
    n = len(pathList)
    tail = pathList[n-1:]
    head = pathList[:n-1]   
    
    return [head, tail[0]]

