#!/bin/env python
#
#     analyse_illumina_run.py: analyse and report on Illumina sequencer runs
#     Copyright (C) University of Manchester 2013 Peter Briggs
#
"""analyse_illumina_run.py

Provides functionality for analysing data from an Illumina sequencer run.

"""

__version__ = "0.1.0"

#######################################################################
# Import modules
#######################################################################

import os
import sys
import optparse
import shutil
import logging
logging.basicConfig(format="%(levelname)s %(message)s")

# Put ../share onto Python search path for modules
SHARE_DIR = os.path.abspath(
    os.path.normpath(
        os.path.join(os.path.dirname(sys.argv[0]),'..','share')))
sys.path.append(SHARE_DIR)
import IlluminaData

#######################################################################
# Functions
#######################################################################

def name_matches(name,pattern):
    """Simple wildcard matching of project and sample names
    
    Arguments
      name: text to match against pattern
      pattern: simple 'glob'-like pattern to match against

    Returns
      True if name matches pattern; False otherwise.
    """
    if not pattern.endswith('*'):
        # Exact match required
        return (name == pattern)
    else:
        return name.startswith(pattern.rstrip('*'))

#######################################################################
# Main program
#######################################################################

if __name__ == "__main__":
    # Create command line parser
    p = optparse.OptionParser(usage="%prog OPTIONS illumina_data_dir",
                              version="%prog "+__version__,
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
                 "containing the fastq.gz files")
    p.add_option("--copy",action="store",dest="copy_pattern",default=None,
                 help="copy fastq.gz files matching COPY_PATTERN to current directory")
    p.add_option("--verify",action="store",dest="sample_sheet",default=None,
                 help="check CASAVA outputs against those expected for SAMPLE_SHEET")
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
            options.list or
            options.sample_sheet):
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
            sample_names = project.prettyPrintSamples()
            print "Project %s: %s (%d samples)" % (project_name,
                                                   sample_names,
                                                   n_samples)

    # Copy fastq.gz files to the current directory
    if options.copy_pattern is not None:
        # Extract project and sample names/patterns
        try:
            project_pattern,sample_pattern = options.copy_pattern.split("/")
            print "Copy: look for samples matching pattern %s" % options.copy_pattern
            print "Data files will be copied to %s" % os.getcwd()
        except ValueError:
            logging.error("ERROR invalid pattern '%s'" % options.copy_pattern)
            sys.exit(1)
        # Loop through projects and samples looking for matches
        for project in illumina_data.projects:
            if name_matches(project.name,project_pattern):
                # Loop through samples
                for sample in project.samples:
                    if name_matches(sample.name,sample_pattern):
                        for fastq in sample.fastq:
                            fastq_file = os.path.join(sample.dirn,fastq)
                            print "\tCopying .../%s" % os.path.basename(fastq_file)
                            dst = os.path.abspath(os.path.basename(fastq_file))
                            if os.path.exists(dst):
                                logging.error("File %s already exists! Skipped" % dst)
                            else:
                                shutil.copy(fastq_file,dst)

    # Verify against sample sheet
    if options.sample_sheet is not None:
        # Get predicted outputs
        predicted_projects = IlluminaData.\
            CasavaSampleSheet(options.sample_sheet).predict_output()
        # Loop through projects and check that predicted outputs exist
        status = 0
        for proj in predicted_projects:
            # Locate project directory
            proj_dir = os.path.join(illumina_data.unaligned_dir,proj)
            if os.path.isdir(proj_dir):
                predicted_samples = predicted_projects[proj]
                for smpl in predicted_samples:
                    # Locate sample directory
                    smpl_dir = os.path.join(proj_dir,smpl)
                    if os.path.isdir(smpl_dir):
                        # Check for output files
                        predicted_names = predicted_samples[smpl]
                        for name in predicted_names:
                            # Look for R1 file
                            f = os.path.join(smpl_dir,"%s_R1_001.fastq.gz" % name)
                            if not os.path.exists(f):
                                logging.warning("Verify: missing R1 file '%s'" % f)
                                status = 1
                            # Look for R2 file (paired end only)
                            if illumina_data.paired_end:
                                f = os.path.join(smpl_dir,"%s_R2_001.fastq.gz" % name)
                                if not os.path.exists(f):
                                    logging.warning("Verify: missing R2 file '%s'" % f)
                                    status = 1
                    else:
                        # Sample directory not found
                        logging.warning("Verify: missing %s" % smpl_dir)
                        status = 1
            else:
                # Project directory not found
                logging.warning("Verify: missing %s" % proj_dir)
                status = 1
        # Finished
        if status == 0:
            print "Verification against sample sheet '%s': OK" % \
                options.sample_sheet
        else:
            logging.error("Verification against sample sheet '%s': FAILED" %
                          options.sample_sheet)
        sys.exit(status)
                            
                
                
                                    
        
