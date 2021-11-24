#!/usr/bin/env python
#
#     build_illumina_analysis_dir.py: build analysis dir with links to fastq files
#     Copyright (C) University of Manchester 2012-2013,2019,2021 Peter Briggs
#

__version__ = "1.1.1"

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
import argparse
import logging
import gzip

# Put .. onto Python search path for modules
SHARE_DIR = os.path.abspath(
    os.path.normpath(
        os.path.join(os.path.dirname(sys.argv[0]),'..')))
sys.path.append(SHARE_DIR)
import bcftbx.IlluminaData as IlluminaData
import bcftbx.utils as bcf_utils

#######################################################################
# Functions
#######################################################################

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
    print("Creating analysis directory for project '%s'..." % project.full_name)
    # Check for & create directory
    if os.path.exists(project_dir):
        print("-> %s already exists" % project_dir)
    else:
        print("Making analysis directory for %s" % project.name)
        if not dry_run:
            bcf_utils.mkdir(project_dir,mode=0o775)
    # Make an empty ScriptCode directory
    scriptcode_dir = os.path.join(project_dir,"ScriptCode")
    if os.path.exists(scriptcode_dir):
        print("'ScriptCode' directory %s already exists" % scriptcode_dir)
    else:
        print("Making 'ScriptCode' directory for %s" % project.name)
        if not dry_run:
            bcf_utils.mkdir(scriptcode_dir,mode=0o775)
    # Check for & create links to fastq files
    if not merge_replicates:
        for sample in project.samples:
            fastq_names = IlluminaData.get_unique_fastq_names(sample.fastq)
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
                    print("Linking to %s" % fastq)
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
            print("Sample %s" % sample.name)
            for name in replicates:
                print("\tReplicate '%s'" % name)
                for fastq in replicates[name]:
                    print("\t\t%s" % fastq)
            # Do the merge
            for name in replicates:
                merged_fastq = os.path.join(project_dir,name+'.fastq')
                bcf_utils.concatenate_fastq_files(merged_fastq,replicates[name])
    # Return directory name
    return project_dir

#######################################################################
# Main program
#######################################################################

if __name__ == "__main__":
    # Create command line parser
    p = argparse.ArgumentParser(
        description="Create per-project analysis directories for "
        "Illumina run. 'illumina_data_dir' is the top-level directory "
        "containing the 'Unaligned' directory with the fastq.gz files "
        "generated from the bcl files. For each 'Project_...' directory "
        "%prog makes a new subdirectory and populates with links to "
        "the fastq.gz files for each sample under that project.")
    p.add_argument('--version',action='version',
                   version=("%%(prog)s %s" % __version__))
    p.add_argument("--dry-run",action="store_true",dest="dry_run",
                   help="report operations that would be performed if "
                   "creating the analysis directories but don't actually "
                   "do them")
    p.add_argument("--unaligned",action="store",dest="unaligned_dir",
                   default="Unaligned",
                   help="specify an alternative name for the 'Unaligned' "
                   "directory conatining the fastq.gz files")
    p.add_argument("--expt",action="append",dest="expt_type",default=[],
                   help="specify experiment type (e.g. ChIP-seq) to append "
                   "to the project name when creating analysis directories. "
                   "The syntax for EXPT_TYPE is '<project>:<type>' e.g. "
                   "--expt=NY:ChIP-seq will create directory 'NY_ChIP-seq'. "
                   "Use multiple --expt=... to set the types for different "
                   "projects")
    p.add_argument("--keep-names",action="store_true",dest="keep_names",
                   default=False,
                   help="preserve the full names of the source fastq files "
                   "when creating links")
    p.add_argument("--merge-replicates",action="store_true",
                   dest="merge_replicates",default=False,
                   help="create merged fastq files for each set of "
                   "replicates detected")
    p.add_argument('illumina_data_dir',
                   help="top-level directory containing the 'Unaligned' "
                   "directory with the fastq.gz files")
    # Parse command line
    args = p.parse_args()

    # Get data directory name
    illumina_analysis_dir = os.path.abspath(args.illumina_data_dir)

    # Populate Illumina data object
    illumina_data = IlluminaData.IlluminaData(illumina_analysis_dir,
                                              unaligned_dir=args.unaligned_dir)

    # Assign experiment types
    for expt in args.expt_type:
        name,type_ = expt.split(':')
        illumina_data.get_project(name).expt_type = type_

    # Create and populate per-project directory structure
    for project in illumina_data.projects:
        create_analysis_dir(project,
                            top_dir=illumina_analysis_dir,
                            merge_replicates=args.merge_replicates,
                            keep_names=args.keep_names,
                            dry_run=args.dry_run)


