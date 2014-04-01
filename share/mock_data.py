#!/usr/bin/env python
#
#     mock_data.py: utility classes and functions for generating test data
#     Copyright (C) University of Manchester 2014 Peter Briggs
#
########################################################################
#
# mock_utils.py
#
#########################################################################

"""mock_utils

Utility classes and functions for generating test data and directory
structures, intended to be used in unit tests.

* TestUtils provides a set of class methods for creating arbitrary files,
  directories and symlinks.

* BaseExampleDir can be used as a base class for building and interrogating
  disposable example directories.

* ExampleDirScooby, ExampleDirSpiders and ExampleDirLanguages are
  classes that can be used to make instant test directory structures of
  varying complexity.


"""

#######################################################################
# Import modules that this module depends on
#######################################################################

import os
import tempfile
import shutil
import copy
import Md5sum
import bcf_utils

#######################################################################
# Modules constants
#######################################################################

class TestUtils:
    """Utilities to help with setting up/running tests etc

    """
    @classmethod
    def make_file(self,filename,text,basedir=None):
        """Create test file
        
        """
        if filename is None:
            # mkstemp returns a tuple
            tmpfile = tempfile.mkstemp(dir=basedir,text=True)
            filename = tmpfile[1]
        elif basedir is not None:
            filename = os.path.join(basedir,filename)
        fp = open(filename,'w')
        fp.write(text)
        fp.close()
        return filename

    @classmethod
    def make_dir(self,dirname=None):
        """Create test directory
        
        """
        if dirname is None:
            dirname = tempfile.mkdtemp()
        else:
            os.mkdir(dirname)
        return dirname

    @classmethod
    def make_sub_dir(self,basedir,dirname):
        """Create a subdirectory in an existing directory
        
        """
        subdir = os.path.join(basedir,dirname)
        if not os.path.exists(subdir):
            os.makedirs(subdir)
        return subdir

    @classmethod
    def make_sym_link(self,target,link_name=None,basedir=None):
        """Create a symbolic link

        """
        if link_name is None:
            link_name = os.path.basename(target)
        if basedir is not None:
            link_name = os.path.join(basedir,link_name)
        os.symlink(target,link_name)
        return link_name

# Base class for making test data directories
class BaseExampleDir:
    """Base class for making test data directories

    Create, populate and destroy directory with test data.

    Typically you should subclass the BaseExampleDir and then
    use method calls to add files, links and directories. For
    example:

    >>> class MyExampleDir(BaseExampleDir):
    >>>    def __init__(self):
    >>>       BaseExampleDir.__init__(self)
    >>>       self.add_file("Test","This is a test file")
    >>>

    Then to use in a program or unit test method:

    >>> d = MyExampleDir()
    >>> d.create_directory()
    >>> # do stuff
    >>> d.delete_directory()

    There are also methods to get information about the directory
    structure, for example:

    >>> files = d.filelist() # List all files and links, return full paths

    Paths are implicitly relative to the base directory, which
    is a temporary directory created automatically when the
    'create_directory' method is invoked.

    """

    def __init__(self):
        self.dirn = None
        self.files = []
        self.content = {}
        self.links = []
        self.targets = {}
        self.dirs = []

    def add_dir(self,path):
        if path not in self.dirs:
            self.dirs.append(path)
            if self.dirn is not None:
                TestUtils.make_sub_dir(self.dirn,path)

    def add_file(self,path,content=''):
        self.files.append(path)
        self.content[path] = content
        self.add_dir(os.path.dirname(path))
        if self.dirn is not None:
            TestUtils.make_file(path,self.content[path],basedir=self.dirn)

    def add_link(self,path,target=None):
        self.links.append(path)
        self.targets[path] = target
        self.add_dir(os.path.dirname(path))
        if self.dirn is not None:
            TestUtils.make_sym_link(self.targets[path],path,basedir=self.dirn)

    def path(self,filen):
        if self.dirn is not None:
            return os.path.join(self.dirn,filen)
        else:
            return filen

    def filelist(self,include_links=True,full_path=True):
        filelist = copy.copy(self.files)
        if include_links:
            for link in self.links:
                resolved_link = os.path.join(os.path.dirname(self.path(link)),
                                             os.readlink(self.path(link)))
                if not os.path.isdir(resolved_link):
                    filelist.append(link)
        filelist.sort()
        if full_path:
            filelist = [self.path(x) for x in filelist]
        return filelist

    def create_directory(self):
        self.dirn = TestUtils.make_dir()
        for d in self.dirs:
            TestUtils.make_sub_dir(self.dirn,d)
        for f in self.files:
            TestUtils.make_file(f,self.content[f],basedir=self.dirn)
        for l in self.links:
            TestUtils.make_sym_link(self.targets[l],l,basedir=self.dirn)
        return self.dirn

    def delete_directory(self):
        if self.dirn is not None:
            shutil.rmtree(self.dirn)
            self.dirn = None

    def checksum_for_file(self,path):
        """
        """
        return Md5sum.md5sum(self.path(path))

class ExampleDirScooby(BaseExampleDir):
    """Small test data directory with files and subdirectories

    """
    def __init__(self):
        BaseExampleDir.__init__(self)
        self.add_file("test.txt","This is a test file")
        self.add_file("fred/test.txt","This is another test file")
        self.add_file("daphne/test.txt","This is another test file")
        self.add_file("thelma/test.txt","This is another test file")
        self.add_file("shaggy/test.txt","This is another test file")
        self.add_file("scooby/test.txt","This is another test file")

class ExampleDirSpiders(BaseExampleDir):
    """Small test data directory with files and links

    """
    def __init__(self):
        BaseExampleDir.__init__(self)
        # Files
        self.add_file("spider.txt","The itsy-bitsy spider\nClimbed up the chimney spout")
        self.add_file("spider2.txt","The itsy-bitsy spider\nClimbed up the chimney spout")
        self.add_file("fly.txt","'Come into my parlour'\nSaid the spider to the fly")
        # Symbolic links
        self.add_link("itsy-bitsy.txt","spider.txt")
        self.add_link("itsy-bitsy2.txt","spider2.txt")
        # Broken links
        self.add_link("broken.txt","missing.txt")
        self.add_link("broken2.txt","missing.txt")

class ExampleDirLanguages(BaseExampleDir):
    """Test data directory with more complicated structure and linking

    """
    def __init__(self):
        BaseExampleDir.__init__(self)
        # Files
        self.add_file("hello","Hello!")
        self.add_file("goodbye","Goodbye!")
        self.add_file("spanish/hola","Hello!")
        self.add_file("spanish/adios","Goodbye!")
        self.add_file("welsh/north_wales/maen_ddrwg_gen_i","Sorry!")
        self.add_file("welsh/south_wales/maen_flin_da_fi","Sorry!")
        self.add_file("icelandic/takk_fyrir","Thank you!")
        # Symbolic links
        self.add_link("hi","hello")
        self.add_link("bye","goodbye")
        self.add_dir("countries")
        self.add_link("countries/spain","../spanish")
        self.add_link("countries/north_wales","../welsh/north_wales")
        self.add_link("countries/south_wales","../welsh/south_wales")
        self.add_link("countries/iceland","../icelandic")
