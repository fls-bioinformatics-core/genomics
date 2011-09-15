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
import Queue
import logging

#######################################################################
# Class definitions
#######################################################################

# Qstat: helper class for getting information from qstat
class Qstat:
    """Utility class for getting information from the qstat command.

    Provides basic functionality for getting information on running jobs
    from the GE 'qstat' command.
    """
    def __init__(self):
        pass

    def list(self,user=None):
        """Get list of job ids in the queue.
        """
        cmd = ['qstat']
        if user:
            cmd.extend(('-u',user))
        else:
            # Get current user name
            cmd.extend(('-u',os.getlogin()))
        # Run the qstat
        p = subprocess.Popen(cmd,stdout=subprocess.PIPE)
        p.wait()
        # Process the output: get job ids
        job_ids = []
        # Typical output is:
        # job-ID  prior   name       user         ...<snipped>...
        # ----------------------------------------...<snipped>...
        # 620848 -499.50000 qc       myname       ...<snipped>...
        # ...
        # i.e. 2 header lines then one line per job
        for line in p.stdout:
            try:
                if line.split()[0].isdigit():
                    job_ids.append(line.split()[0])
            except IndexError:
                pass
        return job_ids

    def njobs(self,user=None):
        """Return the number of jobs in the queue.
        """
        return len(self.list(user=user))

    def hasJob(self,job_id):
        """Check if the specified job id is in the queue.
        """
        return (job_id in self.list())

# QsubJob: container for a script run
class QsubJob:
    """Wrapper class for setting up, submitting and monitoring qsub scripts

    Set up a job by creating a QsubJob instance specifying the name, working directory,
    script file to execute, and arguments to be supplied to the script.

    The job is started by invoking QsubJob's 'start' method; its status can be checked
    with the 'isRunning' method, and terminated and resubmitted using the 'terminate' and
    'resubmit' methods respectively.

    Information about the job can also be accessed via its properties. The following
    properties record the original parameters supplied on instantiation:

      name
      working_dir
      script
      args

    Additional information is set once the job has started or stopped running:

      job_id      The id number for the running job set by GE
      log         The log file for the job (relative to working_dir)
      start_time  The start time (seconds since the epoch)
      end_time    The end time (seconds since the epoch)

    """
    def __init__(self,name,dirn,script,*args):
        """Create an instance of QsubJob.

        Arguments:
          name: name to give the running job (i.e. qsub -N)
          dirn: directory to run the script in (i.e. qsub -wd)
          script: script file to submit, either a full path, relative path to dirn, or
            must be on the user's PATH in the environment where GE jobs are executed
          args: arbitrary arguments to supply to the script when it is submitted via qsub
        """
        self.name = name
        self.working_dir = dirn
        self.script = script
        self.args = args
        self.job_id = None
        self.log = None
        self.submitted = False
        self.terminated = False
        self.start_time = None
        self.end_time = None
        self.home_dir = os.getcwd()
        self.__finished = False
        self.__qstat = Qstat()

    def start(self):
        """Submit the job to the GE queue
        """
        if not self.submitted and not self.__finished:
            self.job_id = QsubScript(self.name,self.working_dir,self.script,*self.args)
            self.submitted = True
            self.start_time = time.time()
            self.log = self.name+'.o'+self.job_id
            # Wait for evidence that the job has started
            logging.debug("Waiting for job to start")
            while not self.__qstat.hasJob(self.job_id) and not os.path.exists(self.log):
                time.sleep(5)
        logging.debug("Job %s started (%s)" % (self.job_id,
                                               time.asctime(time.localtime(self.start_time))))
        return self.job_id

    def terminate(self):
        """Terminate (qdel) a running job
        """
        if not self.isRunning():
            Qdeljob(self.job_id)
            self.terminated = True
            self.end_time = time.time()

    def resubmit(self):
        """Resubmit the job

        Terminates the job (if still running) and restarts"""
        # Terminate running job
        if self.isRunning():
            self.terminate()
            while self.isRunning():
                time.sleep(5)
        # Reset flags
        self.__finished = False
        self.submitted = False
        self.terminated = False
        self.start_time = None
        self.end_time = None
        # Resubmit
        return self.start()

    def isRunning(self):
        """Check if job is still running
        """
        if not self.submitted:
            return False
        if not self.__finished:
            if not self.__qstat.hasJob(self.job_id):
                self.end_time = time.time()
                self.__finished = True
        return not self.__finished

# PipelineRunner: class to set up and run multiple jobs
class PipelineRunner:
    """Class to run and manage multiple GE jobs.

    PipelineRunner enables multiple jobs to be queued via the 'queueJob' method. The
    pipeline is then started using the 'run' method - this submits each job in turn (while
    limiting the number in the GE queue to a specified maximum) and monitors when they
    finish:

    p = PipelineRunner()
    p.queueJob('/home/foo','foo.sh','bar.in')
    ...
    p.run()

    Currently it runs in 'blocking' mode, i.e. 'run' doesn't return until all jobs have been
    submitted and have completed.
    """
    def __init__(self,max_concurrent_jobs=4,poll_interval=30):
        """Create new PipelineRunner instance.

        Arguments:
          max_concurrent_jobs: maximum number of GE jobs that the script will allow
          poll_interval: time interval (in seconds) between checks on the queue status
        """
        # Parameters
        self.max_concurrent_jobs = max_concurrent_jobs
        self.poll_interval = poll_interval
        # Queue of jobs to run
        self.jobs = Queue.Queue()
        # Subset that are currently running
        self.running = []
        # Subset that have completed
        self.completed = []
        # Local qstat instance for monitoring
        self.qstat = Qstat()

    def queueJob(self,working_dir,script,*args):
        """Add a job to the pipeline.

        The job will be queued and executed once the pipeline's 'run' method has been
        executed.

        Arguments:
          working_dir: directory to run the job in
          script: script file to run
          args: arguments to be supplied to the script at run time
        """
        job_name = os.path.splitext(os.path.basename(script))[0]
        self.jobs.put(QsubJob(job_name,working_dir,script,*args))
        logging.debug("Added job: now %d jobs in pipeline" % self.jobs.qsize())

    def nQueued(self):
        """Return the number of jobs still to be submitted to the GE queue
        """
        return self.jobs.qsize()

    def nRunning(self):
        """Return the number of jobs currently running in the GE queue
        """
        return len(self.running)

    def nCompleted(self):
        """Return the number of jobs that have completed
        """
        return len(self.completed)

    def run(self):
        """Execute the jobs in the pipeline

        Each job previously added to the pipeline by 'queueJob' will be submitted to the
        GE queue and checked for termination.

        'run' operates in 'blocking' mode, so it doesn't return until all jobs have been
        submitted and have finished executing.
        """
        logging.debug("PipelineRunner: started")
        while not self.jobs.empty() or self.nRunning() > 0:
            # Flag to report updated status
            updated_status = False
            # Look for running jobs that have completed
            for job in self.running[::-1]:
                if not job.isRunning():
                    # Job has completed
                    self.running.remove(job)
                    self.completed.append(job)
                    updated_status = True
                    print "Job has completed: %s: %s %s (%s)" % (
                        job.job_id,
                        job.name,
                        os.path.basename(job.working_dir),
                        time.asctime(time.localtime(job.end_time)))
                    # Set the permissions on the output log file to rw-rw-r--
                    if os.path.exists(os.path.join(job.working_dir,job.log)):
                        os.chmod(os.path.join(job.working_dir,job.log),0664)
            # Submit new jobs to GE queue
            while not self.jobs.empty() and self.qstat.njobs() < self.max_concurrent_jobs:
                next_job = self.jobs.get()
                next_job.start()
                self.running.append(next_job)
                updated_status = True
                print "Job has started: %s: %s %s (%s)" % (
                    next_job.job_id,
                    next_job.name,
                    os.path.basename(next_job.working_dir),
                    time.asctime(time.localtime(next_job.start_time)))
                if self.jobs.empty():
                    logging.debug("PipelineRunner: all jobs now submitted")
            # Report
            if updated_status:
                print "Currently %d jobs waiting, %d running, %d finished" % \
                    (self.nQueued(),self.nRunning(),self.nCompleted())
            # If there are still running jobs then wait
            if self.nRunning() > 0:
                time.sleep(self.poll_interval)
        # Pipeline has finished
        print "Pipeline completed"
        return

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
def QsubScript(name,working_dir,script,*args):
    """Submit a script or command to the cluster via 'qsub'
    """
    # 
    logging.debug("QsubScript: submitting job")
    logging.debug("QsubScript: name       :%s" % name)
    logging.debug("QsubScript: working_dir: %s" % working_dir)
    logging.debug("QsubScript: script     : %s" % script)
    logging.debug("QsubScript: args       : %s" % str(args))
    # Build command to be submitted
    cmd_args = [script]
    cmd_args.extend(args)
    cmd = ' '.join(cmd_args)
    # Build qsub command to submit it
    qsub = ['qsub','-b','y','-V','-N',name]
    if not working_dir:
        qsub.append('-cwd')
    else:
        qsub.extend(('-wd',working_dir))
    qsub.append(cmd)
    logging.debug("QsubScript: qsub command: %s" % qsub)
    # Run the qsub job in the current directory
    # This shouldn't be significant
    cwd = os.getcwd()
    logging.debug("QsubScript: executing in %s" % cwd)
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

# QdelJob: delete a job from the queue
def QdelJob(job_id):
    """Remove a job from the GE queue using 'qdel'
    """
    logging.debug("QdelJob: deleting job")
    qdel=('qdel',job_id)
    p = subprocess.Popen(qdel)
    p.wait()

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
    email_addr = None

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
        print "  --email=<address>: send an email to <address> when the"
        print "               pipeline has completed."
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
        elif arg.startswith("--email="):
            email_addr = arg.split('=')[1]
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

    # Set up and run pipeline
    pipeline = PipelineRunner(max_concurrent_jobs=max_concurrent_jobs)
    for data_dir in data_dirs:
        # Get for this directory
        print "Collecting data from %s" % data_dir
        if input_type == "solid":
            run_data = GetSolidDataFiles(data_dir)
        elif input_type == "fastq":
            run_data = GetFastqFiles(data_dir)
        # Add jobs to pipeline runner (up to limit of max_total_jobs)
        for data in run_data:
            pipeline.queueJob(data_dir,script,*data)
            if max_total_jobs > 0 and pipeline.nQueued() == max_total_jobs:
                print "Maximum number of jobs queued (%d)" % max_total_jobs
                break
    # Run the pipeline
    pipeline.run()

    # Finished
    if email_addr is not None:
        print "Sending email notification to %s" % email_addr
        subject = "QC pipeline completed"
        message = "Pipeline finished at %s\n\n" % time.asctime()
        for data_dir in data_dirs:
            message += "\t%s\n" % data_dir
        message += "\nRan %d jobs:\n\n" % pipeline.nCompleted()
        for job in pipeline.completed:
            message += "\t%s\t%s\t%s\t%.1fs\n" % (job.job_id,
                                              job.name,
                                              job.working_dir,
                                              (job.end_time - job.start_time))
        SendEmail(subject,email_addr,message)
    print "Finished"
