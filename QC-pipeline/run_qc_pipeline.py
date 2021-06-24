#!/usr/bin/env python
#
#     run_pipeline.py: run pipeline script on file sets
#     Copyright (C) University of Manchester 2011,2019,2021 Peter Briggs
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
import argparse

# Put .. onto Python search path for modules
SHARE_DIR = os.path.abspath(
    os.path.normpath(
        os.path.join(os.path.dirname(sys.argv[0]),'..')))
sys.path.append(SHARE_DIR)
from bcftbx import get_version
import bcftbx.JobRunner as JobRunner
import bcftbx.Pipeline as Pipeline

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
            os.chmod(os.path.join(job.working_dir,job.log),0o664)

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
        print("Sending email notification to %s re group '%s'" %
              (email_addr,group))
        SendEmail(subject,email_addr,report)
    else:
        print("Unable to send email notification: no address set")

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
    except Exception as ex:
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
    p = argparse.ArgumentParser(version="%(prog)s "+get_version(),
                                description=
                                "Execute SCRIPT on data in each directory "
                                "DIR. By default the SCRIPT is executed on "
                                "each CSFASTA/QUAL file pair found in DIR, "
                                "as 'SCRIPT CSFASTA QUAL'. Use the --input "
                                "option to run SCRIPT on different types of "
                                "data (e.g. FASTQ files). SCRIPT can be a "
                                "quoted string to include command line "
                                "options (e.g. 'run_solid2fastq.sh --gzip').")

    # Basic options
    group = p.add_argument_group("Basic Options")
    group.add_argument('--limit',action='store',dest='max_concurrent_jobs',
                       type=int,default=max_concurrent_jobs,
                       help="queue no more than MAX_CONCURRENT_JOBS at one "
                       "time (default %s)" % max_concurrent_jobs)
    group.add_argument('--input',action='store',dest='input_type',
                       default=input_type,
                       help="specify type of data to use as input for the "
                       "script. INPUT_TYPE can be one of: 'solid' "
                       "(CSFASTA/QUAL file pair, default), 'solid_paired_end'"
                       "(CSFASTA/QUAL_F3 and CSFASTA/QUAL_F5 quartet), "
                       "'fastq' (FASTQ file), 'fastqgz' (gzipped FASTQ file)")
    group.add_argument('--email',action='store',dest='email_addr',
                       default=None,
                       help="send email to EMAIL_ADDR when each stage of the "
                       "pipeline is complete")
    group.add_argument('--log-dir',action='store',dest='log_dir',
                       default=None,
                       help="put log files into LOG_DIR (defaults to cwd)")

    # Advanced options
    group = p.add_argument_group("Advanced Options")
    group.add_argument('--regexp',action='store',dest='pattern',
                       default=None,
                       help="regular expression to match input files against")
    group.add_argument('--runner',action='store',dest='runner',
                       default=runner_type,
                       help="specify how jobs are executed: ge = Grid Engine, "
                       "simple = use local system. Default is '%s'" %
                       runner_type)

    # Grid engine specific options
    group = p.add_argument_group("Grid Engine-specific options")
    group.add_argument('--queue',action='store',dest='ge_queue',
                       default=ge_queue,
                       help="explicitly specify Grid Engine queue to use")
    group.add_argument('--ge_args',action='store',dest='ge_args',
                       default=None,
                       help="explicitly specify additional arguments to use "
                       "for Grid Engine submission (e.g. '-j y')")

    # Developer options
    group = p.add_argument_group("Developer Options")
    group.add_argument('--debug',action='store_true',dest='debug',
                       default=False,
                       help="print debugging output")
    group.add_argument('--test',action='store',dest='max_total_jobs',
                       default=0,type=int,
                       help="submit no more than MAX_TOTAL_JOBS (otherwise "
                       "submit all jobs)")

    # Positional argumenrs
    p.add_argument('script',metavar="SCRIPT",
                   help="script file to execute")
    p.add_argument('dirs',metavar="DIR",nargs="+",
                   help="directory to execute SCRIPT in")

    # Deal with command line
    arguments = p.parse_args()

    # "Script" can consist of script name alone, or a script plus options
    script_args = arguments.script.split()
    # Script name
    print("Script: '%s'" % arguments.script)
    if os.path.isabs(script_args[0]):
        # Absolute path
        if os.path.isfile(script_args[0]):
            script = script_args[0]
        else:
            script = None
    else:
        # Try relative to pwd
        script = os.path.normpath(os.path.join(os.getcwd(),script_args[0]))
        if not os.path.isfile(script):
            # Try relative to directory for script
            script = os.path.abspath(os.path.normpath(
                os.path.join(os.path.dirname(sys.argv[0]),script_args[0])))
            if not os.path.isfile(script):
                script = None
    if script is None:
        logging.error("Script file not found: %s" % script)
        sys.exit(1)
    script_args = script_args[1:]
    print("Full path for script: %s" % script)
    if script_args:
        print("Additional script arguments:")
        for arg in script_args:
            print("\t%s" % arg)
    # Data directories
    for arg in arguments.dirs:
        print("Directory: %s" % arg)
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
    if arguments.debug:
        logging_level = logging.DEBUG
    else:
        logging_level = logging.INFO
    logging.basicConfig(format='%(levelname)8s %(message)s')
    logging.getLogger().setLevel(logging_level)

    # Set up job runner
    if arguments.runner == 'simple':
        runner = JobRunner.SimpleJobRunner(join_logs=True)
    elif arguments.runner == 'ge':
        if arguments.ge_args:
            ge_extra_args = str(arguments.ge_args).split(' ')
        else:
            ge_extra_args = None
        runner = JobRunner.GEJobRunner(queue=arguments.ge_queue,
                                       ge_extra_args=ge_extra_args)
    else:
        logging.error("Unknown job runner: '%s'" % arguments.runner)
        sys.exit(1)
    runner.set_log_dir(arguments.log_dir)

    # Set up and run pipeline
    pipeline = Pipeline.PipelineRunner(runner,
                                       max_concurrent_jobs=\
                                       arguments.max_concurrent_jobs,
                                       jobCompletionHandler=JobCleanup,
                                       groupCompletionHandler=\
                                       lambda group,jobs,email=\
                                       arguments.email_addr:
                                       SendReport(email,group,jobs))
    for data_dir in data_dirs:
        # Get for this directory
        print("Collecting data from %s" % data_dir)
        if arguments.input_type == "solid":
            pipeline_func = Pipeline.GetSolidDataFiles
        elif arguments.input_type == "solid_paired_end":
            pipeline_func = Pipeline.GetSolidPairedEndFiles
        elif arguments.input_type == "fastq":
            pipeline_func = Pipeline.GetFastqFiles
        elif arguments.input_type == "fastqgz":
            pipeline_func = Pipeline.GetFastqGzFiles
        else:
            logging.error("Unknown input type: '%s'" % arguments.input_type)
            sys.exit(1)
        run_data = pipeline_func(data_dir,pattern=arguments.pattern)
        # Add jobs to pipeline runner (up to limit of max_total_jobs)
        for data in run_data:
            if arguments.max_total_jobs > 0 and \
               pipeline.nWaiting() == arguments.max_total_jobs:
                print("Maximum number of jobs queued (%d)" %
                      arguments.max_total_jobs)
                break
            label = os.path.splitext(os.path.basename(data[0]))[0]
            group = os.path.basename(data_dir)
            # Set up argument list for script
            args = []
            if script_args:
                for arg in script_args:
                    args.append(arg)
            for arg in data:
                args.append(arg)
            pipeline.queueJob(data_dir,script,args,label=label,group=group)
    # Run the pipeline
    pipeline.run()

    # Finished
    if email_addr is not None:
        print("Sending email notification to %s" % arguments.email_addr)
        subject = "Pipeline completed: %s" % os.path.basename(script)
        SendEmail(subject,arguments.email_addr,pipeline.report())
    print("Finished")
