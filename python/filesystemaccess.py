#!/usr/bin/python3

import os
import shutil
import stat
import platform


class FileSystemAccess:
    """
    This class wraps the accesses to the file-system to
    allow the usage of a fake file-system for tests.
    """

    def exists(self, path):
        """Returns true if the path exists."""
        return os.path.exists(str(path))

    def isfile(self, path):
        """Returns true if the path leads to a file."""
        return os.path.isfile(path)

    def isdir(self, path):
        """Returns true if the path leads to a directory."""
        return os.path.isdir(path)

    def mkdir(self, path):
        """Creates a directory. The parent directory must exist."""
        return os.mkdir(path)

    def mkdirs(self, path):
        """
        Creates multiple directories. This will not throw an error if a directory already exists.
        """
        return os.makedirs(path, 0o777, True)

    def listdir(self, path):
        """
        Returns all entries in the directory given by path except . and .. .
        Throws when path does not exist?
        """
        return os.listdir(path)

    def rmtree(self, path):
        """
        Removes a directory and all of its content.
        We use our own implementation because
        shutil.rmtree() fails when files are write
        protected on windows.
        """
        system = platform.system()
        if system == 'Windows':
            for root, dirs, files in os.walk(str(path), topdown=False):
                for name in files:
                    filename = os.path.join(root, name)
                    os.chmod(filename, stat.S_IWUSR)
                    os.remove(filename)
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
            os.rmdir(str(path))
        elif system == 'Linux':
            shutil.rmtree(str(path))
        else:
            raise Exception('Unknown OS')


    def copyfile(self, path_from, path_to):
        """Copies a file."""
        shutil.copyfile(path_from, path_to)


    def touch_file(self, file_path):
        """Updates the time stamp of a file and creates it if it does not exists."""
        file_string = str(file_path)
        with open(file_string, 'a'):
            os.utime(file_string, None)


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
        return self._get_deep_subnode_with_path(path) is not None

    def isfile(self, path):
        node = self._get_deep_subnode_with_path(path)
        if node is not None:
            return not node.is_dir
        return False

    def isdir(self, path):
        node = self._get_deep_subnode_with_path(path)
        if node is not None:
            return node.is_dir
        return False

    def listdir(self, path):
        node = self._get_deep_subnode_with_path(path)
        if node is not None and node.is_dir:
            return [x.name for x in node.children]
        raise Exception('Path "' + path + '" does not exist or is not a directory.')

    def rmtree(self, path):
        # check if path is valid
        if not self.isdir(path):
            raise Exception("The path \"" + path + "\" given to rmtree() does not lead to a directory.")

        paren_dirs, top_dir = _get_path_as_head_and_tail_list(path)
        parent_node = self._get_deep_subnode(paren_dirs)
        parent_node.children = [x for x in parent_node.children if x.name != top_dir]    # filter out the directory.
        return

    def copyfile(self, path_from, path_to):
        if path_from == path_to:
            raise Exception("Can not use the same source and destination path (\"" + path_from + "\") in filesystemaccess.copyfile()")
        # get fileFrom node
        file_node_from = self._get_deep_subnode_with_path(path_from)

        if file_node_from is None:
            raise Exception("Source file \"" + path_from + "\" does not exist in filesystemaccess.copyfile()")

        if file_node_from.is_dir:
            raise Exception("Source \"" + path_from + "\" is a path to a directory but must be a path to a file in filesystemaccess.copyfile()")

        # get dirTo node
        dirs_to, filename_to = _get_path_as_head_and_tail_list(path_to)
        dir_to_node = self._get_deep_subnode(dirs_to)
        if dir_to_node is None:
            raise Exception("The destination directory for file \"" + path_to + "\" does not exist in filesystemaccess.copyfile()")        
        # copy file 
        file_to_node = dir_to_node.get_child(filename_to)
        if file_to_node is not None:  # overwrite existing one
            file_to_node.content = file_node_from.content
        else:   # create new
            dir_to_node.add_child(FakeFileSystemFileNode(filename_to, file_node_from.content))
        return

    #------------------------------------------------------------

    def hasfile(self, path, content):
        file_node = self._get_deep_subnode_with_path(path)
        if file_node is None or file_node.is_dir or file_node.content != content:
            return False
        return True

    def addfile(self, path, content):
        dirs, filename = _get_path_as_head_and_tail_list(path)
        node = self._create_directory_nodes(dirs)
        if not node.has_child(filename):
            node.add_child(FakeFileSystemFileNode(filename, content))

    def mkdir(self, path):
        """
        Unlike mkdirs this behaves more like os.mkdir() which only can create one dir at a time.
        But path must be absolute.
        """
        subdirs = _get_path_as_head_and_tail_list(path)[0]
        if subdirs and self._get_deep_subnode(subdirs) is None:
            raise Exception("FakeFileSystemAccess.mkdir(): The parent directory of the created directory \"" + path + "\" must exist.")

        if self.exists(path):
            raise Exception("FakeFileSystemAccess.mkdir(): Path \"" + path + "\" points to an existing file or directory.")

        self.mkdirs(path)

    def mkdirs(self, path):
        dirs = _get_path_as_list(path)
        self._create_directory_nodes(dirs)

    def _get_deep_subnode(self, node_list):
        node = self.root
        for node_name in node_list:
            if node.has_child(node_name):
                node = node.get_child(node_name)
            else:
                return None
        return node

    def _get_deep_subnode_with_path(self, path):
        nodes = _get_path_as_list(path)
        return self._get_deep_subnode(nodes)

    def _create_directory_nodes(self, node_name_list):
        # create or get the directory nodes
        node = self.root
        for dir_name in node_name_list:
            child = node.get_child(dir_name)
            if child is None:
                new_node = FakeFileSystemNode(dir_name)
                node.add_child(new_node)
                node = new_node
            else:
                node = child
        return node



class FakeFileSystemNode:
    """
    Represents a directory in the file-system tree.
    """
    def __init__(self, name):
        self.name = name
        self.is_dir = True
        self.children = []

    def add_child(self, node):
        if not self.has_child(node.name):
            self.children.append(node)
        else:
            raise Exception("Node \"" + self.name + "\" already has a child with name \"" + node.name + "\".")

    def has_child(self, child_name):
        return self.get_child(child_name) is not None

    def get_child(self, child_name):
        searchpredicate = lambda x: x.name == child_name
        return next((x for x in self.children if searchpredicate(x)), None)


class FakeFileSystemFileNode(FakeFileSystemNode):
    """
    Represents a file in the file-system tree.
    """
    def __init__(self, name, content):
        FakeFileSystemNode.__init__(self, name)
        self.is_dir = False
        self.content = content

    def add_child(self, node):
        raise Exception("Can not add sub-nodes to a filesystemaccess.FakeFileSystemFileNode.")


def _get_path_as_list(path):
    # make sure path has unix format
    path = str(path).replace("\\", "/")

    # remove leading slashes at the end and beginning
    if path.startswith("/"):
        path = path[1:]
    if path.endswith("/"):
        path = path[:-1]

    return path.split("/")

def _get_path_as_head_and_tail_list(path):

    path_list = _get_path_as_list(path)
    n = len(path_list)
    tail = path_list[n-1:]
    head = path_list[:n-1]

    return [head, tail[0]]
