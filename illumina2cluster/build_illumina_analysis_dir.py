#!/bin/env python
#
#     build_illumina_analysis_dir.py: build analysis dir with links to fastq files
#     Copyright (C) University of Manchester 2012-2013 Peter Briggs
#

__version__ = "1.0.1"

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

# Put ../share onto Python search path for modules
SHARE_DIR = os.path.abspath(
    os.path.normpath(
        os.path.join(os.path.dirname(sys.argv[0]),'..','share')))
sys.path.append(SHARE_DIR)
import IlluminaData
import bcf_utils

#######################################################################
# Functions
#######################################################################

def get_unique_fastqs(sample):
    """Generate mapping of full fastq names to shorter unique names
    
    Given an IlluminaSample object, return a dictionary mapping the
    full fastq file names to their shortest unique versions within
    the sample.

    Arguments:
      sample: a populated IlluminaSample object.

    Returns:
      Dictionary mapping fastq names to shortest unique versions
  
    """
    # Define a set of templates of increasing complexity,
    # from which to generate shortened names
    templates = [ "NAME",
                  "NAME TAG",
                  "NAME TAG LANE",
                  "FULL" ]
    # Try each template in turn to see if it can generate
    # a unique set of short names
    for template in templates:
        name_mapping = {}
        unique_names = []
        # Process each fastq file name
        for fastq in sample.fastq:
            fq = IlluminaData.IlluminaFastq(fastq)
            name = []
            if template == "FULL":
                name.append(str(fq))
            else:
                for t in template.split():
                    if t == "NAME":
                        name.append(fq.sample_name)
                    elif t == "TAG":
                        if fq.barcode_sequence is not None:
                            name.append(fq.barcode_sequence)
                    elif t == "LANE":
                        name.append("L%03d" % fq.lane_number)
                # Add the read number for paired end data
                if sample.paired_end:
                    name.append("R%d" % fq.read_number)
            name = '_'.join(name) + ".fastq.gz"
            # Store the name
            if name not in unique_names:
                name_mapping[fastq] = name
                unique_names.append(name)
        # If the number of unique names matches total number
        # of files then we have a unique set
        if len(unique_names) == len(sample.fastq):
            return name_mapping
    # Failed to make a unique set of names
    raise Exception,"Failed to make a set of unique fastq names"

def create_analysis_dir(project,
                        top_dir=None,
                        merge_replicates=False,
                        keep_names=False,
                        dry_run=False):
    """Create and populate analysis directory for an IlluminaProject

    Creates a new directory and populates either with links to FASTQ
    files, or with 'merged' FASTQ files created by concatenating
    multiple FASTQs for each sample (which can happen for multiplexed
    runs where samples are split across multiple lanes).

    Project directory names are made up of the project name and then
    the experiment type, or just the project name if experiment type
    is not set.

    Arguments:
      project   : populated IlluminaProject object
      top_dir   : parent directory to create analysis subdirectory
                  under. Defaults to cwd if not explicitly specified
      merge_replicates: if True then creates a single FASTQ file for
                  each sample by merging multiple FASTQs together
      keep_names: if True then links to FASTQ files will have the same
                  names as the original files; by default links use the
                  shortest unique name
      dry_run   : if True then report what would be done but don't
                  actually perform any action

    Returns:
      Name of the project directory.
    
    """
    project_dir = os.path.join(top_dir,project.full_name)
    print "Creating analysis directory for project '%s'..." % project.full_name
    # Check for & create directory
    if os.path.exists(project_dir):
        print "-> %s already exists" % project_dir
    else:
        print "Making analysis directory for %s" % project.name
        if not dry_run:
            bcf_utils.mkdir(project_dir,mode=0775)
    # Make an empty ScriptCode directory
    scriptcode_dir = os.path.join(project_dir,"ScriptCode")
    if os.path.exists(scriptcode_dir):
        print "'ScriptCode' directory %s already exists" % scriptcode_dir
    else:
        print "Making 'ScriptCode' directory for %s" % project.name
        if not dry_run:
            bcf_utils.mkdir(scriptcode_dir,mode=0775)
    # Check for & create links to fastq files
    if not merge_replicates:
        for sample in project.samples:
            fastq_names = IlluminaData.get_unique_fastqs_names(sample.fastqs)
            for fastq in sample.fastq:
                fastq_file = os.path.join(sample.dirn,fastq)
                if keep_names:
                    fastq_ln = os.path.join(project_dir,fastq)
                else:
                    fastq_ln = os.path.join(project_dir,fastq_names[fastq])
                if os.path.exists(fastq_ln):
                    logging.error("Failed to link to %s: %s already exists" %
                                  (fastq_file,os.path.basename(fastq_ln)))
                else:
                    print "Linking to %s" % fastq
                    if not dry_run:
                        bcf_utils.mklink(fastq_file,fastq_ln,relative=True)
    else:
        # Merge files for replicates within each sample
        for sample in project.samples:
            replicates = {}
            # Gather replicates to be merged
            for fastq in sample.fastq:
                fastq_data = IlluminaData.IlluminaFastq(fastq)
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
    # Return directory name
    return project_dir

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
                              version="%prog "+__version__,
                              description="Create per-project analysis directories for "
                              "Illumina run. 'illumina_data_dir' is the top-level directory "
                              "containing the 'Unaligned' directory with the fastq.gz files "
                              "generated from the bcl files. For each 'Project_...' directory "
                              "%prog makes a new subdirectory and populates with links to "
                              "the fastq.gz files for each sample under that project.")
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
    illumina_data = IlluminaData.IlluminaData(illumina_analysis_dir,
                                              unaligned_dir=options.unaligned_dir)

    # Assign experiment types
    for expt in options.expt_type:
        name,type_ = expt.split(':')
        illumina_data.get_project(name).expt_type = type_

    # Create and populate per-project directory structure
    for project in illumina_data.projects:
        create_analysis_dir(project,
                            top_dir=illumina_analysis_dir,
                            merge_replicates=options.merge_replicates,
                            keep_names=options.keep_names,
                            dry_run=options.dry_run)


