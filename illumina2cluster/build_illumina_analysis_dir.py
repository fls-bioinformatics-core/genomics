#!/bin/env python
#
#     build_illumina_analysis_dir.py: build analysis dir with links to fastq files
#     Copyright (C) University of Manchester 2012 Peter Briggs
#
"""build_illumina_analysis_dir.py

Query and build per-project analysis directories for post-bcl-to-fastq
data from Illumina GA2 sequencer.

--list prints information about the projects and samples.

Otherwise analysis directories are created for each project and populated
with links to the fastq.gz files for the samples.

Use --dry-run to see what will be done before actually doing it.

Use --expt=... option to set application types for each project.

"""

#######################################################################
# Import modules
#######################################################################

import os
import sys
import optparse
import logging

class IlluminaData:
    """Class for examining Illumina data post bcl-to-fastq conversion

    Provides the following attributes:

    analysis_dir:  top-level directory holding the 'Unaligned' subdirectory
                   with the primary fastq.gz files
    projects:      list of IlluminaProject objects (one for each project
                   defined at the fastq creation stage, expected to be in
                   subdirectories "Project_...")
    unaligned_dir: full path to the 'Unaligned' directory holding the
                   primary fastq.gz files

    Provides the following methods:

    get_project(): lookup and return an IlluminaProject object corresponding
                   to the supplied project name

    """

    def __init__(self,illumina_analysis_dir,unaligned_dir="Unaligned"):
        """Create and populate a new IlluminaData object

        Arguments:
          illumina_analysis_dir: path to the analysis directory holding
            the fastq files (expected to be in a subdirectory called
            'Unaligned').
          unaligned_dir: (optional) alternative name for the subdirectory
            under illumina_analysis_dir holding the fastq files

        """
        self.analysis_dir = os.path.abspath(illumina_analysis_dir)
        self.projects = []
        # Look for "unaligned" data directory
        self.unaligned_dir = os.path.join(illumina_analysis_dir,unaligned_dir)
        if not os.path.exists(self.unaligned_dir):
            raise IlluminaDataError, "Missing data directory %s" % self.unaligned_dir
        # Look for projects
        for f in os.listdir(self.unaligned_dir):
            dirn = os.path.join(self.unaligned_dir,f)
            if f.startswith("Project_") and os.path.isdir(dirn):
                logging.debug("Project dirn: %s" % f)
                self.projects.append(IlluminaProject(dirn))
        # Raise an exception if no projects found
        if not self.projects:
            raise IlluminaDataError, "No projects found"
        # Sort projects on name
        self.projects.sort(lambda a,b: cmp(a.name,b.name))

    def get_project(self,name):
        """Return project that matches 'name'

        Arguments:
          name: name of a project

        Returns:
          IlluminaProject object with the matching name; raises
          'IlluminaDataError' exception if no match is found.

        """
        for project in self.projects:
            if project.name == name: return project
        raise IlluminaDataError, "No matching project for '%s'" % name

class IlluminaProject:
    """Class for storing information on a 'project' within an Illumina run

    A project is a subset of fastq files from a run of the Illumina GA2
    sequencer; in the first instance projects are defined within the
    SampleSheet.csv file which is output by the sequencer.

    Provides the following attributes:

    name:      name of the project
    dirn:      (full) path of the directory for the project
    expt_type: the application type for the project e.g. RNA-seq, ChIP-seq
               Initially set to None; should be explicitly set by the
               calling subprogram
    samples:   list of IlluminaSample objects for each sample within the
               project

    """

    def __init__(self,dirn):
        """Create and populate a new IlluminaProject object

        Arguments:
          dirn: path to the directory holding the samples within the
                project (expected to be in subdirectories "Sample_...")
        """
        self.dirn = dirn
        self.expt_type = None
        self.samples = []
        # Get name by removing prefix
        self.project_prefix = "Project_"
        if not os.path.basename(self.dirn).startswith(self.project_prefix):
            raise IlluminaDataError, "Bad project name '%s'" % self.dirn
        self.name = os.path.basename(self.dirn)[len(self.project_prefix):]
        logging.debug("Project name: %s" % self.name)
        # Look for samples
        self.sample_prefix = "Sample_"
        for f in os.listdir(self.dirn):
            sample_dirn = os.path.join(self.dirn,f)
            if f.startswith(self.sample_prefix) and os.path.isdir(sample_dirn):
                self.samples.append(IlluminaSample(sample_dirn))
        # Raise an exception if no samples found
        if not self.samples:
            raise IlluminaDataError, "No samples found for project %s" % \
                project.name
        # Sort samples on name
        self.samples.sort(lambda a,b: cmp(a.name,b.name))

class IlluminaSample:
    """Class for storing information on a 'sample' within an Illumina project

    A sample is a fastq file generated within an Illumina GA2 sequencer run.

    Provides the following attributes:

    name:  sample name
    dirn:  (full) path of the directory for the sample
    fastq: name of the fastq.gz file (without leading directory, join to
           'dirn' to get full path)

    """

    def __init__(self,dirn):
        """Create and populate a new IlluminaSample object

        Arguments:
          dirn: path to the directory holding the fastq.gz file for the
                sample

        """
        self.dirn = dirn
        self.fastq = []
        # Get name by removing prefix
        self.sample_prefix = "Sample_"
        self.name = os.path.basename(dirn)[len(self.sample_prefix):]
        logging.debug("\tSample: %s" % self.name)
        # Look for fastq files
        for f in os.listdir(self.dirn):
            if f.endswith(".fastq.gz"):
                self.fastq.append(f)
                logging.debug("\tFastq : %s" % f)
        if not self.fastq:
            raise IlluminaDataError, "Unable to find fastq.gz files for %s" % \
                self.name

class IlluminaDataError(Exception):
    """Base class for errors with Illumina-related code"""

#######################################################################
# Main program
#######################################################################

if __name__ == "__main__":
    # Create command line parser
    p = optparse.OptionParser(usage="%prog OPTIONS illumina_data_dir",
                              description="Create per-project analysis directories for "
                              "Illumina run. 'illumina_data_dir' is the top-level directory "
                              "containing the 'Unaligned' directory with the fastq.gz files "
                              "generated from the bcl files. For each 'Project_...' directory "
                              "%prog makes a new subdirectory and populates with links to "
                              "the fastq.gz files for each sample under that project.")
    p.add_option("-l","--list",action="store_true",dest="list",
                 help="list projects and samples without creating the analysis directories")
    p.add_option("--dry-run",action="store_true",dest="dry_run",
                 help="report operations that would be performed if creating the "
                 "analysis directories but don't actually do them")
    p.add_option("--unaligned",action="store",dest="unaligned_dir",default="Unaligned",
                 help="specify an alternative name for the 'Unaligned' directory "
                 "conatining the fastq.gz files")
    p.add_option("--expt",action="append",dest="expt_type",default=[],
                 help="specify experiment type (e.g. ChIP-seq) to append to the project name "
                 "when creating analysis directories. The syntax for EXPT_TYPE is "
                 "'<project>:<type>' e.g. --expt=NY:ChIP-seq will create directory "
                 "'NY_ChIP-seq'. Use multiple --expt=... to set the types for different "
                 "projects")
    # Parse command line
    options,args = p.parse_args()

    # Get data directory name
    if len(args) != 1:
        p.error("expected one argument (location of Illumina analysis dir)")
    illumina_analysis_dir = os.path.abspath(args[0])

    # Populate Illumina data object
    illumina_data = IlluminaData(illumina_analysis_dir,unaligned_dir=options.unaligned_dir)

    # List option
    if options.list:
        for project in illumina_data.projects:
            print "Project: %s (%d samples)" % (project.name,len(project.samples))
            for sample in project.samples:
                if len(sample.fastq) == 1:
                    print "\t%s" % sample.name
                else:
                    print "\t%s (%d fastqs)" % (sample.name,len(sample.fastq)) 
        sys.exit()

    # Assign experiment types
    for expt in options.expt_type:
        name,type_ = expt.split(':')
        illumina_data.get_project(name).expt_type = type_

    # Create and populate per-project directory structure
    for project in illumina_data.projects:
        project_name = project.name
        if project.expt_type is not None:
            project_name += "_%s" % project.expt_type
        project_dir = os.path.join(illumina_analysis_dir,project_name)
        print "Creating analysis directory for project '%s'..." % project_name
        # Check for & create directory
        if os.path.exists(project_dir):
            print "-> %s already exists" % project_dir
        else:
            print "Making analysis directory for %s" % project.name
            if not options.dry_run: os.mkdir(project_dir)
        # Check for & create links to fastq files
        for sample in project.samples:
            for fastq in sample.fastq:
                fastq_file = os.path.join(sample.dirn,fastq)
                fastq_ln = os.path.join(project_dir,sample.name+'.fastq.gz')
                if os.path.exists(fastq_ln):
                    print "-> %s.fastq.gz already exists" % sample.name
                else:
                    print "Linking to %s" % sample.fastq            
                    if not options.dry_run: os.symlink(fastq,fastq_ln)

