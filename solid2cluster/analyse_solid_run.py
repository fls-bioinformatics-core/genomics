#!/bin/env python
#
#     analyse_solid_run.py: analyse and report on SOLiD sequencer runs
#     Copyright (C) University of Manchester 2011-12 Peter Briggs
#
########################################################################
#
# analyse_solid_run.py
#
#########################################################################

"""analyse_solid_run.py

Provides functionality for analysing a SOLiD run, to verify and report data
about the run, and suggest a layout scheme for the analysis directories.
"""

#######################################################################
# Import modules that this module depends on
#######################################################################

import sys
import os
import string
import shutil
import optparse
import logging
logging.basicConfig(format="%(levelname)s %(message)s")

# Put ../share onto Python search path for modules
SHARE_DIR = os.path.abspath(
    os.path.normpath(
        os.path.join(os.path.dirname(sys.argv[0]),'..','share')))
sys.path.append(SHARE_DIR)
import SolidData
import Experiment

#######################################################################
# Class definitions
#######################################################################

# No classes defined

#######################################################################
# Module Functions: program functions
#######################################################################

def report_run(solid_runs):
    """Print a brief report about SOLiD runs.

    This generates a brief screen report about the content of the
    supplied SOLiD runs e.g. flow cells, layout, number of samples
    etc.

    Arguments:
      solid_runs: a list or tuple of SolidRun objects to report.
    """
    # Report the data for each run
    first_run = True
    for run in solid_runs:
        # Cosmetic: add separation between runs
        if not first_run:
            print
        else:
            first_run = False
        # Report overall slide layout
        slide_layout = run.slideLayout()
        title = "Flow Cell %s (%s)" % (str(run.run_info.flow_cell),
                                       str(slide_layout))
        print "%s\n%s\n%s" % ('#'*len(title),title,'#'*len(title))
        print "I.D.   : %s" % (run.run_info.name)
        print "Date   : %s" % (run.run_info.date)
        print "Samples: %d" % len(run.samples)
        if run.is_paired_end:
            print "\nPaired-end run"
        #
        # Report projects for each sample
        for sample in run.samples:
            title = "\nSample %s" % sample
            title = title + '\n' + "="*len(title)
            print title
            for project in sample.projects:
                libraries = project.prettyPrintLibraries()
                title = "Project %s: %s (%d libraries)" % (project.name,
                                                           libraries,
                                                           len(project.libraries))
                title = '\n' + title + '\n' + "-"*len(title)
                print title
                print "Pattern: %s/%s" % (sample,project.getLibraryNamePattern())
                # Report location of primary data
                for library in project.libraries:
                    files = [library.csfasta,library.qual]
                    if run.is_paired_end:
                        files.extend((library.csfasta_f5,library.qual_f5))
                    for f in files:
                        if f is not None:
                            print "%s" % f
                        else:
                            print "Missing primary data for %s" % library.name

def write_spreadsheet(solid_runs,spreadsheet):
    """Generate or append run data to an XLS-format spreadsheet

    Creates a new spreadsheet or appends to an existing one, writing
    new rows to summarise the data about the solid runs supplied as
    input.

    Arguments:
      solid_runs: a list or tuple of SolidRun objects to report.
      spreadsheet: the name of the XLS-format spreadsheet to write
        the data
    """
    # Check whether spreadsheet file already exists
    if os.path.exists(spreadsheet):
        write_header = False
    else:
        write_header = True

    # Only write date once
    write_date = True

    # Open spreadsheet
    wb = Spreadsheet.Spreadsheet(spreadsheet,'SOLiD Runs')

    # Header row
    if write_header:
        wb.addTitleRow(['Ref No',
                        'Project Description',
                        'P.I.',
                        'Date',
                        'Library type',
                        'Sample & Layout Description',
                        'B/C samples',
                        'Total reads',
                        'I.D.',
                        'Cost'])
    
    # Spacer row
    wb.addEmptyRow(color='gray25')

    # Report the data for each run
    for run in solid_runs:
        # First line: date, flow cell layout, and id
        slide_layout = run.slideLayout()
        if slide_layout is None:
            # Unknown layout arrangement
            slide_layout = "%d samples" % len(run.samples)
        description = "FC"+str(run.run_info.flow_cell)+" ("+slide_layout+")"
        # Run with only one sample
        total_reads = ''
        if len(run.samples) == 1:
            description += ": "+str(run.samples[0].name)
            try:
                if run.samples[0].projects[0].isBarcoded():
                    # Barcoded sample, get stats
                    total_reads = run.samples[0].barcode_stats.totalReads()
                    if total_reads is None:
                        # Potential problem
                        total_reads = "NOT_FOUND"
                else:
                    # Not a barcoded sample
                    total_reads = "MANUAL_LOOKUP"
            except IndexError:
                # Some problem looking up barcode status
                total_reads = "NO_INFO"
        # Deal with date string
        if write_date:
            run_date = run.run_info.date
            write_date = False # Don't write date again
        else:
            run_date = ''
        run_id = run.run_info.name
        wb.addRow(['',
                   '',
                   '',
                   run_date,
                   '',
                   description,
                   '',
                   total_reads,
                   run_id])
        # Add one line per project in each sample
        index = 0
        for sample in run.samples:
            for project in sample.projects:
                libraries = project.prettyPrintLibraries()
                experimenters_initials = project.libraries[0].initials
                # Get initial description and total reads
                if len(run.samples) > 1:
                    # Multiple samples in one project
                    description = sample.name+": "
                    # Total reads
                    # For barcoded samples we should be able to extract
                    # thos from the barcode statistics data
                    if project.isBarcoded():
                        total_reads = sample.barcode_stats.totalReads()
                        if total_reads is None:
                            # Potential problem
                            total_reads = "NOT_FOUND"
                    else:
                        # Not a barcoded sample, manual lookup
                        total_reads = "MANUAL_LOOKUP"
                else:
                    # All libraries belong to the same sample
                    description = ''
                    # Total reads already written once
                    total_reads = ''
                # Library type
                if project.isBarcoded():
                    library_type = "bar-coding"
                else:
                    library_type = ''
                # Add samples to the libraries
                description += str(len(project.libraries))+" samples "+\
                    libraries
                # Project description field
                # Essentially a placeholder with experimenter's initials
                project_description = "%s) %s [project description]" % \
                    (string.lowercase[index],experimenters_initials)
                index += 1
                # FIXME need to check that this total read info is
                # actually correct
                wb.addRow(['',
                           project_description,
                           '[P.I.]',
                           '',
                           library_type,
                           description,
                           len(project.libraries),
                           total_reads])
                wb.addEmptyRow()
                
    # Write the spreadsheet
    wb.write()

def suggest_analysis_layout(solid_runs):
    """Generate a bash script to build the analysis directory scheme

    Given a set of SolidRuns, print a set of script commands for running the
    build_analysis_dir.py program to create and populate the analysis directories.

    The script can be edited before being executed by the user.

    Arguments:
      solid_runs: a list of SolidRun objects.
    """
    print "#!/bin/sh\n#\n# Script commands to build analysis directory structure"
    for run in solid_runs:
        build_analysis_dir_cmd = 'build_analysis_dir.py'
        top_dir = os.path.abspath(os.path.join(os.getcwd(),os.path.basename(run.run_dir)))
        for sample in run.samples:
            for project in sample.projects:
                # Create one experiment per project
                cmd_line = []
                expt = Experiment.Experiment()
                expt.name = project.getProjectName()
                expt.type = "expt"
                expt.sample = project.getSample().name
                expt.library = project.getLibraryNamePattern()
                # Print the arguments for the layout
                cmd_line.extend((build_analysis_dir_cmd,
                                 "--top-dir=%s_analysis" % top_dir,
                                 "--link=relative",
                                 "--naming-scheme=partial"))
                cmd_line.append(expt.describe())
                cmd_line.append(run.run_dir)
                print "#\n%s" % (' \\\n').join(cmd_line)

def suggest_rsync_command(solid_runs):
    """Generate a bash script to rsync data to another location

    Given a set of SolidRuns, print a set of script commands for running rsync
    to copy the data directories to another location.

    The script should be edited before being executed by the user.
    """
    print "#!/bin/sh\n#"
    print "# Script command to rsync a subset of data to another location"
    print "# Edit the script to remove the exclusions on the data sets to be copied"
    for run in solid_runs:
        print "rsync --dry-run -av -e ssh \\"
        for sample in run.samples:
            for library in sample.libraries:
                print "--exclude=" + str(library) + " \\"
        print "%s user@remote.system:/destination/parent/dir" % run.run_dir

def verify_runs(solid_dirs):
    """Do basic verification checks on SOLiD run directories

    For each SOLiD run directory, create a SolidRun object and check for the
    expected sample and library directories, and that primary data files
    (csfasta and qual) have been assigned and exist.

    Returns a UNIX-like status code: 0 indicates that the checks passed,
    1 indicates that they failed.

    Arguments:
      solid_dirs: a list of SOLiD sequencing directory names.

    Returns:
      0 if the run is verified, 1 if there is a problem.
    """
    print "Performing verification"
    status = 0
    for solid_dir in solid_dirs:
        # Initialise
        run_status = 0
        run = SolidData.SolidRun(solid_dir)
        if not run.verify():
            run_status = 1
        print "%s:" % run.run_name,
        if run_status == 0:
            print " [PASSED]"
        else:
            print " [FAILED]"
            status = 1
    # Completed
    print "Overall status:",
    if status == 0:
        print " [PASSED]"
    else:
        print " [FAILED]"
    return status

def print_md5sums(solid_runs):
    """Calculate and print md5sums for primary data files

    This will generate a list of md5sums that can be passed to the
    md5sum program to check against a copy of the the runs using

    md5sum -c CHECKSUMS

    Arguments:
      solid_runs: list or tuple of SolidRun instances.
    """
    for run in solid_runs:
        for sample in run.samples:
            for library in sample.libraries:
                try:
                    print "%s  %s" % (Md5sum.md5sum(library.csfasta),
                                      strip_prefix(library.csfasta,os.getcwd()))
                except Exception,ex:
                    logging.error("FAILED for F3 csfasta: %s" % ex)
                try:
                    print "%s  %s" % (Md5sum.md5sum(library.qual),
                                      strip_prefix(library.qual,os.getcwd()))
                except Exception,ex:
                    logging.error("FAILED for F3 qual: %s" % ex)
                if run.is_paired_end:
                    try:
                        print "%s  %s" % (Md5sum.md5sum(library.csfasta_f5),
                                          strip_prefix(library.csfasta_f5,os.getcwd()))
                    except Exception,ex:
                        logging.error("FAILED for F5 csfasta: %s" % ex)
                    try:
                        print "%s  %s" % (Md5sum.md5sum(library.qual_f5),
                                          strip_prefix(library.qual_f5,os.getcwd()))
                    except Exception,ex:
                        logging.error("FAILED for F5 qual: %s" % ex)

def copy_data(solid_runs,library_defns):
    """Copy selection of primary data files to current directory

    Locates primary data files matching a sample/library specification
    string of the form <sample_pattern>/<library_pattern>. The patterns
    are matching against sample and library names, and can be either
    exact or can include a trailing wildcard character (i.e. *) to match
    multiple names. For example:

    - 'SA_LH_POOL_49/LH1' matches the library called 'LH1' in the sample
      'SA_LH_POOL_49';

    - '*/LH1' matches all libraries called 'LH1' in any sample;

    - '*/LH*' matches all libraries starting 'LH' in any sample;

    - '*/*' matches all primary data files in all runs

    The files are copied to the current directory.

    Arguments:
      solid_runs: list of populated SolidRun objects
      library_defns: list of library definition strings (see above
        for syntax/format)
    """
    for library_defn in library_defns:
        sample = library_defn.split('/')[0]
        library = library_defn.split('/')[1]
        print "Copy: look for samples matching pattern %s" % library_defn
        print "Data files will be copied to %s" % os.getcwd()
        for run in solid_runs:
            for lib in run.fetchLibraries(sample,library):
                print "-> matched %s/%s" % (lib.parent_sample.name,lib.name)
                primary_data_files =[]
                primary_data_files.append(lib.csfasta)
                primary_data_files.append(lib.qual)
                if run.is_paired_end:
                    primary_data_files.append(lib.csfasta_f5)
                    primary_data_files.append(lib.qual_f5)
                for filn in primary_data_files:
                    print "\tCopying .../%s" % os.path.basename(filn)
                    dst = os.path.abspath(os.path.basename(filn))
                    if os.path.exists(dst):
                        logging.error("File %s already exists! Skipped" % dst)
                    else:
                        shutil.copy(filn,dst)

def strip_prefix(path,prefix):
    """Strip the supplied prefix from a file name
    """
    if path.startswith(prefix):
        new_path = path.replace(prefix,'',1)
        if new_path.startswith(os.sep):
            new_path = new_path.replace(os.sep,'',1)
        return new_path
    else:
        return path

#######################################################################
# Main program
#######################################################################

if __name__ == "__main__":

    # Set up command line parser
    p = optparse.OptionParser(usage="%prog OPTIONS solid_run_dir [ solid_run_dir ... ]",
                              description="Utility for performing various checks and "
                              "operations on SOLiD run directories. If a single "
                              "solid_run_dir is specified then %prog automatically finds "
                              "and operates on all associated directories from the same "
                              "instrument and with the same timestamp.")

    p.add_option("--only",action="store_true",dest="only",
                 help="only operate on the specified solid_run_dir, don't "
                 "locate associated run directories")
    p.add_option("--report",action="store_true",dest="report",
                 help="print a report of the SOLiD run")
    p.add_option("--xls",action="store_true",dest="xls",
                 help="write report to Excel spreadsheet")
    p.add_option("--verify",action="store_true",dest="verify",
                 help="do verification checks on SOLiD run directories")
    p.add_option("--layout",action="store_true",dest="layout",
                 help="generate script for laying out analysis directories")
    p.add_option("--md5sum",action="store_true",dest="md5sum",
                 help="calculate md5sums for primary data files")
    p.add_option("--rsync",action="store_true",dest="rsync",
                 help="generate script for rsyncing data")
    p.add_option("--copy",action="append",dest="copy_pattern",default=[],
                 help="copy primary data files to pwd from specific library "
                 "where names match COPY_PATTERN, which should be of the "
                 "form '<sample>/<library>'")
    p.add_option("--quiet",action="store_true",dest="quiet",
                 help="suppress warnings")
    p.add_option("--debug",action="store_true",dest="debug",
                 help="turn on debugging output (nb overrides --quiet)")

    # Process the command line
    options,args = p.parse_args()

    # Check inputs
    if not len(args):
        p.error("Expected at least one SOLiD run directory name")

    # Reset logging level for --debug and --quiet
    if options.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    elif options.quiet:
        logging.getLogger().setLevel(logging.ERROR)

    # Solid run directories
    for arg in args:
        if not os.path.isdir(arg):
            logging.error("'%s' not found or not a directory" % arg)
            sys.exit(1)
    if len(args) == 1:
        # Single directory supplied
        if options.only:
            solid_dirs = [args[0]]
        else:
            # Add associated directories
            solid_dirs = SolidData.list_run_directories(args[0])
    else:
        # Use all supplied arguments
        solid_dirs = args

    # Output spreadsheet name
    if options.xls:
        spreadsheet = os.path.splitext(os.path.basename(solid_dirs[0]))[0] + ".xls"
        print "Writing spreadsheet %s" % spreadsheet

    # Check there's at least one thing to do
    if not (options.report or 
            options.layout or 
            options.xls or 
            options.verify or
            options.rsync or
            options.md5sum or
            options.copy_pattern):
        options.report = True

    # Get the run information
    solid_runs = []
    for solid_dir in solid_dirs:
        run = SolidData.SolidRun(solid_dir)
        if not run:
            logging.error("Error extracting run data for %s" % solid_dir)
            sys.exit(1)
        else:
            solid_runs.append(run)

    # Report the runs
    if options.report:
        report_run(solid_runs)

    # Report the runs to a spreadsheet
    if options.xls:
        try:
            import Spreadsheet
            write_spreadsheet(solid_runs,spreadsheet)
        except ImportError, ex:
            logging.error("Unable to write spreadsheet: %s" % ex)

    # Suggest a layout for analysis
    if options.layout:
        suggest_analysis_layout(solid_runs)

    # Generate script rsync
    if options.rsync:   
        suggest_rsync_command(solid_runs)

    # Generate md5sums
    if options.md5sum:
        try:
            import Md5sum
            print_md5sums(solid_runs)
        except ImportError:
            logging.error("Unable to generate MD5 sums: %s" % ex)

    # Copy specific primary data files
    if options.copy_pattern:
        copy_data(solid_runs,options.copy_pattern)

    # Do verification
    # Nb this should always be the last step
    # Use the verification return code as the exit status
    if options.verify:
        status = verify_runs(solid_dirs)
        sys.exit(status)
