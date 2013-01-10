#!/bin/env python
#
#     analyse_illumina_run.py: analyse and report on Illumina sequencer runs
#     Copyright (C) University of Manchester 2013 Peter Briggs
#
"""analyse_illumina_run.py

Provides functionality for analysing data from an Illumina sequencer run.

"""

#######################################################################
# Import modules
#######################################################################

import os
import sys
import optparse

# Put ../share onto Python search path for modules
SHARE_DIR = os.path.abspath(
    os.path.normpath(
        os.path.join(os.path.dirname(sys.argv[0]),'..','share')))
sys.path.append(SHARE_DIR)
import IlluminaData

#######################################################################
# Functions
#######################################################################

# No functions defined

#######################################################################
# Main program
#######################################################################

if __name__ == "__main__":
    # Create command line parser
    p = optparse.OptionParser(usage="%prog OPTIONS illumina_data_dir",
                              description="Utility for performing various checks and "
                              "operations on Illumina data. 'illumina_data_dir' is the "
                              "top-level directory containing the 'Unaligned' directory "
                              "with the fastq.gz files.")
    p.add_option("--report",action="store_true",dest="report",
                 help="report sample names and number of samples for each project")
    p.add_option("-l","--list",action="store_true",dest="list",
                 help="list projects, samples and fastq files directories")
    p.add_option("--unaligned",action="store",dest="unaligned_dir",default="Unaligned",
                 help="specify an alternative name for the 'Unaligned' directory "
                 "conatining the fastq.gz files")
    # Parse command line
    options,args = p.parse_args()

    # Get data directory name
    if len(args) != 1:
        p.error("expected one argument (location of Illumina analysis dir)")
    illumina_analysis_dir = os.path.abspath(args[0])

    # Populate Illumina data object
    illumina_data = IlluminaData.IlluminaData(illumina_analysis_dir,
                                              unaligned_dir=options.unaligned_dir)

    # Check there's at least one thing to do
    if not (options.report or 
            options.list):
        options.report = True

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

    # Report the names of the samples in each project
    if options.report:
        for project in illumina_data.projects:
            project_name = project.name
            n_samples = len(project.samples)
            sample_names = ', '.join([str(s.name) for s in project.samples])
            print "Project %s: %s (%d samples)" % (project_name,
                                                   sample_names,
                                                   n_samples)
