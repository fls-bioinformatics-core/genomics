#     bcf_utils.py: utility classes and functions shared between BCF codes
#     Copyright (C) University of Manchester 2013 Peter Briggs
#
########################################################################
#
# bcf_utils.py
#
#########################################################################

__version__ = "1.0.2"

"""bcf_utils

Utility classes and functions shared between BCF codes.

Basic file system wrappers and utilities:

  mkdir
  mklink
  chmod
  format_file_size
  commonprefix
  is_gzipped_file

Sample name utilities:

  extract_initials
  extract_prefix
  extract_index_as_string
  extract_index
  pretty_print_names

File manipulations:

  concatenate_fastq_files

"""

#######################################################################
# Import modules that this module depends on
#######################################################################

import os
import logging
import string
import gzip
import shutil

#######################################################################
# Class definitions
#######################################################################

# None defined

#######################################################################
# Module Functions
#######################################################################

# File system wrappers and utilities

def mkdir(dirn,mode=None):
    """Make a directory

    Arguments:
      dirn: the path of the directory to be created
      mode: (optional) a mode specifier to be applied to the
        new directory once it has been created e.g. 0775 or 0664

    """
    logging.debug("Making %s" % dirn)
    if not os.path.isdir(dirn):
        os.mkdir(dirn)
        if mode is not None: chmod(dirn,mode)

def mklink(target,link_name,relative=False):
    """Make a symbolic link

    Arguments:
      target: the file or directory to link to
      link_name: name of the link
      relative: if True then make a relative link (if possible);
        otherwise link to the target as given (default)"""
    logging.debug("Linking to %s from %s" % (target,link_name))
    target_path = target
    if relative:
        # Try to construct relative link to target
        target_abs_path = os.path.abspath(target)
        link_abs_path = os.path.abspath(link_name)
        common_prefix = commonprefix(target_abs_path,link_abs_path)
        if common_prefix:
            # Use relpath to generate the relative path from the link
            # to the target
            target_path = os.path.relpath(target_abs_path,os.path.dirname(link_abs_path))
    os.symlink(target_path,link_name)

def chmod(target,mode):
    """Change mode of file or directory

    Arguments:
      target: file or directory to apply new mode to
      mode: a valid mode specifier e.g. 0775 or 0664
    """
    logging.debug("Changing mode of %s to %s" % (target,mode))
    if not os.path.islink(target):
        try:
            os.chmod(target,mode)
        except OSError, ex:
            logging.warning("Failed to change permissions on %s to %s: %s" % (target,mode,ex))
    else:
        logging.warning("Skipped chmod for symbolic link")

def format_file_size(fsize):
    """Format a file size from bytes to human-readable form

    Takes a file size in bytes and returns a human-readable
    string, e.g. 4.0K, 186M, 1.5G.

    Arguments:
      fsize: size in bytes

    Returns:
      Human-readable version of file size.

    """
    # Return size in human readable form
    fsize = float(fsize)/1024
    units = 'K'
    if fsize > 1024:
        fsize = fsize/1024
        units = 'M'
        if fsize > 1024:
            fsize = fsize/1024
            units = 'G'
    return "%.1f%s" % (fsize,units)
            
def commonprefix(path1,path2):
    """Determine common prefix path for path1 and path2

    Use this in preference to os.path.commonprefix as the version
    in os.path compares the two paths in a character-wise fashion
    and so can give counter-intuitive matches; this version compares
    path components which seems more sensible.

    For example: for two paths /mnt/dir1/file and /mnt/dir2/file,
    os.path.commonprefix will return /mnt/dir, whereas this function
    will return /mnt.

    Arguments:
      path1: first path in comparison
      path2: second path in comparison

    Returns:
      Leading part of path which is common to both input paths.
    """
    path1_components = str(path1).split(os.sep)
    path2_components = str(path2).split(os.sep)
    common_components = []
    ncomponents = min(len(path1_components),len(path2_components))
    for i in range(ncomponents):
        if path1_components[i] == path2_components[i]:
            common_components.append(path1_components[i])
        else:
            break
    commonprefix = "%s" % os.sep.join(common_components)
    return commonprefix

def is_gzipped_file(filename):
    """Check if a file has a .gz extension

    Arguments:
      filename: name of the file to be tested (can include leading path)

    Returns:
      True if filename has trailing .gz extension, False if not.

    """
    return os.path.splitext(filename)[1] == '.gz'

# Sample/library name utilities

def extract_initials(name):
    """Return leading initials from the library or sample name

    Conventionaly the experimenter's initials are the leading characters
    of the name e.g. 'DR' for 'DR1', 'EP' for 'EP_NCYC2669', 'CW' for
    'CW_TI' etc

    Arguments:
      name: the name of a sample or library

    Returns:
      The leading initials from the name.
    """
    initials = []
    for c in str(name):
        if c.isalpha():
            initials.append(c)
        else:
            break
    return ''.join(initials)
        
def extract_prefix(name):
    """Return the library or sample name prefix

    Arguments:
      name: the name of a sample or library

    Returns:
      The prefix consisting of the name with trailing numbers
      removed, e.g. 'LD_C' for 'LD_C1'
    """
    return str(name).rstrip(string.digits)

def extract_index_as_string(name):
    """Return the library or sample name index as a string

    Arguments:
      name: the name of a sample or library

    Returns:
      The index, consisting of the trailing numbers from the name. It is
      returned as a string to preserve leading zeroes, e.g. '1' for
      'LD_C1', '07' for 'DR07' etc
    """
    index = []
    chars = [c for c in str(name)]
    chars.reverse()
    for c in chars:
        if c.isdigit():
            index.append(c)
        else:
            break
    index.reverse()
    return ''.join(index)

def extract_index(name):
    """Return the library or sample name index as an integer

    Arguments:
      name: the name of a sample or library

    Returns:
      The index as an integer, or None if the index cannot be converted to
      integer format.
    """
    indx = extract_index_as_string(name)
    if indx == '':
        return None
    else:
        return int(indx)

def pretty_print_names(name_list):
    """Given a list of library or sample names, format for pretty printing.

    Arguments:
      name_list: a list or tuple of library or sample names

    Returns:
      String with a condensed description of the library
      names, for example:

      ['DR1', 'DR2', 'DR3', DR4'] -> 'DR1-4'
    """
    # Create a list of string-type names sorted into prefix and index order
    names = [str(x) for x in sorted(name_list,
                                    key=lambda n: (extract_prefix(n),extract_index(n)))]
    # Go through and group
    groups = []
    group = []
    last_index = None
    for name in names:
        # Check if this is next in sequence
        try:
            if extract_index(name) == last_index+1:
                # Next in sequence
                group.append(name)
                last_index = extract_index(name)
                continue
        except TypeError:
            # One or both of the indexes was None
            pass
        # Current name is not next in previous sequence
        # Tidy up and start new group
        if group:
            groups.append(group)
        group = [name]
        last_index = extract_index(name)
    # Capture last group
    if group:
        groups.append(group)
    # Pretty print
    out = []
    for group in groups:
        if len(group) == 1:
            # "group" of one
            out.append(group[0])
        else:
            # Group with at least two members
            out.append(group[0]+"-"+extract_index_as_string(group[-1]))
    # Concatenate and return
    return ', '.join(out)

# File manipulations

def concatenate_fastq_files(merged_fastq,fastq_files,bufsize=10240,
                            overwrite=False,verbose=True):
    """Create a single FASTQ file by concatenating one or more FASTQs

    Given a list or tuple of FASTQ files (which can be compressed or
    uncompressed or a combination), creates a single output FASTQ by
    concatenating the contents.

    Arguments:
      merged_fastq: name of output FASTQ file (mustn't exist beforehand)
      fastq_files:  list of FASTQ files to concatenate
      bufsize: (optional) size of buffer to use for copying data
      overwrite: (optional) if True then overwrite the output file if it
        already exists (otherwise raise OSError); default is False
      verbose: (optional) if True then report operations to stdout,
        otherwise operate quietly

    """
    if verbose: print "Creating merged fastq file '%s'" % merged_fastq
    # Check that initial file doesn't exist
    if os.path.exists(merged_fastq) and not overwrite:
        raise OSError, "Target file '%s' already exists, stopping" % merged_fastq
    # Create temporary name
    merged_fastq_part = merged_fastq+'.part'
    # Open for writing
    if is_gzipped_file(merged_fastq):
        if is_gzipped_file(fastq_files[0]):
            # Copy first file in list directly and open for append
            if verbose: print "Copying %s" % fastq_files[0]
            shutil.copy(fastq_files[0],merged_fastq_part)
            first_file = 1
            fq_merged = gzip.GzipFile(merged_fastq_part,'ab')
        else:
            # Open for write
            first_file = 0
            fq_merged = gzip.GzipFile(merged_fastq_part,'wb')
    else:
        if not is_gzipped_file(fastq_files[0]):
            if verbose: print "Copying %s" % fastq_files[0]
            # Copy first file in list directly and open for append
            shutil.copy(fastq_files[0],merged_fastq_part)
            first_file = 1
            fq_merged = open(merged_fastq_part,'ab')
        else:
            # Assume regular file
            first_file = 1
            fq_merged = open(merged_fastq_part,'wb')
    # For each fastq, read data and append to output - simples!
    for fastq in fastq_files[first_file:]:
        if verbose: print "Adding records from %s" % fastq
        # Check it exists
        if not os.path.exists(fastq):
            raise OSError, "'%s' not found, stopping" % fastq
        # Open file for reading
        if not is_gzipped_file(fastq):
            fq = open(fastq,'rb')
        else:
            fq = gzip.GzipFile(fastq,'rb')
        # Read and append data
        while True:
            data = fq.read(10240)
            if not data: break
            fq_merged.write(data)
        fq.close()
    # Finished, clean up
    fq_merged.close()
    os.rename(merged_fastq_part,merged_fastq)

#######################################################################
# Tests
#######################################################################
import unittest

class TestFileSystemFunctions(unittest.TestCase):
    """Unit tests for file system wrapper and utility functions

    """

    def test_commonprefix(self):
        self.assertEqual('/mnt/stuff',commonprefix('/mnt/stuff/dir1',
                                                   '/mnt/stuff/dir2'))
        self.assertEqual('',commonprefix('/mnt1/stuff/dir1',
                                         '/mnt2/stuff/dir2'))

    def test_is_gzipped_file(self):
        self.assertTrue(is_gzipped_file('hello.gz'))
        self.assertTrue(is_gzipped_file('hello.tar.gz'))
        self.assertFalse(is_gzipped_file('hello'))
        self.assertFalse(is_gzipped_file('hello.txt'))
        self.assertFalse(is_gzipped_file('hello.gz.part'))
        self.assertFalse(is_gzipped_file('hellogz'))

class TestFormatFileSize(unittest.TestCase):
    """Unit tests for formatting file sizes

    """

    def test_bytes_to_kb(self):
        self.assertEqual("0.9K",format_file_size(900))
        self.assertEqual("4.0K",format_file_size(4096))

    def test_bytes_to_mb(self):
        self.assertEqual("186.0M",format_file_size(195035136))

    def test_bytes_to_gb(self):
        self.assertEqual("1.6G",format_file_size(1717986919))

class TestNameFunctions(unittest.TestCase):
    """Unit tests for name handling utility functions

    """

    def test_extract_initials(self):
        self.assertEqual('DR',extract_initials('DR1'))
        self.assertEqual('EP',extract_initials('EP_NCYC2669'))
        self.assertEqual('CW',extract_initials('CW_TI'))

    def test_extract_prefix(self):
        self.assertEqual('LD_C',extract_prefix('LD_C1'))

    def test_extract_index_as_string(self):
        self.assertEqual('1',extract_index_as_string('LD_C1'))
        self.assertEqual('07',extract_index_as_string('DR07'))
        self.assertEqual('',extract_index_as_string('DROHSEVEN'))

    def test_extract_index(self):
        self.assertEqual(1,extract_index('LD_C1'))
        self.assertEqual(7,extract_index('DR07'))
        self.assertEqual(None,extract_index('DROHSEVEN'))
        self.assertEqual(0,extract_index('HUES1A0'))

    def test_pretty_print_names(self):
        self.assertEqual('JC_SEQ26-29',pretty_print_names(('JC_SEQ26',
                                                           'JC_SEQ27',
                                                           'JC_SEQ28',
                                                           'JC_SEQ29')))
        self.assertEqual('JC_SEQ26',pretty_print_names(('JC_SEQ26',)))
        self.assertEqual('JC_SEQ26, JC_SEQ28-29',pretty_print_names(('JC_SEQ26',
                                                           'JC_SEQ28',
                                                           'JC_SEQ29')))
        self.assertEqual('JC_SEQ26, JC_SEQ28, JC_SEQ30',pretty_print_names(('JC_SEQ26',
                                                           'JC_SEQ28',
                                                           'JC_SEQ30')))

class TestConcatenateFastqFiles(unittest.TestCase):
    """Unit tests for concatenate_fastq_files

    """
    def setUp(self):
        # Create a set of test files
        self.fastq_data1 = """"@73D9FA:3:FC:1:1:7507:1000 1:N:0:
NACAACCTGATTAGCGGCGTTGACAGATGTATCCAT
+
#))))55445@@@@@C@@@@@@@@@:::::<<:::<
@73D9FA:3:FC:1:1:15740:1000 1:N:0:
NTCTTGCTGGTGGCGCCATGTCTAAATTGTTTGGAG
+
#+.))/0200<<<<<:::::CC@@C@CC@@@22@@@
@73D9FA:3:FC:1:1:8103:1000 1:N:0:
NGACCGATTAGAGGCGTTTTATGATAATCCCAATGC
+
#(,((,)*))/.0--2255282299@@@@@@@@@@@
"""
        self.fastq_data2 = """@73D9FA:3:FC:1:1:7488:1000 1:N:0:
NTGATTGTCCAGTTGCATTTTAGTAAGCTCTTTTTG
+
#,,,,33223CC@@@@@@@C@@@@@@@@C@CC@222
@73D9FA:3:FC:1:1:6680:1000 1:N:0:
NATAAATCACCTCACTTAAGTGGCTGGAGACAAATA
+
#--,,55777@@@@@@@CC@@C@@@@@@@@:::::<
"""

    def tearDown(self):
        os.remove(self.fastq1)
        os.remove(self.fastq2)
        os.remove(self.merged_fastq)

    def make_fastq_file(self,fastq,data):
        # Create a fastq file for the testing
        if os.path.splitext(fastq)[1] != '.gz':
            open(fastq,'wt').write(data)
        else:
            gzip.GzipFile(fastq,'wt').write(data)

    def test_concatenate_fastq_files(self):
        self.fastq1 = "concat.unittest.1.fastq"
        self.fastq2 = "concat.unittest.2.fastq"
        self.make_fastq_file(self.fastq1,self.fastq_data1)
        self.make_fastq_file(self.fastq2,self.fastq_data2)
        self.merged_fastq = "concat.unittest.merged.fastq"
        concatenate_fastq_files(self.merged_fastq,
                                [self.fastq1,self.fastq2],
                                overwrite=True,
                                verbose=False)
        merged_fastq_data = open(self.merged_fastq,'r').read()
        self.assertEqual(merged_fastq_data,self.fastq_data1+self.fastq_data2)

    def test_concatenate_fastq_files_gzipped(self):
        self.fastq1 = "concat.unittest.1.fastq.gz"
        self.fastq2 = "concat.unittest.2.fastq.gz"
        self.make_fastq_file(self.fastq1,self.fastq_data1)
        self.make_fastq_file(self.fastq2,self.fastq_data2)
        self.merged_fastq = "concat.unittest.merged.fastq.gz"
        concatenate_fastq_files(self.merged_fastq,
                                [self.fastq1,self.fastq2],
                                overwrite=True,
                                verbose=False)
        merged_fastq_data = gzip.GzipFile(self.merged_fastq,'r').read()
        self.assertEqual(merged_fastq_data,self.fastq_data1+self.fastq_data2)

#######################################################################
# Main program
#######################################################################

if __name__ == "__main__":
    # Turn off most logging output for tests
    logging.getLogger().setLevel(logging.CRITICAL)
    # Run tests
    unittest.main()
