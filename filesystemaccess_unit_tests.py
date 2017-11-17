#!/usr/bin/python3

import unittest

from . import filesystemaccess


class TestFakeFileSystemAccess(unittest.TestCase):
                     
    def setUp(self):
        self.sut = filesystemaccess.FakeFileSystemAccess();


    def test_addfile_isfile_hasFile_exitsts(self):
        
        path = "/bla/blub"
        content = "content"

        # addfile
        self.sut.addfile(path, content)

        # isfile
        self.assertTrue(self.sut.isfile(path))
        self.assertFalse(self.sut.isfile("/bla"))
        self.assertFalse(self.sut.isfile("blib"))
        # hasfile
        self.assertTrue(self.sut.hasfile(path,content))
        self.assertFalse(self.sut.hasfile(path,"bullocks"))
        self.assertFalse(self.sut.hasfile("/bla",content))
        # exists
        self.assertTrue(self.sut.exists(path))

    
    def test_addfile_overwrites_existing_files(self):
        # Setup
        path = "/bla/blub"
        content1 = "content1"
        content2 = "content2"

        # Execute
        self.sut.addfile(path, content1)
        self.sut.addfile(path, content2)

        # Verify
        self.assertFalse(self.sut.hasfile(path,content2))


    def test_adddir_isdir(self):
        
        path = "/bla/blub"

        # addfile
        self.sut.mkdirs(path)

        # isfile
        self.assertTrue(self.sut.isdir(path))
        self.assertTrue(self.sut.isdir("/bla"))
        self.assertFalse(self.sut.isdir("blib"))

    
    def test_mkdir(self):
        
        # check adding one dir works
        validPath = "/bla"  # we have a special case there are no explicit parent dirs.
        self.sut.mkdir(validPath)
        self.sut.isdir(validPath)
        validPath = "/bla/blub"
        self.sut.mkdir(validPath)
        self.sut.isdir(validPath)
        validPath = "/bla/blub/bleb"
        self.sut.mkdir(validPath)
        self.sut.isdir(validPath)

        # check adding an existing dir throws
        self.assertRaises(Exception, self.sut.mkdir, validPath)

        # check adding multiple dirs at once does not work
        invalidPath = "/bleb/blib"
        self.assertRaises(Exception, self.sut.mkdir, invalidPath)


    def test_do_some_tests_to_verify_it_works_with_windows_path(self):

        path = "C:\\bla\\blub"

        # addfile
        self.sut.addfile(path, "content")

        # isfile
        self.assertTrue(self.sut.exists(path))


    def test_listdir_happy_case_and_uniqueness_of_node_names(self):
        #Setup
        self.sut.addfile("/bla/blub", "content")
        self.sut.addfile("/bla/blub", "content2") # add stuff twice to make sure it is only added once
        self.sut.mkdirs("/bla/bleb")
        self.sut.mkdirs("/bla/bleb")

        # Execute
        entries = self.sut.listdir("/bla")
        emptyEntries = self.sut.listdir("/bla/bleb")

        # Verify
        self.assertEqual(entries, ["blub","bleb"])
        self.assertEqual(emptyEntries, [])

    
    def test_listdir_throws_if_dir_does_not_exist_or_is_file(self):
        #Setup
        pathToNotExist = "/bla/blub"
        pathToFile = "/bla/myfile.txt"
        self.sut.addfile(pathToFile, "content")

        # Execute
        self.assertRaises(Exception, self.sut.listdir, pathToNotExist)
        self.assertRaises(Exception, self.sut.listdir, pathToFile)


    def test_rmtree_happy_case(self):
        # Setup
        self.sut.addfile("/bli/bla/blub", "content")
        self.sut.mkdirs("/bli/bla/bleb")

        # Execute
        self.sut.rmtree("/bli/bla")

        # Verify
        self.assertFalse(self.sut.exists("/bli/bla"))
        self.assertTrue(self.sut.isdir("/bli"))


    def test_rmtree_throws_for_not_existing_pathes_or_file_pathes(self):
        #Setup
        pathToNotExist = "/bla/blub"
        pathToFile = "/bla/myfile.txt"
        self.sut.addfile(pathToFile, "content")

        # Execute
        self.assertRaises(Exception, self.sut.rmtree, pathToNotExist)
        self.assertRaises(Exception, self.sut.rmtree, pathToFile)


    def test_copyfile_happy_case(self):
        #Setup
        content = "content"
        pathFrom = "/bla/myfile.txt"
        self.sut.addfile(pathFrom, content)
        self.sut.mkdirs("/bli/bleb")    # the parent directory of src must already exist
        pathTo = "/bli/bleb/copied_file.txt"

        # Execute
        self.sut.copyfile(pathFrom, pathTo)

        # Verify
        self.assertTrue(self.sut.hasfile(pathFrom,content))
        self.assertTrue(self.sut.hasfile(pathTo,content))

    def test_copyfile_overwrites_existing_files(self):
        # Setup
        contentFrom = "content from"
        pathFrom = "/bla/blub.txt"
        self.sut.addfile(pathFrom,contentFrom)
        contentTo = "content to"
        pathTo = "/bla/bib.txt"
        self.sut.addfile(pathTo,contentTo)

        # Execute
        self.sut.copyfile(pathFrom, pathTo)

        # Verify
        self.assertTrue(self.sut.hasfile(pathTo,contentFrom))


    def test_copyfile_raises_when_src_and_dst_are_same(self):
        #Setup
        pathFrom = "/bla/myfile.txt"
        self.sut.addfile(pathFrom, "content")
        # Execute
        self.assertRaises(Exception, self.sut.copyfile, pathFrom, pathFrom)


    def test_copyfile_raises_when_src_not_exist(self):
        #Setup
        pathFrom = "/bla/myfile.txt"
        self.sut.mkdirs("/bli/bleb")    # the parent directory of src must already exist
        pathTo = "/bli/bleb/copied_file.txt"
        
        # Execute
        self.assertRaises(Exception, self.sut.copyfile, pathFrom, pathTo)

    def test_copyfile_raises_when_src_is_dir(self):
        #Setup
        pathFrom = "/bla/myfile.txt"
        self.sut.mkdirs(pathFrom)
        self.sut.mkdirs("/bli/bleb")    # the parent directory of src must already exist
        pathTo = "/bli/bleb/copied_file.txt"
        
        # Execute
        self.assertRaises(Exception, self.sut.copyfile, pathFrom, pathTo)


    def test_copyfile_raises_when_parent_path_of_dst_does_not_exist(self):
        #Setup
        pathFrom = "/bla/myfile.txt"
        self.sut.mkdirs(pathFrom)
        pathTo = "/bli/bleb/copied_file.txt"
        
        # Execute
        self.assertRaises(Exception, self.sut.copyfile, pathFrom, pathTo)