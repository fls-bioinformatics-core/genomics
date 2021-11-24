#!/usr/bin/env python
#
#     analyse_illumina_run.py: analyse and report on Illumina sequencer runs
#     Copyright (C) University of Manchester 2013,2019 Peter Briggs
#
"""analyse_illumina_run.py

Provides functionality for analysing data from an Illumina sequencer run.

"""

__version__ = "0.2.2"

#######################################################################
# Import modules
#######################################################################

import os
import sys
import argparse
import shutil
import logging
logging.basicConfig(format="%(levelname)s %(message)s")

# Put .. onto Python search path for modules
SHARE_DIR = os.path.abspath(
    os.path.normpath(
        os.path.join(os.path.dirname(sys.argv[0]),'..')))
sys.path.append(SHARE_DIR)
import bcftbx.IlluminaData as IlluminaData
import bcftbx.FASTQFile as FASTQFile
import bcftbx.utils as bcf_utils

#######################################################################
# Main program
#######################################################################

if __name__ == "__main__":
    # Create command line parser
    p = argparse.ArgumentParser(
        description="Utility for performing various checks and "
        "operations on Illumina data. 'illumina_data_dir' is the "
        "top-level directory containing the 'Unaligned' directory "
        "with the fastq.gz files.")
    p.add_argument('--version',action='version',
                   version=("%%(prog)s %s" % __version__))
    p.add_argument("--report",action="store_true",dest="report",
                   help="report sample names and number of samples for "
                   "each project")
    p.add_argument("--summary",action="store_true",dest="summary",
                   help="short report of samples (suitable for logging "
                   "file)")
    p.add_argument("-l","--list",action="store_true",dest="list",
                   help="list projects, samples and fastq files "
                   "directories")
    p.add_argument("--unaligned",action="store",dest="unaligned_dir",
                   default="Unaligned",
                   help="specify an alternative name for the 'Unaligned' "
                   "directory containing the fastq.gz files")
    p.add_argument("--copy",action="store",dest="copy_pattern",
                   default=None,
                   help="copy fastq.gz files matching COPY_PATTERN to "
                   "current directory")
    p.add_argument("--merge-fastqs",action="store_true",
                   dest="merge_fastqs",
                   help="Merge multiple fastqs for samples")
    p.add_argument("--verify",action="store",dest="sample_sheet",
                   default=None,
                   help="check CASAVA outputs against those expected "
                   "for SAMPLE_SHEET")
    p.add_argument("--stats",action="store_true",dest="stats",
                   help="Report statistics (read counts etc) for fastq "
                   "files")
    p.add_argument('illumina_data_dir',
                   help="top-level directory containing the 'Unaligned' "
                   "directory with the fastq.gz files")
    # Parse command line
    args = p.parse_args()

    # Get data directory name
    illumina_analysis_dir = os.path.abspath(args.illumina_data_dir)

    # Populate Illumina data object
    try:
        illumina_data = IlluminaData.IlluminaData(illumina_analysis_dir,
                                                  unaligned_dir=args.unaligned_dir)
    except IlluminaData.IlluminaDataError as ex:
        logging.error("Failed to collect data: %s",ex)
        sys.exit(1)

    # Check there's at least one thing to do
    report = args.report
    if not (args.report or
            args.summary or
            args.list or
            args.sample_sheet or
            args.merge_fastqs):
        report = True

    # List option
    if args.list:
        for project in illumina_data.projects:
            n_samples = len(project.samples)
            print("Project: %s (%d sample%s)" % (project.name,
                                                 n_samples,
                                                 's' if n_samples != 1 else ''))
            for sample in project.samples:
                if sample.paired_end:
                    n_fastq_pairs = len(sample.fastq_subset(read_number=1))
                    if n_fastq_pairs == 1:
                        print("\t%s (R1/R2 pair)" % sample.name)
                    else:
                        print("\t%s (%d fastq R1/R2 pairs)" %
                              (sample.name,n_fastq_pairs))
                else:
                    n_fastqs = len(sample.fastq)
                    if n_fastqs == 1:
                        print("\t%s" % sample.name)
                    else:
                        print("\t%s (%d fastqs)" % (sample.name,n_fastqs))
                # Print fastq names
                fastqs = sample.fastq_subset(read_number=1) + \
                         sample.fastq_subset(read_number=2)
                for fastq in fastqs:
                    print("\t\t%s" % fastq)

    # Report the names of the samples in each project
    if report:
        for project in illumina_data.projects:
            print("%s" % IlluminaData.describe_project(project))
            # Report statistics for fastq files
            if args.stats:
                # Print number of reads for each file, and file size
                for sample in project.samples:
                    for fastq in sample.fastq:
                        fq = os.path.join(sample.dirn,fastq)
                        nreads = FASTQFile.nreads(fq)
                        fsize = os.path.getsize(fq)
                        print("%s\t%s\t%d" % (fastq,
                                              bcf_utils.format_file_size(fsize),
                                              nreads))
            print("")

    # Summary: short report suitable for logging file
    if args.summary:
        print("%s" % IlluminaData.summarise_projects(illumina_data))

    # Print number of undetermined reads
    if args.stats and illumina_data.undetermined is not None:
        print("Undetermined indices")
        for lane in illumina_data.undetermined.samples:
            for fastq in lane.fastq:
                fq = os.path.join(lane.dirn,fastq)
                nreads = FASTQFile.nreads(fq)
                fsize = os.path.getsize(fq)
                print("%s\t%s\t%d" % (fastq,
                                      bcf_utils.format_file_size(fsize),
                                      nreads))

    # Copy fastq.gz files to the current directory
    if args.copy_pattern is not None:
        # Extract project and sample names/patterns
        try:
            project_pattern,sample_pattern = args.copy_pattern.split("/")
            print("Copy: look for samples matching pattern %s" %
                  args.copy_pattern)
            print("Data files will be copied to %s" % os.getcwd())
        except ValueError:
            logging.error("ERROR invalid pattern '%s'" % args.copy_pattern)
            sys.exit(1)
        # Loop through projects and samples looking for matches
        for project in illumina_data.projects:
            if bcf_utils.name_matches(project.name,project_pattern):
                # Loop through samples
                for sample in project.samples:
                    if bcf_utils.name_matches(sample.name,sample_pattern):
                        for fastq in sample.fastq:
                            fastq_file = os.path.join(sample.dirn,fastq)
                            print("\tCopying .../%s" %
                                  os.path.basename(fastq_file))
                            dst = os.path.abspath(os.path.basename(fastq_file))
                            if os.path.exists(dst):
                                logging.error("File %s already exists! Skipped" % dst)
                            else:
                                shutil.copy(fastq_file,dst)

    # Verify against sample sheet
    if args.sample_sheet is not None:
        if IlluminaData.verify_run_against_sample_sheet(illumina_data,
                                                        args.sample_sheet):
            print("Verification against sample sheet '%s': OK" %
                  args.sample_sheet)
            status = 0
        else:
            logging.error("Verification against sample sheet '%s': FAILED" %
                          args.sample_sheet)
            status = 1
        sys.exit(status)

    # Merge multiple fastqs in each sample
    if args.merge_fastqs:
        for project in illumina_data.projects:
            for sample in project.samples:
                for read in (1,2):
                    # Concatenate fastqs for this read
                    fastq_merged = sample.name
                    if sample.paired_end:
                        fastq_merged += "_R%d" % read
                    fastq_merged += ".fastq.gz"
                    bcf_utils.concatenate_fastq_files(fastq_merged,
                                                      sample.fastq_subset(read_number=read,
                                                                          full_path=True),
                                                      bufsize=1024*1024)


                    
