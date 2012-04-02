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
import time
import optparse

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

def JobCleanup(job):
    """Perform clean-up operations when job has completed

    This is a callback function that should be invoked by the pipeline
    runner when a job finishes, to do things like setting the correct
    permissions on the output log files.

    Arguments:
      job: a Pipeline.Job instance for the finished job.
    """
    # Set the permissions on the output log file to rw-rw-r--
    if job.log:
        if os.path.exists(os.path.join(job.working_dir,job.log)):
            os.chmod(os.path.join(job.working_dir,job.log),0664)

def SendReport(email_addr,group,job_list):
    """Send an email notification/report when a job group has completed

    This is a callback function that should be invoked by the pipeline
    runner when a group of jobs finishes. It creates a report on the
    finished jobs and emails that to the supplied address.

    Arguments:
      email_addr: an email address to send the report to, or None
      group: name of the completed group
      job_list: list of Pipeline.Job instances for the jobs in the
        completed group
    """
    if email_addr is not None:
        subject = "Pipeline completed for %s" % group
        report = "Group completed %s\n" % time.asctime()
        report += "\n%d jobs completed:\n" % len(job_list)
        for job in job_list:
            report += "\t%s\t%s\t%s\t%.1fs\t[%s]\n" % (job.label,
                                                       job.log,
                                                       job.working_dir,
                                                       (job.end_time - job.start_time),
                                                       job.status())
        print "Sending email notification to %s re group '%s'" % (email_addr,group)
        SendEmail(subject,email_addr,report)
    else:
        print "Unable to send email notification: no address set"

# SendEmail: send an email message via mutt
def SendEmail(subject,recipient,message):
    """Send an email message via the 'mutt' client

    Arguments:
      subject: the subject line for the message
      recipicient: email address to send the message to
      message: text to be put in the message body

    Returns:
      If the send operation was successful then returns True, otherwise
      returns False.
    """
    try:
        p = subprocess.Popen(('mutt','-s',subject,recipient),
                             stdin=subprocess.PIPE)
        p.stdin.write(message)
        p.stdin.close()
        p.wait()
        return True
    except Exception, ex:
        logging.error("SendMail failed to send email via mutt")
        logging.error("Exception: %s" % ex)
        return False

#######################################################################
# Main program
#######################################################################

if __name__ == "__main__":
    # Initialise
    max_concurrent_jobs = 4
    poll_interval = 30
    max_total_jobs = 0
    script = None
    data_dirs = []
    input_type = "solid"
    email_addr = None
    ge_queue = None
    runner_type = "ge"

    # Set up command line parser
    p = optparse.OptionParser(usage="%prog [options] SCRIPT DIR [ DIR ...]",
                              description=
                              "Execute SCRIPT on data in each directory DIR. By default"
                              "the SCRIPT is executed on each CSFASTA/QUAL file pair "
                              "found in DIR, as 'SCRIPT CSFASTA QUAL. Use the --input "
                              "option to run SCRIPT on different types of data (e.g. "
                              "FASTQ files.")

    # Basic options
    group = optparse.OptionGroup(p,"Basic Options")
    group.add_option('--limit',action='store',dest='max_concurrent_jobs',type='int',
                     default=max_concurrent_jobs,
                     help="queue no more than MAX_CONCURRENT_JOBS at one time (default %s)"
                     % max_concurrent_jobs)
    group.add_option('--queue',action='store',dest='ge_queue',default=ge_queue,
                     help="explicitly specify Grid Engine queue to use")
    group.add_option('--input',action='store',dest='input_type',default=input_type,
                     help="specify type of data to use as input for the script. INPUT_TYPE "
                     "can be one of: 'solid' (CSFASTA/QUAL file pair, default), 'fastq' "
                     "(FASTQ file)")
    group.add_option('--email',action='store',dest='email_addr',default=None,
                     help="send email to EMAIL_ADDR when each stage of the pipeline is "
                     "complete")
    p.add_option_group(group)

    # Advanced options
    group = optparse.OptionGroup(p,"Advanced Options")
    group.add_option('--test',action='store',dest='max_total_jobs',default=0,type='int',
                     help="submit no more than MAX_TOTAL_JOBS (otherwise submit all jobs)")
    group.add_option('--runner',action='store',dest='runner',default=runner_type,
                     help="specify how jobs are executed: ge = Grid Engine, drmma = Grid "
                     "Engine via DRMAA interface, simple = use local system. Default is "
                     "'%s'" % runner_type)
    group.add_option('--debug',action='store_true',dest='debug',default=False,
                     help="print debugging output")
    p.add_option_group(group)

    # Deal with command line
    options,arguments = p.parse_args()

    # Check arguments
    if len(arguments) < 2:
        p.error("Takes at least two arguments: script and one or more directories")
    else:
        # Script name
        arg = arguments[0]
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
        # Data directories
        for arg in arguments[1:]:
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
    if options.debug:
        logging_level = logging.DEBUG
    else:
        logging_level = logging.INFO
    logging.basicConfig(format='%(levelname)8s %(message)s')
    logging.getLogger().setLevel(logging_level)

    # Set up job runner
    if options.runner == 'simple':
        runner = JobRunner.SimpleJobRunner()
    elif options.runner == 'ge':
        runner = JobRunner.GEJobRunner(queue=ge_queue)
    elif options.runner == 'drmaa':
        runner = JobRunner.DRMAAJobRunner(queue=ge_queue)
    else:
        logging.error("Unknown job runner: '%s'" % options.runner)
        sys.exit(1)

    # Set up and run pipeline
    pipeline = Pipeline.PipelineRunner(runner,max_concurrent_jobs=options.max_concurrent_jobs,
                                       jobCompletionHandler=JobCleanup,
                                       groupCompletionHandler=lambda group,jobs,
                                       email=options.email_addr: SendReport(email,group,jobs))
    for data_dir in data_dirs:
        # Get for this directory
        print "Collecting data from %s" % data_dir
        if options.input_type == "solid":
            run_data = Pipeline.GetSolidDataFiles(data_dir)
        elif options.input_type == "fastq":
            run_data = Pipeline.GetFastqFiles(data_dir)
        else:
            logging.error("Unknown input type: '%s'" % options.input_type)
            sys.exit(1)
        # Add jobs to pipeline runner (up to limit of max_total_jobs)
        for data in run_data:
            if options.max_total_jobs > 0 and pipeline.nWaiting() == options.max_total_jobs:
                print "Maximum number of jobs queued (%d)" % options.max_total_jobs
                break
            label = os.path.splitext(os.path.basename(data[0]))[0]
            group = os.path.basename(data_dir)
            pipeline.queueJob(data_dir,script,data,label=label,group=group)
    # Run the pipeline
    pipeline.run()

    # Finished
    if email_addr is not None:
        print "Sending email notification to %s" % options.email_addr
        subject = "Pipeline completed: %s" % os.path.basename(script)
        SendEmail(subject,options.email_addr,pipeline.report())
    print "Finished"
