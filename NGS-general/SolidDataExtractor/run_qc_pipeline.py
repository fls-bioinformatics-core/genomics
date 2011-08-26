#!/bin/env python
#
#     run_pipeline.py: run pipeline script on file sets
#     Copyright (C) University of Manchester 2011 Peter Briggs
#
########################################################################
#
# run_pipeline.py
#
#########################################################################

"""run_pipeline.py

Implements a program to run a pipeline script or command on the
set of files in a specific directory.

Usage: python run_pipeline.py [OPTIONS] <script> <data_dir> [ <data_dir> ... ]

<script> must accept arguments based on the --input option, but defaults to
         a csfasta/qual file pair.
<data_dir> contains the input data for the script.
"""

#######################################################################
# Import modules that this module depends on
#######################################################################

import sys
import os
import time
import subprocess
import logging

#######################################################################
# Class definitions
#######################################################################

# No classes defined

#######################################################################
# Module Functions
#######################################################################

# RunScript: execute a script or command
def RunScript(script,csfasta,qual):
    """Run a script or command
    """
    cwd=os.path.dirname(csfasta)
    p = subprocess.Popen((script,csfasta,qual),cwd=cwd)
    print "Running..."
    p.wait()
    print "Finished"

# QsubScript: submit a command to the cluster
def QsubScript(name,script,*args):
    """Submit a script or command to the cluster via 'qsub'
    """
    # 
    logging.debug("QsubScript: submitting job")
    cmd_args = [script]
    cmd_args.extend(args)
    cmd = ' '.join(cmd_args)
    qsub=('qsub','-b','y','-cwd','-V','-N',name,cmd)
    cwd = os.getcwd()
    p = subprocess.Popen(qsub,cwd=cwd,stdout=subprocess.PIPE)
    p.wait()
    # Capture the job id from the output
    job_id = None
    for line in p.stdout:
        if line.startswith('Your job'):
            job_id = line.split()[2]
    logging.debug("QsubScript: done - job id = %s" % job_id)
    # Return the job id
    return job_id

# QstatJobs: get number of jobs user has already in queue
def QstatJobs(user=None):
    """Get the number of jobs a user has in the queue
    """
    # Get the results of qstat -u (assume current user if None)
    cmd = ['qstat']
    if user:
        cmd.extend(('-u',user))
    else:
        # Get current user name
        cmd.extend(('-u',os.getlogin()))
    # Run the qstat
    p = subprocess.Popen(cmd,stdout=subprocess.PIPE)
    p.wait()
    # Process the output: count lines
    nlines = 0
    for line in p.stdout:
        nlines += 1
    # Typical output is:
    # job-ID  prior   name       user         ...<snipped>...
    # ----------------------------------------...<snipped>...
    # 620848 -499.50000 qc       myname       ...<snipped>...
    # ...
    # i.e. 2 header lines then one line per job
    return nlines - 2

# RunPipeline: execute script for multiple sets of files
def RunPipeline(script,run_data,max_concurrent_jobs=4):
    """Execute script for multiple sets of files

    Given a script and a list of input file sets, script will be
    submitted to the cluster once for each set of files. No more
    than max_concurrent_jobs will be running for the user at any
    time.

    Arguments:
      script: name (including path) for pipeline script.
      run_data: a list consisting of tuples of files which will be
        supplied to the script as arguments.
      max_concurrent_jobs: the maximum number of jobs that the runner
        will submit to the cluster at any particular time (optional).
    """
    # For each pair of files, run the pipeline script
    for data in run_data:
        # Check if queue is "full"
        while QstatJobs() >= max_concurrent_jobs:
            # Wait a while before checking again
            logging.debug("Waiting for free space in queue...")
            time.sleep(poll_interval)
        # Submit
        logging.info("Submitting job: '%s %s'" % (script,data))
        job_id = QsubScript('qc',script,*data)
        logging.info("Job id = %s" % job_id)

def GetSolidDataFiles(dirn):
    """Return list of csfasta/qual file pairs in target directory
    """
    # Gather data files
    logging.debug("Collecting csfasta/qual file pairs in %s" % dirn)
    data_files = []
    all_files = os.listdir(data_dir)
    all_files.sort()

    # Look for csfasta and matching qual files
    for filen in all_files:
        logging.debug("Examining file %s" % filen)
        root = os.path.splitext(filen)[0]
        ext = os.path.splitext(filen)[1]
        if ext == ".qual":
            qual = filen
            # Match csfasta names which don't have "_QV" in them
            try:
                i = root.rindex('_QV')
                csfasta = root[:i]+root[i+3:]+".csfasta"
            except IndexError:
                # QV not in name, try to match whole name
                csfasta = root+".csfasta"
            if os.path.exists(os.path.join(data_dir,csfasta)):
                data_files.append((csfasta,qual))
            else:
                logging.critical("Unable to get csfasta for %s" % filen)
    # Done - return file pairs
    return data_files

def GetFastqFiles(dirn):
    """Return list of fastq files in target directory
    """
    # Gather data files
    logging.debug("Collecting fastq files in %s" % dirn)
    data_files = []
    all_files = os.listdir(data_dir)
    all_files.sort()

    # Look for csfasta and matching qual files
    for filen in all_files:
        logging.debug("Examining file %s" % filen)
        root = os.path.splitext(filen)[0]
        ext = os.path.splitext(filen)[1]
        if ext == ".fastq": data_files.append((filen,))
    # Done - return file list
    return data_files

#######################################################################
# Main program
#######################################################################

if __name__ == "__main__":
    # Initialise
    max_concurrent_jobs = 4
    poll_interval = 30
    max_total_jobs = 0
    logging_level = logging.INFO
    script = None
    data_dirs = []
    input_type = "solid"

    # Deal with command line
    if len(sys.argv) < 3:
        print "Usage: %s [OPTIONS] <script> <dir> [<dir> ...]" % \
            os.path.basename(sys.argv[0])
        print ""
        print "<script> : pipeline script file to execute"
        print "<dir>    : one or more directories holding SOLiD data"
        print "           By default, <script> will be executed for each"
        print "           csfasta/qual file pair in dir, using:"
        print "             <script> <csfasta> <qual>"
        print "           Use --input option to run e.g."
        print "             <script> <fastq> etc"
        print ""
        print "Options:"
        print "  --limit=<n>: queue no more than <n> jobs at one time"
        print "               (default %s)" % max_concurrent_jobs
        print "  --test=<n> : submit no more than <n> jobs in total"
        print "  --debug    : print debugging output while running"
        print "  --input=<type> : specify type of input for script"
        print "               Can be one of:"
        print "               solid = csfasta/qual file pair (default)"
        print "               fastq = fastq file"
        print
        sys.exit()

    # Collect command line options
    for arg in sys.argv[1:]:
        if arg.startswith("--limit="):
            # Set maximum number of jobs to queue at one time
            max_concurrent_jobs = int(arg.split('=')[1])
        elif arg.startswith("--debug"):
            # Set logging level to output debugging info
            logging_level = logging.DEBUG
        elif arg.startswith("--test="):
            # Run in test mode: limit the number of jobs
            # submitted
            max_total_jobs = int(arg.split('=')[1])
        elif arg.startswith("--input="):
            # Specify input type
            input_type = arg.split('=')[1]
        elif arg.startswith("--") and len(data_dirs) > 0:
            # Some option appeared after we started collecting
            # directories
            logging.error("Unexpected argument encountered: %s" % arg)
            sys.exit(1)
        else:
            if script is None:
                # Script name
                print "Script: %s" % arg
                if os.path.isabs(arg):
                    # Absolute path
                    if os.path.isfile(arg):
                        script = arg
                    else:
                        script = None
                else:
                    # Try relative to pwd
                    script = os.path.normpath(os.path.join(os.getcwd(),arg))
                    if not os.path.isfile(script):
                        # Try relative to directory for script
                        script = os.path.abspath(os.path.normpath(
                                os.path.join(os.path.dirname(sys.argv[0]),arg)))
                        if not os.path.isfile(script):
                            script = None
                if script is None:
                    logging.error("Script file not found: %s" % script)
                    sys.exit(1)
                print "Full path for script: %s" % script
            else:
                # Data directory
                print "Directory: %s" % arg
                dirn = os.path.abspath(arg)
                if not os.path.isdir(dirn):
                    logging.error("Not a directory: %s" % dirn)
                    sys.exit(1)
                data_dirs.append(dirn)

    # Set logging format and level
    logging.basicConfig(format='%(levelname)8s %(message)s')
    logging.getLogger().setLevel(logging_level)

    # Iterate over data directories
    for data_dir in data_dirs:

        print "Running %s on data in %s" % (script,data_dir)
        if input_type == "solid":
            run_data = GetSolidDataFiles(data_dir)
        elif input_type == "fastq":
            run_data = GetFastqFiles(data_dir)

        # Check there's something to run on
        if len(run_data) == 0:
            logging.error("No data files collected for %d" % data_dir)
            continue

        # Test mode: limit the total number of jobs that will be
        # submitted
        if max_total_jobs > 0:
            run_data = run_data[:max_total_jobs]

        # Relocate to the data dir
        os.chdir(data_dir)

        # Run the pipeline
        RunPipeline(script,run_data,max_concurrent_jobs)

    # Finished
    print "All pipelines finished"

