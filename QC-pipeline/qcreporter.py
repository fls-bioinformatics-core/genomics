#!/usr/bin/env python
#
#     qcreporter.py: generate report file for NGS qc runs
#     Copyright (C) University of Manchester 2012-2014,2019 Peter Briggs
#
########################################################################
#
# qcreporter.py
#
#########################################################################

"""qcreporter

Generate HTML reports for NGS QC pipeline runs.

"""

__version__ = "0.3.0"

#######################################################################
# Import modules that this module depends on
#######################################################################

import sys
import os
import argparse
import logging

# Put .. onto Python search path for modules
SHARE_DIR = os.path.abspath(
    os.path.normpath(
        os.path.join(os.path.dirname(sys.argv[0]),'..')))
sys.path.append(SHARE_DIR)
from bcftbx.qc.report import SolidQCReporter,IlluminaQCReporter,QCReporterError

# Configure logging output
logging.basicConfig(format="%(levelname)s: %(message)s")

#######################################################################
# Main program
#######################################################################

if __name__ == "__main__":
    # Set up command line parser
    p = argparse.ArgumentParser(version="%(prog)s "+__version__,
                                description=
                                "Generate QC report for each directory DIR "
                                "which contains the outputs from a QC script "
                                "(either SOLiD or Illumina). Creates a "
                                "'qc_report.<run>.<name>.html' file in DIR "
                                "plus an archive 'qc_report.<run>.<name>.zip' "
                                "which contains the HTML plus all the "
                                "necessary files for unpacking and viewing "
                                "elsewhere.")
    p.add_argument("--platform",action="store",dest="platform",default=None,
                   choices=('solid','illumina'),
                   help="explicitly set the type of sequencing platform "
                   "('solid', 'illumina')")
    p.add_argument("--format",action="store",dest="data_format",default=None,
                   choices=('solid','solid_paired_end','fastq','fastqgz'),
                   help="explicitly set the format of files ('solid', "
                   "'solid_paired_end', 'fastq', 'fastqgz')")
    p.add_argument("--qc_dir",action="store",dest="qc_dir",default='qc',
                 help="specify a different name for the QC results "
                   "subdirectory (default is 'qc')")
    p.add_argument("--verify",action="store_true",dest="verify",
                   default=False,
                   help="don't generate report, just verify the QC outputs")
    p.add_argument('--regexp',action='store',dest='pattern',default=None,
                   help="select subset of files which match regular "
                   "expression PATTERN")
    p.add_argument('--debug',action='store_true',dest='debug',default=False,
                   help="turn on debugging output")
    p.add_argument('dirs',metavar="DIR",nargs="+",
                   help="directory to report QC for")

    # Deal with command line
    arguments = p.parse_args()

    # Turn on debug output
    if arguments.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    # Loop over input directories
    for d in arguments.dirs:
        # Identify platform
        if arguments.platform is not None:
            platform = arguments.platform
        else:
            platform = None
            print "Acquiring QC outputs for samples in %s" % d
            try:
                os.path.abspath(d).index('solid')
                platform = 'solid'
            except ValueError:
                try:
                    os.path.abspath(d).index('ILLUMINA')
                    platform = 'illumina'
                except ValueError:
                    pass
        # Format of input files
        data_format = arguments.data_format
        # Determine the appropriate reporter type
        qcreporter_class = None
        if platform is None:
            logging.error("Unable to identify platform for %s (use "
                          "--platform option?)" % d)
        elif platform == 'solid':
            qcreporter_class = SolidQCReporter
        elif platform == 'illumina':
            qcreporter_class = IlluminaQCReporter
        else:
            logging.error("Unknown platform '%s'" % platform)
        # Create and populate a reporter, if possible
        qcreporter = None
        if qcreporter_class is not None:
            try:
                qcreporter = qcreporter_class(d,
                                              data_format=data_format,
                                              qc_dir=arguments.qc_dir,
                                              regex_pattern=
                                              arguments.pattern,
                                              version=__version__)
            except QCReporterError,ex:
                logging.error("Unable to extract data from %s: %s" % (d,ex))
        # Perform required action
        if qcreporter is not None:
            if arguments.verify:
                if qcreporter.samples:
                    # Run verification
                    status = qcreporter.verify()
                    if not status:
                        logging.error("QC failed for one or more samples in %s" % d)
                        sys.exit(1)
                    else:
                        print "QC verified for all samples in %s" % d
                else:
                    logging.error("QC failed: no samples identified in %s" % d)
                    sys.exit(1)
            else:
                if qcreporter.samples:
                    # Generate report
                    print "Generating report for %s" % d
                    qcreporter.zip()
                else:
                    logging.error("No samples identified in %s" % d)
                    sys.exit(1)
