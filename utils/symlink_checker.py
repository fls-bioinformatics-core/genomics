#!/bin/env python
#
#     symlink_checker.py: check and update symbolic links
#     Copyright (C) University of Manchester 2012-2014 Peter Briggs
#
########################################################################
#
# symlink_checker.py
#
#########################################################################

"""symlink_checker

Utility for checking and updating symbolic links.
"""

#######################################################################
# Module metadata
#######################################################################

__version__ = "1.0.0"

#######################################################################
# Import modules that this module depends on
#######################################################################

import os
import re
import logging
import optparse

#######################################################################
# Classes
#######################################################################

class Symlink:
    """Class for interrogating and modifying symbolic links

    The Symlink class provides an interface for getting information
    about a symbolic link.

    To create a new Symlink instance do e.g.:

    >>> l = Symlink('my_link.lnk')

    Information about the link can be obtained via the various
    properties:

    - target = returns the link target
    - is_absolute = reports if the target represents an absolute link
    - is_broken = reports if the target doesn't exist

    There are also methods:

    - resolve_target() = returns the normalise absolute path to the 
      target
    - update_target() = updates the target to a new location

    """
    def __init__(self,path):
        """Create a new Symlink instance

        Raises an exception if the supplied path doesn't point to
        a link instance.

        Arguments:
          path: path to the link

        """
        if not os.path.islink(path):
            raise Exception("%s is not a link" % path)
        self.__path = path
        self.__abspath = os.path.abspath(self.__path)

    @property
    def target(self):
        """Return the target of the symlink

        """
        return os.readlink(self.__abspath)

    @property
    def is_absolute(self):
        """Return True if the link target is an absolute link

        """
        return os.path.isabs(self.target)

    @property
    def is_broken(self):
        """Return True if the link target doesn't exist i.e. link is broken

        """
        return not os.path.exists(self.resolve_target())

    def resolve_target(self):
        """Return the normalised absolute path to the link target

        """
        if self.is_absolute:
            path = self.target
        else:
            path = os.path.abspath(os.path.join(os.path.dirname(self.__abspath),
                                                self.target))
        return os.path.normpath(path)

    def update_target(self,new_target):
        """Replace the current link target with new_target

        Arguments:
          new_target: path to replace the existing target with

        """
        os.unlink(self.__abspath)
        os.symlink(new_target,self.__abspath)

    def __repr__(self):
        """Implement the __repr__ built-in

        """
        return self.__path

#######################################################################
# Classes
#######################################################################

def links(dirn):
    """Traverse and return all symbolic links in under a directory

    Given a starting directory, traverses the structure underneath
    and yields the path for each symlink that is found.

    Arguments:
      dirn: name of the top-level directory

    Returns:
      Yields the name and full path for each symbolic link under 'dirn'.

    """
    for d in os.walk(dirn):
        if os.path.islink(d[0]):
            yield d[0]
        for sd in d[1]:
            path = os.path.join(d[0],sd)
            if os.path.islink(path):
                yield path
        for f in d[2]:
            path = os.path.join(d[0],f)
            if os.path.islink(path):
                yield path

#######################################################################
# Tests
#######################################################################
import unittest
import tempfile
import shutil
from mock_data import TestUtils,ExampleDirSpiders,ExampleDirLanguages

class ExampleDirLinks(ExampleDirSpiders):
    def __init__(self):
        ExampleDirSpiders.__init__(self)
    def create_directory(self):
        ExampleDirSpiders.create_directory(self)
        # Add an absolute link
        self.add_link("absolute.txt",self.path("fly.txt"))
        # Add a broken absolute link
        self.add_link("absolutely_broken.txt",self.path("absolutely_missing.txt"))
        # Add a relative link with '..'
        self.add_link("web/relative.txt","../spider.txt")
        # Add a link to a directory
        self.add_link("web2","web")

class TestSymlink(unittest.TestCase):
    """Tests for the 'Symlink' class

    """
    def setUp(self):
        """Build directory with test data

        """
        self.example_dir = ExampleDirLinks()
        self.wd = self.example_dir.create_directory()

    def tearDown(self):
        """Remove directory with test data

        """
        self.example_dir.delete_directory()

    def test_not_a_link(self):
        """Symlink raises exception if path is not a link

        """
        self.assertRaises(Exception,Symlink,self.example_dir.path("spider.txt"))

    def test_target(self):
        """Symlink.target returns correct target

        """
        self.assertEqual(Symlink(self.example_dir.path("itsy-bitsy.txt")).target,
                         "spider.txt")
        self.assertEqual(Symlink(self.example_dir.path("broken.txt")).target,
                         "missing.txt")
        self.assertEqual(Symlink(self.example_dir.path("absolute.txt")).target,
                         self.example_dir.path("fly.txt"))
        self.assertEqual(Symlink(self.example_dir.path("absolutely_broken.txt")).target,
                         self.example_dir.path("absolutely_missing.txt"))
        self.assertEqual(Symlink(self.example_dir.path("web/relative.txt")).target,
                         "../spider.txt")
        self.assertEqual(Symlink(self.example_dir.path("web2")).target,"web")

    def test_is_absolute(self):
        """Symlink.is_absolute correctly identifies absolute links

        """
        self.assertTrue(Symlink(self.example_dir.path("absolute.txt")).is_absolute)
        self.assertTrue(Symlink(self.example_dir.path("absolutely_broken.txt")).is_absolute)
        self.assertFalse(Symlink(self.example_dir.path("itsy-bitsy.txt")).is_absolute)
        self.assertFalse(Symlink(self.example_dir.path("broken.txt")).is_absolute)
        self.assertFalse(Symlink(self.example_dir.path("web/relative.txt")).is_absolute)
        self.assertFalse(Symlink(self.example_dir.path("web2")).is_absolute)

    def test_is_broken(self):
        """Symlink.is_broken correctly identifies broken links

        """
        self.assertFalse(Symlink(self.example_dir.path("absolute.txt")).is_broken)
        self.assertTrue(Symlink(self.example_dir.path("absolutely_broken.txt")).is_broken)
        self.assertFalse(Symlink(self.example_dir.path("itsy-bitsy.txt")).is_broken)
        self.assertTrue(Symlink(self.example_dir.path("broken.txt")).is_broken)
        self.assertFalse(Symlink(self.example_dir.path("web/relative.txt")).is_broken)
        self.assertFalse(Symlink(self.example_dir.path("web2")).is_broken)

    def test_resolve_target(self):
        """Symlink.resolve_target() correctly resolves full link target paths

        """
        self.assertEqual(Symlink(self.example_dir.path("itsy-bitsy.txt")).resolve_target(),
                         self.example_dir.path("spider.txt"))
        self.assertEqual(Symlink(self.example_dir.path("absolute.txt")).resolve_target(),
                         self.example_dir.path("fly.txt"))
        self.assertEqual(Symlink(self.example_dir.path("web/relative.txt")).resolve_target(),
                         self.example_dir.path("spider.txt"))
        self.assertEqual(Symlink(self.example_dir.path("web2")).resolve_target(),
                         self.example_dir.path("web"))

    def test_update_target(self):
        """Symlink.update_target() updates the link target path

        """
        symlink = Symlink(self.example_dir.path("itsy-bitsy.txt"))
        self.assertEqual(symlink.target,"spider.txt")
        symlink.update_target("spider2.txt")
        self.assertEqual(symlink.target,"spider2.txt")

class TestLinksFunction(unittest.TestCase):
    """Tests for the 'links' function

    """
    def setUp(self):
        """Build directory with test data

        """
        self.example_dir = ExampleDirLinks()
        self.wd = self.example_dir.create_directory()
        self.links = []
        for l in ("itsy-bitsy.txt",
                  "itsy-bitsy2.txt",
                  "broken.txt",
                  "broken2.txt",
                  "absolute.txt",
                  "absolutely_broken.txt",
                  "web/relative.txt",
                  "web2"):
            self.links.append(self.example_dir.path(l))

    def tearDown(self):
        """Remove directory with test data

        """
        self.example_dir.delete_directory()

    def test_links(self):
        """links function yields all symlinks

        """
        # Walk the example directory and check all yielded files
        # are in the list of links
        for l in links(self.example_dir.dirn):
            self.assertTrue(l in self.links,"%s not in link list" % l)
            self.links.remove(l)
        self.assertEqual(len(self.links),0,"Some links not found: %s" % ",".join(self.links))

#######################################################################
# Main program
#######################################################################

if __name__ == "__main__":

    # Logging
    logging.basicConfig(format="%(levelname)s: %(message)s")

    # Command line processing
    p = optparse.OptionParser(usage="%prog OPTIONS DIR",
                              version="%prog "+__version__,
                              description="Recursively check and optionally update symlinks "
                              "found under directory DIR")
    p.add_option("--absolute",action="store_true",dest="absolute",default=False,
                 help="report absolute symlinks")
    p.add_option("--broken",action="store_true",dest="broken",default=False,
                 help="report broken symlinks")
    p.add_option("--find",action="store",dest="regex_pattern",default=None,
                 help="report links where the destination matches the supplied REGEX_PATTERN")
    p.add_option("--replace",action="store",dest="new_path",default=None,
                 help="update links found by --find options, by substituting REGEX_PATTERN "
                 "with NEW_PATH")
    options,args = p.parse_args()

    # Check arguments and options
    if len(args) != 1:
        p.error("Takes a single directory as input")
    elif not os.path.isdir(args[0]):
        p.error("'%s': not a directory" % args[0])
    if options.regex_pattern is not None:
        regex = re.compile(options.regex_pattern)

    # Examine links in the directory structure
    for l in links(args[0]):
        link = Symlink(l)
        logging.debug("%s -> %s" % (link,link.target))
        if options.broken and link.is_broken:
            # Broken link
            logging.warning("Broken link:\t%s -> %s" % (link,link.target))
        elif options.absolute and link.is_absolute:
            # Absolute link
            logging.warning("Absolute link:\t%s -> %s" % (link,link.target))
        if options.regex_pattern is not None:
            # Check if target matches pattern
            if regex.search(link.target):
                print "Matched pattern:\t%s -> %s" % (link,link.target)
                if options.new_path is not None:
                    # Update target
                    new_target = regex.sub(options.new_path,link.target)
                    link.update_target(new_target)
                    print "Updated:\t%s -> %s" % (link,link.target)

                
