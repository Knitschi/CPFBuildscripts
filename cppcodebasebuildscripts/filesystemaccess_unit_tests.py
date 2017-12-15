#!/usr/bin/python3

import unittest

from . import filesystemaccess


class TestFakeFileSystemAccess(unittest.TestCase):
    """
    Fixture class for testing the FakeFileSystemAccess class.
    """
    def setUp(self):
        self.sut = filesystemaccess.FakeFileSystemAccess()


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
        self.assertTrue(self.sut.hasfile(path, content))
        self.assertFalse(self.sut.hasfile(path, "bullocks"))
        self.assertFalse(self.sut.hasfile("/bla", content))
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
        valid_path = "/bla"  # we have a special case there are no explicit parent dirs.
        self.sut.mkdir(valid_path)
        self.sut.isdir(valid_path)
        valid_path = "/bla/blub"
        self.sut.mkdir(valid_path)
        self.sut.isdir(valid_path)
        valid_path = "/bla/blub/bleb"
        self.sut.mkdir(valid_path)
        self.sut.isdir(valid_path)

        # check adding an existing dir throws
        self.assertRaises(Exception, self.sut.mkdir, valid_path)

        # check adding multiple dirs at once does not work
        invalid_path = "/bleb/blib"
        self.assertRaises(Exception, self.sut.mkdir, invalid_path)


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
        empty_entries = self.sut.listdir("/bla/bleb")

        # Verify
        self.assertEqual(entries, ["blub","bleb"])
        self.assertEqual(empty_entries, [])

    
    def test_listdir_throws_if_dir_does_not_exist_or_is_file(self):
        #Setup
        path_to_not_exist = "/bla/blub"
        path_to_file = "/bla/myfile.txt"
        self.sut.addfile(path_to_file, "content")

        # Execute
        self.assertRaises(Exception, self.sut.listdir, path_to_not_exist)
        self.assertRaises(Exception, self.sut.listdir, path_to_file)


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
        path_to_not_exist = "/bla/blub"
        path_to_file = "/bla/myfile.txt"
        self.sut.addfile(path_to_file, "content")

        # Execute
        self.assertRaises(Exception, self.sut.rmtree, path_to_not_exist)
        self.assertRaises(Exception, self.sut.rmtree, path_to_file)


    def test_copyfile_happy_case(self):
        #Setup
        content = "content"
        path_from = "/bla/myfile.txt"
        self.sut.addfile(path_from, content)
        self.sut.mkdirs("/bli/bleb")    # the parent directory of src must already exist
        path_to = "/bli/bleb/copied_file.txt"

        # Execute
        self.sut.copyfile(path_from, path_to)

        # Verify
        self.assertTrue(self.sut.hasfile(path_from,content))
        self.assertTrue(self.sut.hasfile(path_to,content))

    def test_copyfile_overwrites_existing_files(self):
        # Setup
        content_from = "content from"
        path_from = "/bla/blub.txt"
        self.sut.addfile(path_from, content_from)
        content_to = "content to"
        path_to = "/bla/bib.txt"
        self.sut.addfile(path_to, content_to)

        # Execute
        self.sut.copyfile(path_from, path_to)

        # Verify
        self.assertTrue(self.sut.hasfile(path_to, content_from))


    def test_copyfile_raises_when_src_and_dst_are_same(self):
        #Setup
        path_from = "/bla/myfile.txt"
        self.sut.addfile(path_from, "content")
        # Execute
        self.assertRaises(Exception, self.sut.copyfile, path_from, path_from)


    def test_copyfile_raises_when_src_not_exist(self):
        #Setup
        path_from = "/bla/myfile.txt"
        self.sut.mkdirs("/bli/bleb")    # the parent directory of src must already exist
        path_to = "/bli/bleb/copied_file.txt"

        # Execute
        self.assertRaises(Exception, self.sut.copyfile, path_from, path_to)

    def test_copyfile_raises_when_src_is_dir(self):
        #Setup
        path_from = "/bla/myfile.txt"
        self.sut.mkdirs(path_from)
        self.sut.mkdirs("/bli/bleb")    # the parent directory of src must already exist
        path_to = "/bli/bleb/copied_file.txt"

        # Execute
        self.assertRaises(Exception, self.sut.copyfile, path_from, path_to)


    def test_copyfile_raises_when_parent_path_of_dst_does_not_exist(self):
        #Setup
        path_from = "/bla/myfile.txt"
        self.sut.mkdirs(path_from)
        path_to = "/bli/bleb/copied_file.txt"

        # Execute
        self.assertRaises(Exception, self.sut.copyfile, path_from, path_to)
