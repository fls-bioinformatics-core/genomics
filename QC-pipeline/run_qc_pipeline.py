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
import logging
import subprocess

# Put ../share onto Python search path for modules
SHARE_DIR = os.path.abspath(
    os.path.normpath(
        os.path.join(os.path.dirname(sys.argv[0]),'..','share')))
sys.path.append(SHARE_DIR)
try:
    import JobRunner
    import Pipeline
except ImportError, ex:
    print "Error importing modules: %s" % ex
    print "Check PYTHONPATH"
    sys.exit(1)

#######################################################################
# Module Functions
#######################################################################

# SendEmail: send an email message via mutt
def SendEmail(subject,recipient,message):
    """Send an email message via the 'mutt' client
    """
    p = subprocess.Popen(('mutt','-s',subject,recipient),
                         stdin=subprocess.PIPE)
    p.stdin.write(message)
    p.stdin.close()
    p.wait()
    return

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
    email_addr = None
    ge_queue = None
    use_simple_runner = False

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
        print "Basic Options:"
        print "  --limit=<n>: queue no more than <n> jobs at one time"
        print "               (default %s)" % max_concurrent_jobs
        print "  --queue=<name>: explicitly specify GE queue to use"
        print "  --input=<type> : specify type of input for script"
        print "               Can be one of:"
        print "               solid = csfasta/qual file pair (default)"
        print "               fastq = fastq file"
        print "  --email=<address>: send an email to <address> when the"
        print "               pipeline has completed."
        print
        print "Advanced Options:"
        print "  --test=<n> : submit no more than <n> jobs in total"
        print "  --runner=<runner>: specify how jobs are executed"
        print "               Can be one of:"
        print "               ge = use Grid Engine (default)"
        print "               simple = use local system"
        print "  --debug    : print debugging output while running"
        print
        sys.exit()

    # Collect command line options
    for arg in sys.argv[1:]:
        if arg.startswith("--limit="):
            # Set maximum number of jobs to queue at one time
            max_concurrent_jobs = int(arg.split('=')[1])
        elif arg.startswith("--queue="):
            # Name of GE queue to use
            ge_queue = arg.split('=')[1]
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
        elif arg.startswith("--email="):
            email_addr = arg.split('=')[1]
        elif arg.startswith("--runner="):
            use_simple_runner = (arg.split('=')[1] == 'simple')
        elif arg.startswith("--") and len(data_dirs) > 0:
            # Some option appeared after we started collecting directories
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
                # Check for duplicates
                if dirn not in data_dirs:
                    data_dirs.append(dirn)
                else:
                    logging.warning("Directory '%s' already specified" % dirn)

    # Set logging format and level
    logging.basicConfig(format='%(levelname)8s %(message)s')
    logging.getLogger().setLevel(logging_level)

    # Set up job runner
    if use_simple_runner:
        runner = JobRunner.SimpleJobRunner()
    else:
        runner = JobRunner.GEJobRunner(queue=ge_queue)

    # Set up and run pipeline
    pipeline = Pipeline.PipelineRunner(runner,max_concurrent_jobs=max_concurrent_jobs)
    for data_dir in data_dirs:
        # Get for this directory
        print "Collecting data from %s" % data_dir
        if input_type == "solid":
            run_data = Pipeline.GetSolidDataFiles(data_dir)
        elif input_type == "fastq":
            run_data = Pipeline.GetFastqFiles(data_dir)
        # Add jobs to pipeline runner (up to limit of max_total_jobs)
        for data in run_data:
            pipeline.queueJob(data_dir,script,data)
            if max_total_jobs > 0 and pipeline.nWaiting() == max_total_jobs:
                print "Maximum number of jobs queued (%d)" % max_total_jobs
                break
    # Run the pipeline
    pipeline.run()

    # Finished
    if email_addr is not None:
        print "Sending email notification to %s" % email_addr
        subject = "QC pipeline completed"
        SendEmail(subject,email_addr,pipeline.report())
    print "Finished"
