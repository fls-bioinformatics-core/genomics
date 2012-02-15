#!/bin/env python
#
#     analyse_solid_run.py: analyse and report on SOLiD sequencer runs
#     Copyright (C) University of Manchester 2011 Peter Briggs
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
import logging
logging.basicConfig(format="%(levelname)s %(message)s")
try:
    # Preferentially use hashlib module
    import hashlib
except ImportError:
    # hashlib not available, use deprecated md5 module
    import md5

# Put ../share onto Python search path for modules
SHARE_DIR = os.path.abspath(
    os.path.normpath(
        os.path.join(os.path.dirname(sys.argv[0]),'..','share')))
sys.path.append(SHARE_DIR)
try:
    import SolidData
    import Experiment
    import Spreadsheet
except ImportError, ex:
    logging.warning("Error importing modules: %s" % ex)

#######################################################################
# Class definitions
#######################################################################

class Md5sum:
    """Utility class for generating MD5SUM checksums

    Code based on examples at:

    http://www.python.org/getit/releases/2.0.1/md5sum.py

    and

    http://stackoverflow.com/questions/1131220/get-md5-hash-of-a-files-without-open-it-in-python

    Example usage:
    >>> chksum = Md5Sum().md5sum("myfile.txt")
    eacc9c036025f0e64fb724cacaadd8b4

    This class implements two methods for generating the md5
    digest of a file: the first uses a method based on the hashlib
    module, while the second (used as a fallback for pre-2.5 Python)
    uses the now deprecated md5 module. Note however that the class
    determines itself which method to use.
    """

    def __init__(self):
        """Create a new Md5sum instance
        """
        self.__BLOCKSIZE = 1024*1024

    def __hexify(self,s):
        """Internal: return a hex representation of a string
        """
        return ("%02x"*len(s)) % tuple(map(ord, s))

    def __md5sum_hashlib(self,filen):
        """Return md5sum digest for a file using hashlib module

        This implements the md5sum checksum generation using the
        hashlib module. This should be available in Python 2.5.

        Arguments:
          filen: name of the file to generate the checksum from
        
        Returns:
          Md5sum digest for the named file.
        """
        chksum = hashlib.md5()
        with open(filen,'rb') as f: 
            for chunk in iter(lambda: f.read(self.__BLOCKSIZE), ''): 
                chksum.update(chunk)
        return self.__hexify(chksum.digest())

    def __md5sum_md5(self,filen):
        """Return md5sum digest for a file using md5 module

        This implements the md5sum checksum generation using the
        deprecated md5 module. This should only be used if the hashlib
        module is unavailable (e.g. Python 2.4 and earlier).

        Arguments:
          filen: name of the file to generate the checksum from
        
        Returns:
          Md5sum digest for the named file.
        """
        f = open(filen, "rb")
        chksum = md5.new()
        while 1:
            block = f.read(self.__BLOCKSIZE)
            if not block:
                break
            chksum.update(block)
        f.close()
        return self.__hexify(chksum.digest())

    def md5sum(self,filen):
        """Return md5sum digest for a file

        Arguments:
          filen: name of the file to generate the checksum from
        
        Returns:
          Md5sum digest for the named file.
        """
        try:
            # Attempt to use hashlib
            return self.__md5sum_hashlib(filen)
        except NameError:
            # hashlib not available, fall back to md5 module
            return self.__md5sum_md5(filen)

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
    for run in solid_runs:
        # Report overall slide layout
        slide_layout = run.slideLayout()
        title = "Flow Cell %s (%s)" % (str(run.run_info.flow_cell),
                                       str(slide_layout))
        title = title + '\n' + "="*len(title)
        print title
        print "I.D.   : %s" % (run.run_info.name)
        print "Date   : %s" % (run.run_info.date)
        print "Samples: %d\n" % len(run.samples)
        if SolidData.is_paired_end(run):
            print "Paired-end run\n"
        #
        # Report projects for each sample
        for sample in run.samples:
            title = "Sample %s" % sample
            title = title + '\n' + "-"*len(title)
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
                    print "%s\n%s" % (library.csfasta,library.qual)
                    if SolidData.is_paired_end(run):
                        print "%s\n%s" % (library.csfasta_reverse,library.qual_reverse)

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
        build_analysis_dir_cmd = os.path.join(os.path.dirname(sys.argv[0]),'build_analysis_dir.py')
        cmd_line = [ build_analysis_dir_cmd, "--top-dir=%s_analysis" % run.run_dir ]
        for sample in run.samples:
            for project in sample.projects:
                # Create one experiment per project
                expt = Experiment.Experiment()
                expt.name = project.getProjectName()
                expt.type = "expt"
                expt.sample = project.getSample().name
                expt.library = project.getLibraryNamePattern()
                # Print the arguments for the layout
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

def verify_runs(solid_runs):
    """Do basic verification checks on SOLiD run data

    For each run described by a SolidRun object, check that there is
    run_definition file, samples and libraries, and that primary data
    files (csfasta and qual) have been assigned and exist.

    Returns a UNIX-like status code: 0 indicates that the checks passed,
    1 indicates that they failed.

    Arguments:
      solid_runs: a list of SolidRun objects.
    """
    print "Performing verification"
    status = 0
    for run in solid_runs:
        print "\nExamining %s:" % run.run_name
        run_status = 0
        # Check that run_definition file loaded
        if not run.run_definition:
            print "Error with run_definition"
            run_status = 1
        else:
            # Check basic parameters: should have non-zero numbers of
            # samples and libraries
            if len(run.samples) == 0:
                print "No sample data"
                run_status = 1
            # Determine if run is paired-end
            paired_end = SolidData.is_paired_end(run)
            # Check libraries in each sample
            for sample in run.samples:
                if len(sample.libraries) == 0:
                    print "No libraries for sample %s" % sample.name
                    run_status = 1
                for library in sample.libraries:
                    # Check csfasta was found
                    if not library.csfasta:
                        print "No csfasta for %s/%s" % \
                            (sample.name,library.name)
                        run_status = 1
                    else:
                        if not os.path.exists(library.csfasta):
                            print "Missing csfasta for %s/%s" % \
                                (sample.name,library.name)
                            run_status = 1
                    # Check qual was found
                    if not library.qual:
                        print "No qual for %s/%s" % \
                            (sample.name,library.name)
                        run_status = 1
                    else:
                        if not os.path.exists(library.qual):
                            print "Missing qual for %s/%s" % \
                                (sample.name,library.name)
                            run_status = 1
                    # Paired-end run: check reverse reads
                    if paired_end:
                        if not library.csfasta_reverse:
                            print "No reverse csfasta for %s/%s" % \
                                (sample.name,library.name)
                            run_status = 1
                        else:
                            if not os.path.exists(library.csfasta_reverse):
                                print "Missing reverse csfasta for %s/%s" % \
                                    (sample.name,library.name)
                                run_status = 1
                        # Check for reverse qual
                        if not library.qual_reverse:
                            print "No reverse qual for %s/%s" % \
                                (sample.name,library.name)
                            run_status = 1
                        else:
                            if not os.path.exists(library.qual_reverse):
                                print "Missing reverse qual for %s/%s" % \
                                    (sample.name,library.name)
                                run_status = 1
        # Completed checks for run
        print "%s:" % run.run_name,
        if run_status == 0:
            print " [PASSED]"
        else:
            print " [FAILED]"
            status = 1
    # Completed
    print "\nOverall status:",
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
    md5sum = Md5sum()
    for run in solid_runs:
        for sample in run.samples:
            for library in sample.libraries:
                print "%s  %s" % (md5sum.md5sum(library.csfasta),
                                  strip_prefix(library.csfasta,os.getcwd()))
                print "%s  %s" % (md5sum.md5sum(library.qual),
                                  strip_prefix(library.qual,os.getcwd()))
                if SolidData.is_paired_end(run):
                    print "%s  %s" % (md5sum.md5sum(library.csfasta_reverse),
                                      strip_prefix(library.csfasta_reverse,os.getcwd()))
                    print "%s  %s" % (md5sum.md5sum(library.qual_reverse),
                                      strip_prefix(library.qual_reverse,os.getcwd()))

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
    # Get solid directories
    if len(sys.argv) < 2:
        print "Usage: %s [OPTIONS] <solid_run_dir>" % \
            os.path.basename(sys.argv[0])
        print ""
        print "Various operations on a SOLiD run directory. Note that if"
        print "<solid_run_dir>_2 also exists then this is automatically"
        print "detected and included in the processing."
        print ""
        print "Options:"
        print "  --report: print a report of the SOLiD run"
        print "  --verify: do verification checks on SOLiD run directories"
        print "  --layout: generate script for laying out analysis directories"
        print "  --rsync:  generate script for rsyncing data"
        print "  --spreadsheet[=<file>.xls]: write report to Excel spreadsheet"
        print "  --md5sum: calculate md5sums for primary data files"
        sys.exit()

    # Solid run directories
    solid_dir_fc1 = sys.argv[-1]
    solid_dir_fc2 = sys.argv[-1]+"_2"
    if os.path.isdir(solid_dir_fc2):
        solid_dirs = (solid_dir_fc1,solid_dir_fc2)
    else:
        solid_dirs = (solid_dir_fc1,)

    # Other options
    do_report_run = False
    if "--report" in sys.argv[1:-1]:
        do_report_run = True

    do_checks = False
    if "--verify" in sys.argv[1:-1]:
        do_checks = True

    do_suggest_layout = False
    if "--layout" in sys.argv[1:-1]:
        do_suggest_layout = True

    do_spreadsheet = False
    for arg in sys.argv[1:-1]:
        if arg.startswith("--spreadsheet"):
            do_spreadsheet = True
            try:
                i = arg.index("=")
                spreadsheet = arg[i+1:]
            except IndexError:
                spreadsheet = solid_dir_fc1+".xls"
            print "Writing spreadsheet %s" % spreadsheet

    do_suggest_rsync = False
    if "--rsync" in sys.argv[1:-1]:
        do_suggest_rsync = True

    do_md5sum = False
    if "--md5sum" in sys.argv[1:-1]:
        do_md5sum = True

    # Check there's at least one thing to do
    if not (do_report_run or 
            do_suggest_layout or 
            do_spreadsheet or 
            do_checks or
            do_suggest_rsync or
            do_md5sum):
        do_report_run = True

    # Get the run information
    solid_runs = []
    for solid_dir in solid_dirs:
        run = SolidData.SolidRun(solid_dir)
        if not run:
            print "Error extracting run data for %s" % solid_dir
        else:
            solid_runs.append(run)

    # Report the runs
    if do_report_run:
        report_run(solid_runs)

    # Report the runs to a spreadsheet
    if do_spreadsheet:
        write_spreadsheet(solid_runs,spreadsheet)

    # Suggest a layout for analysis
    if do_suggest_layout:
        suggest_analysis_layout(solid_runs)

    # Generate script rsync
    if do_suggest_rsync:   
        suggest_rsync_command(solid_runs)

    # Generate md5sums
    if do_md5sum:
        print_md5sums(solid_runs)

    # Do verification
    # Nb this should always be the last step
    # Use the verification return code as the exit status
    if do_checks:
        status = verify_runs(solid_runs)
        sys.exit(status)
