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
import gzip

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

class IlluminaFastq:
    """Class for extracting information about Fastq files

    Given the name of a Fastq file from CASAVA/Illumina platform, extract
    data about the sample name, barcode sequence, lane number, read number
    and set number.

    The format of the names follow the general form:

    <sample_name>_<barcode_sequence>_L<lane_number>_R<read_number>_<set_number>.fastq.gz

    e.g. for

    NA10831_ATCACG_L002_R1_001.fastq.gz

    sample_name = 'NA10831_ATCACG_L002_R1_001'
    barcode_sequence = 'ATCACG'
    lane_number = 2
    read_number = 1
    set_number = 1

    Provides the follow attributes:

    fastq:            the original fastq file name
    sample_name:      name of the sample (leading part of the name)
    barcode_sequence: barcode sequence (string or None)
    lane_number:      integer
    read_number:      integer
    set_number:       integer

    """
    def __init__(self,fastq):
        """Create and populate a new IlluminaFastq object

        Arguments:
          fastq: name of the fastq.gz (optionally can include leading path)

        """
        # Store name
        self.fastq = fastq
        # Values derived from the name
        self.sample_name = None
        barcode_sequence = None
        lane_number = None
        read_number = None
        set_number = None
        # Base name for sample (no leading path or extension)
        fastq_base = os.path.basename(fastq)
        try:
            i = fastq_base.index('.')
            fastq_base = fastq_base[:i]
        except ValueError:
            pass
        # Identify which part of the name is which
        fields = fastq_base.split('_')
        nfields = len(fields)
        # Set number: zero-padded 3 digit integer '001'
        self.set_number = int(fields[-1])
        # Read number: single integer digit 'R1'
        self.read_number = int(fields[-2][1])
        # Lane number: zero-padded 3 digit integer 'L001'
        self.lane_number = int(fields[-3][1:])
        # Barcode sequence: string (or None if 'NoIndex')
        self.barcode_sequence = fields[-4]
        if self.barcode_sequence == 'NoIndex':
            self.barcode_sequence = None
        # Sample name: whatever's left over
        self.sample_name = '_'.join(fields[:-4])

class IlluminaDataError(Exception):
    """Base class for errors with Illumina-related code"""


#######################################################################
# Functions
#######################################################################

def concatenate_fastq_files(merged_fastq,fastq_files):
    """Create a single FASTQ file by concatenating one or more FASTQs

    Given a list or tuple of FASTQ files (which can be compressed or
    uncompressed or a combination), creates a single output FASTQ by
    concatenating the contents.

    Arguments:
      merged_fastq: name of output FASTQ file (mustn't exist beforehand)
      fastq_files:  list of FASTQ files to concatenate

    """
    print "Creating merged fastq file '%s'" % merged_fastq
    # Check that initial file doesn't exist
    if os.path.exists(merged_fastq):
        logging.error("Target file '%s' already exists, stopping")
        sys.exit(1)
    # Create temporary name
    merged_fastq_part = merged_fastq+'.part'
    # Open final output file
    fq_merged = open(merged_fastq_part,'wb')
    # For each fastq, read data and append to output - simples!
    for fastq in fastq_files:
        print "Adding records from %s" % fastq
        # Check it exists
        if not os.path.exists(fastq):
            logging.error("'%s' not found, stopping" % fastq)
            sys.exit(1)
        # Check if it's compressed i.e. gz extension?
        gzipped = (os.path.splitext(fastq)[1] == ".gz")
        # Open file for reading
        if not gzipped:
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
    p.add_option("--keep-names",action="store_true",dest="keep_names",default=False,
                 help="preserve the full names of the source fastq files when creating links")
    p.add_option("--merge-replicates",action="store_true",dest="merge_replicates",default=False,
                 help="create merged fastq files for each set of replicates detected")
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
                for fastq in sample.fastq:
                    print "\t\t%s" % fastq
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
            if not options.dry_run:
                os.mkdir(project_dir)     
                os.chmod(project_dir,0775)
        # Check for & create links to fastq files
        if not options.merge_replicates:
            for sample in project.samples:
                for fastq in sample.fastq:
                    fastq_file = os.path.join(sample.dirn,fastq)
                    if options.keep_names:
                        fastq_ln = os.path.join(project_dir,fastq)
                    else:
                        fastq_ln = os.path.join(project_dir,sample.name+'.fastq.gz')
                    if os.path.exists(fastq_ln):
                        print "-> %s.fastq.gz already exists" % sample.name
                    else:
                        print "Linking to %s" % fastq
                        if not options.dry_run: os.symlink(fastq_file,fastq_ln)
        else:
            # Merge files for replicates within each sample
            for sample in project.samples:
                replicates = {}
                # Gather replicates to be merged
                for fastq in sample.fastq:
                    fastq_data = IlluminaFastq(fastq)
                    name = "%s_%s_R%d" % (fastq_data.sample_name,
                                          fastq_data.barcode_sequence,
                                          fastq_data.read_number)
                    if name not in replicates:
                        replicates[name] = []
                    replicates[name].append(os.path.join(sample.dirn,fastq))
                    # Sort into order
                    replicates[name].sort()
                # Report detected replicates
                print "Sample %s" % sample.name
                for name in replicates:
                    print "\tReplicate '%s'" % name
                    for fastq in replicates[name]:
                        print "\t\t%s" % fastq
                # Do the merge
                for name in replicates:
                    merged_fastq = os.path.join(project_dir,name+'.fastq')
                    concatenate_fastq_files(merged_fastq,replicates[name])
        # Make an empty ScriptCode directory
        scriptcode_dir = os.path.join(project_dir,"ScriptCode")
        if os.path.exists(scriptcode_dir):
            print "'ScriptCode' directory %s already exists" % scriptcode_dir
        else:
            print "Making 'ScriptCode' directory for %s" % project.name
            if not options.dry_run:
                os.mkdir(scriptcode_dir)     
                os.chmod(scriptcode_dir,0775)
        

