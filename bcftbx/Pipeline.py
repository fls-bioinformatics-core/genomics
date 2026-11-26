#!/usr/bin/env python
#
#     Pipeline.py: classes for running scripts iteratively
#     Copyright (C) University of Manchester 2011-2022 Peter Briggs
#
########################################################################
#
# Pipeline.py
#
#########################################################################

"""
Legacy module providing classes for running scripts iteratively over a
collection of data files.
"""

import logging
from .qc import pipeline

#######################################################################
# Class definitions
#######################################################################

# Job: container for a script run
class Job(pipeline.Job):
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
      err         The error log file for the job
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
        super().__init__(runner,name,dirn,script,args,label,group)

    def isRunning(self):
        """Check if job is still running
        """
        return self.is_running()

    def errorState(self):
        """Check if the job is in an error state
        """
        return self.error_state()

# PipelineRunner: class to set up and run multiple jobs
class PipelineRunner(pipeline.PipelineRunner):
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
        super().__init__(runner,max_concurrent_jobs,poll_interval,jobCompletionHandler,groupCompletionHandler)

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
        return self.queue_job(working_dir,script,script_args,label,group)

    def nWaiting(self):
        """Return the number of jobs still waiting to be started
        """
        return self.n_waiting()

    def nRunning(self):
        """Return the number of jobs currently running
        """
        return self.n_running()

    def nCompleted(self):
        """Return the number of jobs that have completed
        """
        return self.n_completed()

    def isRunning(self):
        """Check whether the pipeline is still running

        Returns True if the pipeline is still running (i.e. has either
        running jobs, waiting jobs or both) and False otherwise.
        """
        return self.is_running()


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
    return pipeline.get_solid_data_files(dirn,pattern,file_list)

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
    return pipeline.get_solid_paired_end_files(dirn,pattern,file_list)

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
    return pipeline.get_fastq_files(dirn,pattern,file_list)

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
    return pipeline.get_fastq_gz_files(dirn,pattern,file_list)