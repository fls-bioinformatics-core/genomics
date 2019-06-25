#!/usr/bin/env python
#
#     Pipeline.py: classes for running scripts iteratively
#     Copyright (C) University of Manchester 2011-2019 Peter Briggs
#
########################################################################
#
# Pipeline.py
#
#########################################################################

"""
Classes for running scripts iteratively over a collection of data files.

The essential classes are:

* Job: wrapper for setting up, submitting and monitoring running
  scripts
* PipelineRunner: queue and run script multiple times on standard set
  of inputs
* SolidPipelineRunner: subclass of PipelineRunner specifically for
  running on SOLiD data (i.e. pairs of csfasta/qual files)

There are also some useful methods:

* GetSolidDataFiles: collect csfasta/qual file pairs from a specific
  directory
* GetSolidPairedEndFile: collect csfasta/qual file pairs for paired
  end data
* GetFastqFiles: collect fastq files from a specific directory
* GetFastqGzFiles: collect gzipped fastq files

The PipelineRunners depend on the JobRunner instances (created from
classes in the JobRunner module) to interface with the job management
system. So typical usage might look like:

>>> import JobRunner
>>> import Pipeline
>>> runner = JobRunner.GEJobRunner() # to use Grid Engine
>>> pipeline = Pipeline.PipelineRunner(runner)
>>> pipeline.queueJob(...)
>>> pipeline.run()

"""

#######################################################################
# Module metadata
#######################################################################

__version__ = "0.1.5"

#######################################################################
# Import modules that this module depends on
#######################################################################

import sys
import os
import re
import time
import Queue
import logging

#######################################################################
# Class definitions
#######################################################################

# Job: container for a script run
class Job(object):
    """Wrapper class for setting up, submitting and monitoring running scripts

    Set up a job by creating a Job instance specifying the name, working directory,
    script file to execute, and arguments to be supplied to the script.

    The job is started by invoking the 'start' method; its status can be checked
    with the 'isRunning' method, and terminated and restarted using the 'terminate'
    and 'restart' methods respectively.

    Information about the job can also be accessed via its properties. The following
    properties record the original parameters supplied on instantiation:

      name
      working_dir
      script
      args
      label
      group_label

    Additional information is set once the job has started or stopped running:

      job_id      The id number for the running job returned by the JobRunner
      log         The log file for the job (relative to working_dir)
      start_time  The start time (seconds since the epoch)
      end_time    The end time (seconds since the epoch)
      exit_status The exit code from the command that was run (integer, or None)

    The Job class uses a JobRunner instance (which supplies the necessary methods for
    starting, stopping and monitoring) for low-level job interactions.
    """
    def __init__(self,runner,name,dirn,script,args,label=None,group=None):
        """Create an instance of Job.

        Arguments:
          runner: a JobRunner instance supplying job control methods
          name: name to give the running job
          dirn: directory to run the script in
          script: script file to submit, either a full path, relative path to dirn, or
            must be on the user's PATH in the environment where jobs are executed
          args: Python list with the arguments to supply to the script when it is
            submitted
          label: (optional) arbitrary string to use as an identifier for the job
          group: (optional) arbitrary string to use as a 'group' identifier;
            assign the same 'group' label to multiple jobs to indicate they're
            related
        """
        self.name = name
        self.working_dir = dirn
        self.script = script
        self.args = args
        self.label = label
        self.group_label = group
        self.job_id = None
        self.log = None
        self.submitted = False
        self.failed = False
        self.terminated = False
        self.start_time = None
        self.end_time = None
        self.exit_status = None
        self.home_dir = os.getcwd()
        self.__finished = False
        self.__runner = runner
        # Time interval to use when checking for job start (seconds)
        # Can be floating point number e.g. 0.1 (= 100ms)
        self.__poll_interval = 1
        # Time out period to use before giving up on job submission
        # (seconds)
        self.__timeout = 3600

    def start(self):
        """Start the job running

        Returns:
          Id for job
        """
        if not self.submitted and not self.__finished:
            self.job_id = self.__runner.run(self.name,self.working_dir,self.script,self.args)
            self.submitted = True
            self.start_time = time.time()
            if self.job_id is None:
                # Failed to submit correctly
                logging.warning("Job submission failed")
                self.failed = True
                self.__finished = True
                self.end_time = self.start_time
                return self.job_id
            self.submitted = True
            self.start_time = time.time()
            self.log = self.__runner.logFile(self.job_id)
            # Wait for evidence that the job has started
            logging.debug("Waiting for job to start")
            time_waiting = 0
            while not self.__runner.isRunning(self.job_id) and not os.path.exists(self.log):
                time.sleep(self.__poll_interval)
                time_waiting += self.__poll_interval
                if time_waiting > self.__timeout:
                    # Waited too long for job to start, give up
                    logging.error("Timed out waiting for job to start")
                    self.failed = True
                    self.__finished = True
                    ##self.__end_time = self.start_time
                    self.update()
                    return self.job_id
        logging.debug("Job %s started (%s)" % (self.job_id,
                                               time.asctime(time.localtime(self.start_time))))
        # Also report queue (for GE jobs only)
        try:
            logging.debug("Queue: %s" % self.__runner.queue(self.job_id))
        except AttributeError:
            pass
        return self.job_id

    def terminate(self):
        """Terminate a running job
        """
        if self.isRunning():
            self.__runner.terminate(self.job_id)
            self.terminated = True
            self.update()
            ##self.__end_time = time.time()
            ##self.__exit_status = self.__runner.exit_status(self.job_id)

    def restart(self):
        """Restart the job

        Terminates the job (if still running) and restarts"""
        # Terminate running job
        if self.isRunning():
            self.terminate()
            while self.isRunning():
                time.sleep(self.__poll_interval)
        # Reset flags
        self.__finished = False
        self.submitted = False
        self.terminated = False
        self.start_time = None
        self.end_time = None
        self.exit_status = None
        # Resubmit
        return self.start()

    def isRunning(self):
        """Check if job is still running
        """
        if not self.submitted:
            return False
        self.update()
        return not self.__finished

    def errorState(self):
        """Check if the job is in an error state
        """
        return self.__runner.errorState(self.job_id)

    def status(self):
        """Return descriptive string indicating job status
        """
        if self.__finished:
            if self.terminated:
                return "Terminated"
            else:
                return "Finished"
        elif self.submitted:
            if self.terminated:
                return "Running pending termination"
            else:
                return "Running"
        else:
            return "Waiting"

    def update(self):
        """Update status of job
        """
        if not self.__finished:
            if not self.__runner.isRunning(self.job_id):
                self.__finished = True
                self.end_time = time.time()
                self.exit_status = self.__runner.exit_status(self.job_id)

    def wait(self):
        """Wait for job to complete

        Block calling process until the job has finished running.
        """
        while self.isRunning():
            time.sleep(1)
        return

    @property
    def runner(self):
        """Return the JobRunner instance associated with the Job

        """
        return self.__runner

# PipelineRunner: class to set up and run multiple jobs
class PipelineRunner(object):
    """Class to run and manage multiple concurrent jobs.

    PipelineRunner enables multiple jobs to be queued via the 'queueJob' method. The
    pipeline is then started using the 'run' method - this starts each job up to a
    a specified maximum of concurrent jobs, and then monitors their progress. As jobs
    finish, pending jobs are started until all jobs have completed.

    Example usage:

    >>> p = PipelineRunner()
    >>> p.queueJob('/home/foo','foo.sh','bar.in')
    ... Queue more jobs ...
    >>> p.run()

    By default the pipeline runs in 'blocking' mode, i.e. 'run' doesn't return until all
    jobs have been submitted and have completed; see the 'run' method for details of
    how to operate the pipeline in non-blocking mode.

    The invoking subprogram can also specify functions that will be called when a job
    completes ('jobCompletionHandler'), and when a group completes
    ('groupCompletionHandler'). These can perform any specific actions that are required
    such as sending notification email, setting file ownerships and permissions etc.
    """
    def __init__(self,runner,max_concurrent_jobs=4,poll_interval=30,jobCompletionHandler=None,
                 groupCompletionHandler=None):
        """Create new PipelineRunner instance.

        Arguments:
          runner: a JobRunner instance
          max_concurrent_jobs: maximum number of jobs that the script will allow to run
            at one time (default = 4)
          poll_interval: time interval (in seconds) between checks on the queue status
            (only used when pipeline is run in 'blocking' mode)
        """
        # Parameters
        self.__runner = runner
        self.max_concurrent_jobs = max_concurrent_jobs
        self.poll_interval = poll_interval
        # Groups
        self.groups = []
        self.njobs_in_group = {}
        # Queue of jobs to run
        self.jobs = Queue.Queue()
        # Subset that are currently running
        self.running = []
        # Subset that have completed
        self.completed = []
        # Callback functions
        self.handle_job_completion = jobCompletionHandler
        self.handle_group_completion = groupCompletionHandler

    def queueJob(self,working_dir,script,script_args,label=None,group=None):
        """Add a job to the pipeline.

        The job will be queued and executed once the pipeline's 'run' method has been
        executed.

        Arguments:
          working_dir: directory to run the job in
          script: script file to run
          script_args: arguments to be supplied to the script at run time
          label: (optional) arbitrary string to use as an identifier in the job name
          group: (optional) arbitrary string to use as a 'group' identifier;
            assign the same 'group' label to multiple jobs to indicate they're
            related
        """
        job_name = os.path.splitext(os.path.basename(script))[0]+'.'+str(label)
        if group:
            if group not in self.groups:
                # New group label
                self.groups.append(group)
                self.njobs_in_group[group] = 1
            else:
                self.njobs_in_group[group] += 1
        self.jobs.put(Job(self.__runner,job_name,working_dir,script,script_args,
                          label,group))
        logging.debug("Added job: now %d jobs in pipeline" % self.jobs.qsize())

    def nWaiting(self):
        """Return the number of jobs still waiting to be started
        """
        return self.jobs.qsize()

    def nRunning(self):
        """Return the number of jobs currently running
        """
        return len(self.running)

    def nCompleted(self):
        """Return the number of jobs that have completed
        """
        return len(self.completed)

    def isRunning(self):
        """Check whether the pipeline is still running

        Returns True if the pipeline is still running (i.e. has either
        running jobs, waiting jobs or both) and False otherwise.
        """
        # First update the pipeline status
        self.update()
        # Return the status
        return (self.nWaiting() > 0 or self.nRunning() > 0)

    def run(self,blocking=True):
        """Execute the jobs in the pipeline

        Each job previously added to the pipeline by 'queueJob' will be
        started and checked periodically for termination.

        By default 'run' operates in 'blocking' mode, so it doesn't return
        until all jobs have been submitted and have finished executing.

        To run in non-blocking mode, set the 'blocking' argument to False.
        In this mode the pipeline starts and returns immediately; it is
        the responsibility of the calling subprogram to then periodically
        check the status of the pipeline, e.g.

        >>> p = PipelineRunner()
        >>> p.queueJob('/home/foo','foo.sh','bar.in')
        >>> p.run()
        >>> while p.isRunning():
        >>>     time.sleep(30)
        """
        logging.debug("PipelineRunner: started")
        logging.debug("Blocking mode : %s" % blocking)
        # Report set up
        print("Initially %d jobs waiting, %d running, %d finished" %
              (self.nWaiting(),self.nRunning(),self.nCompleted()))
        # Initial update sets the jobs running
        self.update()
        if blocking:
            while self.isRunning():
                # Pipeline is still executing so wait
                time.sleep(self.poll_interval)
            # Pipeline has finished
            print("Pipeline completed")

    def update(self):
        """Update the pipeline

        The 'update' method checks and updates the status of running jobs,
        and submits any waiting jobs if space is available.
        """
        # Flag to report updated status
        updated_status = False
        # Look for running jobs that have completed
        for job in self.running[::-1]:
            if not job.isRunning():
                # Job has completed
                self.running.remove(job)
                self.completed.append(job)
                updated_status = True
                print("Job has completed: %s: %s %s (%s)" % (
                    job.job_id,
                    job.name,
                    os.path.basename(job.working_dir),
                    time.asctime(time.localtime(job.end_time))))
                # Invoke callback on job completion
                if self.handle_job_completion:
                    self.handle_job_completion(job)
                # Check for completed group
                if job.group_label is not None:
                    jobs_in_group = []
                    for check_job in self.completed:
                        if check_job.group_label == job.group_label:
                            jobs_in_group.append(check_job)
                    if self.njobs_in_group[job.group_label] == len(jobs_in_group):
                        # All jobs in group have completed
                        print("Group '%s' has completed" % job.group_label)
                        # Invoke callback on group completion
                        if self.handle_group_completion:
                            self.handle_group_completion(job.group_label,jobs_in_group)
            else:
                # Job is running, check it's not in an error state
                if job.errorState():
                    # Terminate jobs in error state
                    logging.warning("Terminating job %s in error state" % job.job_id)
                    job.terminate()
        # Submit new jobs to GE queue
        while not self.jobs.empty() and self.nRunning() < self.max_concurrent_jobs:
            next_job = self.jobs.get()
            next_job.start()
            self.running.append(next_job)
            updated_status = True
            print("Job has started: %s: %s %s (%s)" % (
                next_job.job_id,
                next_job.name,
                os.path.basename(next_job.working_dir),
                time.asctime(time.localtime(next_job.start_time))))
            if self.jobs.empty():
                logging.debug("PipelineRunner: all jobs now submitted")
        # Report
        if updated_status:
            print("Currently %d jobs waiting, %d running, %d finished" %
                  (self.nWaiting(),self.nRunning(),self.nCompleted()))

    def report(self):
        """Return a report of the pipeline status
        """
        # Pipeline status
        if self.nRunning() > 0:
            status = "RUNNING"
        elif self.nWaiting() > 0:
            status = "WAITING"
        else:
            status = "COMPLETED"
        report = "Pipeline status at %s: %s\n\n" % (time.asctime(),status)
        # Report directories
        dirs = []
        for job in self.completed:
            if job.working_dir not in dirs:
                dirs.append(job.working_dir)
        for dirn in dirs:
            report += "\t%s\n" % dirn
        # Report jobs waiting
        if self.nWaiting() > 0:
            report += "\n%d jobs waiting to run\n" % self.nWaiting()
        # Report jobs running
        if self.nRunning() > 0:
            report += "\n%d jobs running:\n" % self.nRunning()
            for job in self.running:
                report += "\t%s\t%s\t%s\n" % (job.label,job.log,job.working_dir)
        # Report completed jobs
        if self.nCompleted() > 0:
            report += "\n%d jobs completed:\n" % self.nCompleted()
            for job in self.completed:
                report += "\t%s\t%s\t%s\t%.1fs\t[%s]\n" % (job.label,
                                                           job.log,
                                                           job.working_dir,
                                                           (job.end_time - job.start_time),
                                                           job.status())
        return report

    def __del__(self):
        """Deal with deletion of the pipeline

        If the pipeline object is deleted while still running
        then terminate all running jobs.

        """
        # Empty the queue
        while not self.jobs.empty():
            self.jobs.get()
        # Terminate the running jobs
        for job in self.running:
            logging.debug("Terminating job %s" % job.job_id)
            print("Terminating job %s" % job.job_id)
            try:
                job.terminate()
            except Exception, ex:
                logging.error("Failed to terminate job %s: %s" % (job.job_id,ex))

class SolidPipelineRunner(PipelineRunner):
    """Class to run and manage multiple jobs for Solid data pipelines

    Subclass of PipelineRunner specifically for dealing with scripts
    that take Solid data (i.e. csfasta/qual file pairs).

    Defines the addDir method in addition to all methods already defined
    in the base class; use this method one or more times to specify
    directories with data to run the script on. The SOLiD data file pairs
    in each specified directory will be located automatically.

    For example:

    solid_pipeline = SolidPipelineRunner('qc.sh')
    solid_pipeline.addDir('/path/to/datadir')
    solid_pipeline.run()
    """
    def __init__(self,runner,script,max_concurrent_jobs=4,poll_interval=30):
        PipelineRunner.__init__(self,runner)
        self.script = script

    def addDir(self,dirn):
        logging.debug("Add dir: %s" % dirn)
        run_data = GetSolidDataFiles(dirn)
        for data in run_data:
            self.queueJob(dirn,self.script,data)

#######################################################################
# Module Functions
#######################################################################

def GetSolidDataFiles(dirn,pattern=None,file_list=None):
    """Return list of csfasta/qual file pairs in target directory

    Note that files with names ending in '_T_F3' will be rejected
    as these are assumed to come from the preprocess filtering stage.

    Optionally also specify a regular expression pattern that file
    names must also match in order to be included.

    Arguments:
      dirn: name/path of directory to look for files in
      pattern: optional, regular expression pattern to filter names with
      file_list: optional, a list of file names to use instead of
       fetching a list of files from the specified directory

    Returns:
      List of tuples consisting of two csfasta-qual file pairs (F3 and F5).

    """
    data_files = []
    if file_list is not None:
        # Used supplied file list
        logging.debug("Ignoring dirn argument and using supplied file list")
        all_files = file_list
    else:
        # Check directory exists
        if not os.path.isdir(dirn):
            logging.error("'%s' not a directory: unable to collect SOLiD files" % dirn)
            return []
        # Gather data files
        logging.debug("Collecting csfasta/qual file pairs in %s" % dirn)
        all_files = os.listdir(dirn)
    all_files.sort()
    # Regular expression pattern
    if pattern is not None:
        regex = re.compile(pattern)
    # Look for csfasta and matching qual files
    for filen in all_files:
        logging.debug("Examining file %s" % filen)
        root = os.path.splitext(filen)[0]
        ext = os.path.splitext(filen)[1]
        if ext == ".qual":
            qual = filen
            # Reject names ending with "_T_F3"
            try:
                i = root.rindex('_T_F3')
                logging.debug("Rejecting %s" % qual)
                continue
            except ValueError:
                # Name is okay, ignore
                pass
            # Match csfasta names which don't have "_QV" in them
            try:
                i = root.rindex('_QV')
                csfasta = root[:i]+root[i+3:]+".csfasta"
            except ValueError:
                # QV not in name, try to match whole name
                csfasta = root+".csfasta"
            if csfasta in all_files:
                # If a regex pattern is specified then also filter on it
                if pattern is None or regex.search(csfasta):
                    data_files.append((csfasta,qual))
            else:
                logging.critical("Unable to get csfasta for %s" % filen)
    # Done - return file pairs
    return data_files

def GetSolidPairedEndFiles(dirn,pattern=None,file_list=None):
    """Return list of csfasta/qual file pairs for paired end data

    Optionally also specify a regular expression pattern that file
    names must also match in order to be included.

    Arguments:
      dirn: name/path of directory to look for files in
      pattern: optional, regular expression pattern to filter names with
      file_list: optional, a list of file names to use instead of
       fetching a list of files from the specified directory

    Returns:
      List of csfasta-qual pair tuples.

    """
    # Get list of pairs
    file_pairs = GetSolidDataFiles(dirn,pattern=pattern,file_list=file_list)
    if not file_pairs:
        return []
    # Now match pairs of pairs: files with the same name except for
    # 'F3' and 'F5' or 'F5-BC'
    logging.debug("Matching F3 csfasta/qual file pairs with F5 counterparts")
    key_list = []
    matched_files = dict()
    for pair in file_pairs:
        # Remove _F3, _F5 and _F5-BC components from csfasta to
        # use as a key
        key = pair[0].replace('_F3','').replace('_F5-BC','').replace('_F5','')
        logging.debug("Key: %s for %s" % (key,pair))
        if key in key_list:
            # Already has an entry
            matched_files[key].append(pair)
        else:
            # New key
            key_list.append(key)
            matched_files[key] = [pair]
    # Check pairs of pairs
    data_files = []
    for key in key_list:
        if len(matched_files[key]) != 2:
            logging.debug("discarding pairs: %s" % matched_files[key])
        else:
            # Look for F3 and F5s and put into order
            try:
                matched_files[key][0][0].index('F5')
                # F5 pair are first set
                f3_index = 1
                f5_index = 0
            except ValueError:
                # F3 pair are first set
                f3_index = 0
                f5_index = 1
            # Pull out files and append to list in the
            # correct order (F3 then F5)
            csfasta_f3 = matched_files[key][f3_index][0]
            qual_f3 = matched_files[key][f3_index][1]
            csfasta_f5 = matched_files[key][f5_index][0]
            qual_f5 = matched_files[key][f5_index][1]
            data_files.append((csfasta_f3,qual_f3,csfasta_f5,qual_f5))
    # Done - return file list
    return data_files

def GetFastqFiles(dirn,pattern=None,file_list=None):
    """Return list of fastq files in target directory

    Optionally also specify a regular expression pattern that file
    names must also match in order to be included.

    Arguments:
      dirn: name/path of directory to look for files in
      pattern: optional, regular expression pattern to filter names with
      file_list: optional, a list of file names to use instead of
       fetching a list of files from the specified directory

    Returns:
      List of file-pair tuples.

    """
    data_files = []
    if file_list is not None:
        # Used supplied file list
        logging.debug("Ignoring dirn argument and using supplied file list")
        all_files = file_list
    else:
        # Check directory exists
        if not os.path.isdir(dirn):
            logging.error("'%s' not a directory: unable to collect fastq files" % dirn)
            return []
        # Gather data files
        logging.debug("Collecting fastq files in %s" % dirn)
        all_files = os.listdir(dirn)
    all_files.sort()
    # Regular expression pattern
    if pattern is not None:
        regex = re.compile(pattern)
    # Look for Fastq files
    for filen in all_files:
        logging.debug("Examining file %s" % filen)
        root = os.path.splitext(filen)[0]
        ext = os.path.splitext(filen)[1]
        if ext in (".fastq",".fq"):
            # If a regex pattern is specified then also filter on it
            if pattern is None or regex.search(root):
                data_files.append((filen,))
    # Done - return file list
    return data_files

def GetFastqGzFiles(dirn,pattern=None,file_list=None):
    """Return list of fastq.gz files in target directory

    Optionally also specify a regular expression pattern that file
    names must also match in order to be included.

    Arguments:
      dirn: name/path of directory to look for files in
      pattern: optional, regular expression pattern to filter names with
      file_list: optional, a list of file names to use instead of
       fetching a list of files from the specified directory

    Returns:
      List of file-pair tuples.

    """
    data_files = []
    if file_list is not None:
        # Used supplied file list
        logging.debug("Ignoring dirn argument and using supplied file list")
        all_files = file_list
    else:
        # Check directory exists
        if not os.path.isdir(dirn):
            logging.error("'%s' not a directory: unable to collect fastq.gz files" % dirn)
            return []
        # Gather data files
        logging.debug("Collecting fastq.gz files in %s" % dirn)
        all_files = os.listdir(dirn)
    all_files.sort()
    # Regular expression pattern
    if pattern is not None:
        regex = re.compile(pattern)
    # Look for .fastq.gz
    for filen in all_files:
        logging.debug("Examining file %s" % filen)
        if filen.split('.')[-1] == "gz":
            # Ends with gz
            try:
                if filen.split('.')[-2] in ("fastq","fq"):
                    # If a regex pattern is specified then also filter on it
                    if pattern is None or regex.search(filen.split('.')[-3]):
                        data_files.append((filen,))
            except IndexError:
                # Ignore
                pass
    # Done - return file list
    return data_files

