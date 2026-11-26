#     mock.py: module providing mock Illumina data for testing
#     Copyright (C) University of Manchester 2012-2025 Peter Briggs
#
########################################################################

"""
mock.py

Provides data and classes for mocking up examples of outputs from
Illumina-based sequencer pipeline (e.g. GA2x or HiSeq), including example
directory structures and input and output files, to be used in testing.

These include:

- MockSampleSheet: synthesises a SampleSheet.csv
- MockIlluminaRun: synthesises the raw data output from a sequencer
- MockFastqDir: synthesises the output from CASAVA/bcl2fastq run

There are also static classes with example data:

- SampleSheets: has properties with example SampleSheet.csv files
- RunInfoXml: has static methods for making RunInfo.xml files
- RunParametersXml: has static methods for making RunParameters.xml file

There is a function for mocking the STAR aligner:

- mockSTAR: driver function for a "mock" STAR executable

The following legacy mocking classes are also provided:

- MockIlluminaData: synthesises the output from CASAVA/bcl2fastq run

"""


import os
import shutil
from ..utils.os import mkdir


#######################################################################
# Module data
#######################################################################


from .illumina import SampleSheets
from .illumina import RunInfoXml
from .illumina import RunParametersXml


#######################################################################
# Class definitions
#######################################################################


from .illumina import MockSampleSheet
from .illumina import MockRun as MockIlluminaRun
from .illumina import MockFastqDir


class MockIlluminaData(MockFastqDir):
    """Utility class for creating mock Illumina analysis data directories

    The MockIlluminaData class allows artificial Illumina analysis data
    directories to be defined, created and populated, and then destroyed.

    These artifical directories are intended to be used for testing
    purposes.

    Two styles of analysis directories can be produced: 'casava'-style
    aims to mimic that produced from the CASAVA and bcl2fastq 1.8
    processing software; 'bcl2fastq2' mimics that from the bcl2fastq
    2.* software.

    Basic example usage:

    >>> mockdata = MockIlluminaData('130904_PJB_XXXXX','casava')
    >>> mockdata.add_fastq('PJB','PJB1','PJB1_GCCAAT_L001_R1_001.fastq.gz')
    >>> ...
    >>> mockdata.create()

    This will make a CASAVA-style directory structure like:

    1130904_PJB_XXXXX/
        Unaligned/
            Project_PJB/
                Sample_PJB1/
                    PJB1_GCCAAT_L001_R1_001.fastq.gz
        ...

    Using:

    >>> mockdata = MockIlluminaData('130904_PJB_XXXXX','bcl2fastq2')
    >>> mockdata.add_fastq('PJB','PJB1','PJB1_S1_L001_R1_001.fastq.gz')

    will make a bcl2fast2-style directory structure like:

    1130904_PJB_XXXXX/
        Unaligned/
            PJB/
               PJB1_S1_L001_R1_001.fastq.gz
        ...

    NB if the sample name in the fastq file name differs from the supplied
    sample name then the sample name will be used to create an additional
    directory level, e.g.:

    >>> mockdata = MockIlluminaData('130904_PJB_XXXXX','bcl2fastq2')
    >>> mockdata.add_fastq('PJB','PJB2','PJB2_input_S1_L001_R1_001.fastq.gz')

    will create:

    1130904_PJB_XXXXX/
        Unaligned/
            PJB/
               PJB2/
                   PJB2_input_S1_L001_R1_001.fastq.gz
        ...

    (this replicates the situation for bcl2fastq v2 where Sample_ID and
    Sample_Name differ.)

    Multiple fastqs can be more easily added using e.g.:

    >>> mockdata.add_fastq_batch('PJB','PJB2','PJB1_GCCAAT',lanes=(1,4,5))

    which creates 3 fastq entries for sample PJB2, with lane numbers 1, 4
    and 5.

    Paired-end mock data can be created using the 'paired_end' flag
    when instantiating the MockIlluminaData object.

    To delete the physical directory structure when finished:

    >>> mockdata.remove()

    """
    def __init__(self,name,package,
                 unaligned_dir='Unaligned',
                 paired_end=False,
                 no_lane_splitting=False,
                 top_dir=None):
        """Create new MockIlluminaData instance

        Makes a new empty MockIlluminaData object.

        Arguments:
          name: name of the directory for the mock data
          package: name of the conversion software package to mimic (can
            be 'casava' or 'bcl2fastq2')
          unaligned_dir: directory holding the mock projects etc (default is
            'Unaligned')
          paired_end: specify whether mock data is paired end (True) or not
            (False) (default is False)
          no_lane_splitting: (bcl2fastq2 only) mimick output from bcl2fastq2
            run with --no-lane-splitting (i.e. fastq names don't contain
            lane numbers) (default is False)
          top_dir: specify a parent directory for the mock data (default is
            the current working directory)

        """
        self.__name = name
        self.__unaligned_dir = unaligned_dir
        if top_dir is not None:
            self.__top_dir = os.path.abspath(top_dir)
        else:
            self.__top_dir = os.getcwd()
        self.__created = False
        MockFastqDir.__init__(self, self.unaligned_dir, package,
                              paired_end=paired_end,
                              no_lane_splitting=no_lane_splitting)
        if package not in ('casava','bcl2fastq2'):
            raise Exception("Unknown package '%s': cannot make mock output dir"
                            % package)

    @property
    def name(self):
        """Name of the mock data

        """
        return self.__name

    @property
    def dirn(self):
        """Full path to the mock data directory

        """
        return os.path.join(self.__top_dir,self.__name)

    @property
    def unaligned_dir(self):
        """Full path to the unaligned directory for the mock data

        """
        return os.path.join(self.dirn,self.__unaligned_dir)

    def create(self,force_sample_dir=False):
        """Build and populate the directory structure

        Creates the directory structure on disk which has been defined
        within the MockIlluminaData object.

        Invoke the 'remove' method to delete the directory structure.

        The contents of the MockIlluminaData object can be modified
        after the directory structure has been created, but changes will
        not be reflected on disk. Instead it is necessary to first
        remove the directory structure, and then re-invoke the create
        method.

        create raises an OSError exception if any part of the directory
        structure already exists.

        Arguments:
          force_sample_dir (bool): if True then for bcl2fastq-style
            output, always insert a "sample" subdirectory grouping
            Fastqs for each sample, even if it wouldn't normally be
            created (default is to only add sample subdirectory if
            sample name differs from sample ID)

        """
        # Create top level directory
        if os.path.exists(self.dirn):
            raise OSError("%s already exists" % self.dirn)
        else:
            mkdir(self.dirn)
            self.__created = True
        # "Unaligned" directory
        MockFastqDir.create(self, force_sample_dir=force_sample_dir)

    def remove(self):
        """Delete the directory structure and contents

        This removes the directory structure from disk that has
        previously been created using the create method.

        """
        if self.__created:
            shutil.rmtree(self.dirn)
            self.__created = False

    def __repr__(self):
        """Implement __repr__ for debug purposes
        """
        if not self.__created:
            return ("<%s: not created>" % self.dirn)
        rep = []
        for d in os.walk(self.dirn):
            for d1 in d[1]:
                rep.append(os.path.join(d[0],d1))
            for f in d[2]:
                rep.append(os.path.join(d[0],f))
        return '\n'.join(sorted(rep))


#######################################################################
# Functions
#######################################################################

from .apps import mock_star as mockSTAR