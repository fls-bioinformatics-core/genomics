#!/usr/bin/env python
#
#     JobRunner.py: classes for starting and managing job runs
#     Copyright (C) University of Manchester 2011-2025 Peter Briggs
#

"""
Classes for starting, stopping and managing jobs.

Class ``BaseJobRunner`` is a template with methods that need to be
implemented by subclasses. The subclasses implemented here are:

* ``SimpleJobRunner``: run jobs (e.g. scripts) on a local file system.
* ``GEJobRunner``    : run jobs using Grid Engine (GE) i.e. qsub, qdel etc
* ``SlurmRunner``    : run jobs using Slurm i.e. sbatch, scancel etc

A single job runner instance can be used to start and manage multiple
processes.

Each job is started by invoking the ``run`` method of the runner. This
returns an id string which is then used in calls to the various job
monitoring and control methods (e.g. ``isRunning``, ``terminate`` etc)
to interact with the job.

The runner's ``list`` method returns a list of running job ids.

Simple usage example:

>>> # Create a JobRunner instance
>>> runner = SimpleJobRunner()
>>> # Start a job using the runner and collect its id
>>> job_id = runner.run('Example',None,'myscript.sh')
>>> # Wait for job to complete
>>> import time
>>> while runner.isRunning(job_id):
>>>     time.sleep(10)
>>> # Get the names of the output files
>>> log,err = (runner.logFile(job_id),runner.errFile(job_id))

Processes run using a job runner inherit the environment where the runner
is created and executed.

Additionally runners set an ``BCFTBX_RUNNER_NSLOTS`` environment variable,
which is set to the number of slots (aka CPUs/cores/threads) available to
processes executed by the runner. For all runners this defaults to one
(i.e. serial jobs); the ``nslots`` option can be used when instantiating
``SimpleJobRunner`` and 'SlurmRunner' objects to specify more cores, for
example:

>>> multicore_runner = SimpleJobRunner(nslots=4)

For ``GEJobRunner`` instances the number of cores is set by specifying
the ``-pe`` argument as part of the 'ge_extra_args' option, for example:

>>> multicore_runner = GEJobRunner(extra_ge_args=('-pe','smp.pe','4'))

"""

#######################################################################
# Import modules that this module depends on
#######################################################################

from .jobs import runners
import os
import time

#######################################################################
# Classes
#######################################################################

class BaseJobRunner:
    """Base class for implementing job runners

    This class can be used as a template for implementing custom
    job runners. The idea is that the runners wrap the specifics
    of interacting with an underlying job control system and thus
    provide a generic interface to be used by higher level classes.

    A job runner needs to implement the following methods:

    - ``run``        : starts a job running
    - ``terminate``  : kills a running job
    - ``list``       : lists the running job ids
    - ``logFile``    : returns the name of the log file for a job
    - ``errFile``    : returns the name of the error file for a job
    - ``exit_status``: returns the exit status for the command (or
      None if the job is still running)

    Optionally it can also implement the methods:

    - ``errorState``: indicates if running job is in an "error state"
    - ``isRunning`` : checks if a specific job is running

    if the default implementations are not sufficient.
    """

    def __init__(self):
        self.__log_dir = None

    def run(self,name,working_dir,script,args):
        """Start a job running

        Arguments:
          name: Name to give the job
          working_dir: Directory to run the job in
          script: Script file to run
          args: List of arguments to supply to the script

        Returns:
          Returns a job id, or None if the job failed to start
        """
        raise NotImplementedError("Subclass must implement 'run'")

    def terminate(self,job_id):
        """Terminate a job

        Returns True if termination was successful, False
        otherwise
        """
        raise NotImplementedError("Subclass must implement 'terminate'")

    def list(self):
        """Return a list of running job_ids
        """
        raise NotImplementedError("Subclass must implement 'list'")

    def logFile(self,job_id):
        """Return name of log file relative to working directory
        """
        raise NotImplementedError("Subclass must implement 'logFile'")

    def errFile(self,job_id):
        """Return name of error file relative to working directory
        """
        raise NotImplementedError("Subclass must implement 'errFile'")

    def isRunning(self,job_id):
        """Check if a job is running

        Returns True if job is still running, False if not
        """
        return job_id in self.list()

    def errorState(self,job_id):
        """Check if the job is in an error state

        Return True if the job is deemed to be in an 'error state',
        False otherwise.
        """
        return False

    def exit_status(self,job_id):
        """Return the exit status code for the command

        Return the exit status code from the command that was
        run by the specified job, or None if the job hasn't
        exited yet.
        """
        return None

    @property
    def log_dir(self):
        """Return the current log directory setting

        """
        return self.__log_dir

    def set_log_dir(self,log_dir):
        """(Re)set the directory to write log files to

        """
        if log_dir is not None:
            self.__log_dir = os.path.abspath(log_dir)
        else:
            self.__log_dir = None

class SimpleJobRunner(runners.LocalRunner):
    """Class implementing job runner for local system

    ``SimpleJobRunner`` is a wrapper for the ``LocalRunner``
    class from the ``jobs.runners`` module.

    Arguments:
      log_dir: Directory to write log files to (set to 'None' to use
        CWD)
      join_logs: Combine stderr and stdout into a single log file (by
        default stdout and stderr have their own log files)
      nslots: Number of threads associated with this runner instance
    """

    def __init__(self,log_dir=None,join_logs=False,nslots=1):
        super(SimpleJobRunner,self).__init__(log_dir=log_dir,
                                             join_logs=join_logs,
                                             nslots=nslots)
        self._runner_name = "SimpleJobRunner"

    def isRunning(self, job_id):
        """Check if a job is running
        """
        return self.is_running(job_id)

    def logFile(self,job_id):
        """Return the log file name for a job
        """
        return self.log_file(job_id)

    def errFile(self,job_id):
        """Return the error file name for a job
        """
        return self.err_file(job_id)

class GEJobRunner(runners.GridEngineRunner):
    """Class implementing job runner for Grid Engine

    ``GEJobRunner`` is a wrapper for the ``GridEngineRunner``
    class from the ``jobs.runners`` module.

    Arguments:
      queue (str): name of GE queue to use (set to 'None' to use
        default queue)
      log_dir (str): directory to write log files to (set to 'None'
        to use CWD)
      ge_extra_args (list): arbitrary additional arguments to supply
        to ``qsub``
      poll_interval (int): time interval (in seconds) to use when
        polling Grid Engine e.g. to acquire ``qacct`` information
        (default: 5)
      timeout (int): maximum length of time (in seconds) to wait
        before giving up when polling Grid Engine (default: 30)
    """

    def __init__(self,queue=None,log_dir=None,ge_extra_args=None,
                 poll_interval=5,timeout=30):
        super(GEJobRunner,self).__init__(queue=queue,
                                         log_dir=log_dir,
                                         ge_extra_args=ge_extra_args,
                                         poll_interval=poll_interval,
                                         timeout=timeout)
        self._runner_name = "GEJobRunner"

    def isRunning(self, job_id):
        """Check if a job is running
        """
        return self.is_running(job_id)

    def logFile(self,job_id):
        """Return the log file name for a job

        The name should be '<name>.o<job_id>'
        """
        return self.log_file(job_id)

    def errFile(self,job_id):
        """Return the error file name for a job

        The name should be '<name>.e<job_id>'
        """
        return self.err_file(job_id)

    def errorState(self,job_id):
        """Check if the job is in an error state

        Return True if the job is deemed to be in an 'error
        state' (i.e. qstat returns the state as 'E..'),
        False otherwise.
        """
        return self.error_state(job_id)

class SlurmRunner(runners.SlurmRunner):
    """
    Class implementing job runner for Slurm

    ``SlurmRunner`` is a wrapper for the `SlurmRunner`` class
    from the ``jobs.runners`` module.

    Arguments:
      log_dir (str): path of directory to write log files to (set to 'None'
        to use cwd)
      nslots (int): number of threads assigned to the runner instance
      partition (str): name of Slurm partition to target (set to 'None'
        to use default queue)
      join_logs (bool): if True then combine stderr and stdout into a
        single log file (default is to write stdout and stderr to separate
        log files)
      slurm_extra_args (list): arbitrary additional arguments to supply
        to 'sbatch' (e.g. '["-n", 8]')
      poll_interval (int): time interval to use (in seconds) when polling
        Slurm using 'squeue' (seconds) (default: 300.0)
      timeout (int): maximum length of time to wait (in seconds) before
        giving up when submitting jobs to Slurm and finalizing jobs
        (default: 30)
      missing_job_timeout (int): minimum time (in seconds) that a job
        needs to be flagged as "missing" before it's removed from the
        runner (default: 600)
    """

    def __init__(self, log_dir=None, nslots=None, partition=None,
                 join_logs=None, slurm_extra_args=None,
                 poll_interval=300, timeout=30, missing_job_timeout=600):
        super(SlurmRunner,self).__init__(log_dir=log_dir,
                                         nslots=nslots,
                                         partition=partition,
                                         join_logs=join_logs,
                                         slurm_extra_args=slurm_extra_args,
                                         poll_interval=poll_interval,
                                         timeout=timeout,
                                         missing_job_timeout=missing_job_timeout)
        self._runner_name = "SlurmRunner"

    def isRunning(self, job_id):
        """Check if a job is running
        """
        return self.is_running(job_id)

    def logFile(self,job_id):
        """Return the log file name for a job

        The name should be '<name>.o<job_id>'
        """
        return self.log_file(job_id)

    def errFile(self,job_id):
        """Return the error file name for a job

        The name should be '<name>.e<job_id>'
        """
        return self.err_file(job_id)

    def errorState(self,job_id):
        """Check if the job is in an error state

        Return True if the job is deemed to be in an 'error
        state', False otherwise.
        """
        return self.error_state(job_id)

#######################################################################
# Functions
#######################################################################

def fetch_runner(definition):
    """Return job runner instance based on a definition string

    Given a definition string, returns an appropriate runner
    instance.

    Definitions are of the form:

    ::

        RunnerName[(args)]

    RunnerName can be 'SimpleJobRunner', 'GEJobRunner' or
    'SlurmRunner'. If '(args)' are also supplied then:

    - for SimpleJobRunners, this can be a list of optional
      arguments separated by spaces:

      * 'nslots=N' (where N is an integer; sets a non-default
        number of slots
      * 'join_logs=BOOLEAN' (where BOOLEAN can be 'True',
        'true','y','False','false','n'; sets whether stdout
        and stderr should be written to the same file)

    - for GEJobRunners, this is a set of arbitrary 'qsub'
      options that will be used on job submission

    - for SlurmRunners, this can be a list of optional
      arguments separated by spaces:

      * 'nslots=N' (where N is an integer; sets a non-default
        number of slots
      * 'partition=STRING' (where STRING is the name of the
        target Slurm partition)
      * 'join_logs=BOOLEAN' (where BOOLEAN can be 'True',
        'true','y','False','false','n'; sets whether stdout
        and stderr should be written to the same file)
      * a sting with arbitrary 'sbatch' options that will be
        included on job submission (note: '-J', '-o', '-e'
        and '--export' cannot be specified)

    """
    if definition.startswith('SimpleJobRunner'):
        if definition.startswith('SimpleJobRunner(') and \
           definition.endswith(')'):
            args = definition[len('SimpleJobRunner('):len(definition)-1].split(' ')
            nslots = 1
            join_logs=True
            for arg in args:
                if arg.startswith("nslots="):
                    nslots = int(arg.split('=')[-1])
                elif arg.startswith("join_logs="):
                    join_logs = arg.split('=')[-1].lower()
                    if join_logs in ('true','yes','y'):
                        join_logs = True
                    elif join_logs in ('false','no','n'):
                        join_logs = False
                    else:
                        raise Exception("Invalid value for SimpleJobRunner "
                                        "'join_logs': %s" % join_logs)
                else:
                    raise Exception("Unrecognised argument for "
                                    "SimpleJobRunner definition: %s" % arg)
            return SimpleJobRunner(join_logs=join_logs,nslots=nslots)
        else:
            return SimpleJobRunner(join_logs=True)
    elif definition.startswith('GEJobRunner'):
        if definition.startswith('GEJobRunner(') and definition.endswith(')'):
            ge_extra_args = definition[len('GEJobRunner('):len(definition)-1].split(' ')
            return GEJobRunner(ge_extra_args=ge_extra_args)
        else:
            return GEJobRunner()
    elif definition.startswith("SlurmRunner"):
        if definition.startswith("SlurmRunner(") and definition.endswith(")"):
            args = definition[len("SlurmRunner("):len(definition)-1].split(" ")
            nslots = None
            partition = None
            join_logs=None
            extra_args=[]
            for arg in args:
                if arg.startswith("nslots="):
                    nslots = int(arg.split("=")[-1])
                elif arg.startswith("partition="):
                    partition = arg.split("=")[-1]
                elif arg.startswith("join_logs="):
                    join_logs = arg.split('=')[-1].lower()
                    if join_logs in ("true", "yes", "y"):
                        join_logs = True
                    elif join_logs in ("false", "no", "n"):
                        join_logs = False
                    else:
                        raise Exception(f"Invalid value for SlurmRunner "
                                        f"'join_logs': %s" % join_logs)
                else:
                    extra_args.append(arg)
            return SlurmRunner(nslots=nslots,
                               partition=partition,
                               join_logs=join_logs,
                               slurm_extra_args=extra_args)
        else:
            return SlurmRunner()
    raise Exception("Unrecognised runner definition: %s" % definition)
