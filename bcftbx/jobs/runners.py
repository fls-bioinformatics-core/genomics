#!/usr/bin/env python3
#
#     jobs.runners.py: start, stop and managing job runs
#     Copyright (C) University of Manchester 2011-2025 Peter Briggs
#
########################################################################
#
# jobs.runners.py
#
#########################################################################

"""
Provides classes with a generic signature for starting, stopping and
managing jobs.

The ``JobRunner`` class is a base class which provides a template with
methods that need to be implemented by job runner subclasses.

The subclasses implemented here are:

* ``LocalRunner``: executes jobs on the local file system

A single job runner instance can be used to start and manage multiple
processes.

Usage of job runners is as follows:

* Start a new job by invoking the ``run`` method of the runner; this
  returns an id string which is then used in calls to the various job
  monitoring and control methods to interact with the job.
* The ``list`` method returns a list of running job ids
* The ``is_running`` method checks if a specific job is still running
* The ``terminate`` method kills a running job
* The ``log_file`` and ``err_file`` methods return the paths to the
  log and error files associated with a job

Simple usage example:

# Create a JobRunner instance
>>> runner = LocalRunner()
# Start a job using the runner and collect its id
>>> job_id = runner.run('Example',None,'myscript.sh',[])
# Wait for job to complete
>>> import time
>>> while runner.is_running(job_id):
>>>     time.sleep(10)
# Get the names of the output files
>>> log,err = (runner.log_file(job_id),runner.err_file(job_id))

Processes run using a job runner inherit the environment where the runner
is created and executed.

Addi
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

Additionally, runners set the ``BCFTBX_RUNNER_NSLOTS`` environment variable,
which is set to the number of slots (aka CPUs/cores/threads) available to
processes executed by the runner. For all runners this defaults to one
(i.e. serial jobs); the ``nslots`` option can be used when creating
``LocalRunner`` and 'SlurmRunner' instances to specify more cores, for
example:

>>> multicore_runner = LocalRunner(nslots=4)

For ``GridEngineRunner`` instances the number of cores is set by specifying
the ``-pe`` argument as part of the 'ge_extra_args' option, for example:

>>> multicore_runner = GridEngineRunner(extra_ge_args=('-pe','smp.pe','4'))
"""

import os
import time
import subprocess
import uuid
import logging

# Module specific logger
logger = logging.getLogger(__name__)

#######################################################################
# Classes
#######################################################################

class JobRunner:
    """
    Base class for implementing job runners

    This class can be used as a template for implementing custom
    job runners. The idea is that the runners wrap the specifics
    of interacting with an underlying job control system and thus
    provide a generic interface to be used by higher level classes.

    A job runner needs to implement the following methods:

    - ``run``: starts a job running
    - ``terminate``: kills a running job
    - ``list``: lists the running job ids
    - ``log_file``: returns the name of the log file for a job
    - ``err_file``: returns the name of the error file for a job
    - ``exit_status``: returns the exit status for the command (or
      None if the job is still running)

    Optionally it can also implement the methods:

    - ``error_state``: indicates if running job is in an "error state"
    - ``is_running`` : checks if a specific job is running

    if the default implementations are not sufficient.
    """

    def __init__(self):
        self._log_dir = None

    def run(self, name, working_dir, script, args):
        """
        Start a job running

        Arguments:
          name (str): Name to give the job
          working_dir (str): path to directory to run the job in
          script (str): path to script file to run
          args (list): arguments to supply to the script

        Returns:
          Integer: returns a job id, or None if the job failed to
          start.
        """
        raise NotImplementedError("Subclass must implement 'run'")

    def terminate(self, job_id):
        """
        Terminate a running job

        Arguments:
            job_id (int): id of job to terminate

        Returns:
             Boolean: True if termination was successful, False
             otherwise
        """
        raise NotImplementedError("Subclass must implement 'terminate'")

    def list(self):
        """
        Return a list of running jobs

        Returns:
            list: list of job ids for currently running jobs.
        """
        raise NotImplementedError("Subclass must implement 'list'")

    def log_file(self, job_id):
        """
        Return path to log file

        Arguments:
            job_id (int): id of job

        Returns:
            str: path to log file for the specified job
        """
        raise NotImplementedError("Subclass must implement 'log_file'")

    def err_file(self, job_id):
        """
        Return path to error file

        Arguments:
            job_id (int): id of job

        Returns:
            str: path to error file for the specified job
        """
        raise NotImplementedError("Subclass must implement 'err_file'")

    def is_running(self, job_id):
        """Check if a job is running

        Arguments:
            job_id (int): id of job

        Returns:
            boolean: True if job is still running, False if not
        """
        return job_id in self.list()

    def error_state(self, job_id):
        """
        Check if the job is in an error state

        Arguments:
            job_id (int): id of job

        Returns:
            boolean: True if the job is deemed to be in an
            'error state', False otherwise.
        """
        return False

    def exit_status(self, job_id):
        """
        Return the exit status code for the job

        Arguments:
            job_id (int): id of job

        Returns:
            int or None: the exit status code from the command
            that was run by the specified job (or None if the
            job hasn't exited yet).
        """
        return None

    @property
    def log_dir(self):
        """
        Return the current log directory setting

        Returns:
            str: path to log directory used to write log
            files to
        """
        return self._log_dir

    def set_log_dir(self, log_dir):
        """
        (Re)set the directory for log files to

        Arguments:
            log_dir (str): path to directory to use for log
            files
        """
        if log_dir is not None:
            self._log_dir = os.path.abspath(log_dir)
        else:
            self._log_dir = None


class LocalRunner(JobRunner):
    """
    Job runner for local system

    ``LocalRunner`` runs jobs as processes the local system;
    the status of jobs is determined using the Linux ``ps eu``
    command, and they are terminated using ``kill -9``.

    Arguments:
      log_dir (str): path to directory for log files to (set to `None`
        to use CWD)
      join_logs (bool): combine stderr and stdout into a single log
        file (by default stdout and stderr have their own log files)
      nslots (int): Number of threads associated with the runner
        instance
    """
    def __init__(self, log_dir=None, join_logs=False, nslots=1):
        # Runner name
        self._runner_name = "LocalRunner"
        # Store a list of job ids (= pids) managed by this class
        self._job_list = []
        # Names
        self._names = {}
        # Base log id
        self._log_id = int(time.time())
        # Directory for log files
        self.set_log_dir(log_dir)
        # Join stderr to stdout
        self._join_logs = join_logs
        # Number of slots
        self._nslots = nslots
        # Keep track of log files etc
        self._log_files = {}
        self._err_files = {}
        self._log_fp = {}
        self._err_fp = {}
        self._exit_status = {}
        self._job_popen = {}
        # Job id lock
        self._job_lock = ResourceLock()
        # Call base class init
        super().__init__()

    def __repr__(self):
        name = self._runner_name
        args = []
        if self._nslots > 1:
            args.append("nslots=%s" % self._nslots)
        args.append("join_logs=%s" % self._join_logs)
        if args:
            name += '(%s)' % ' '.join(args)
        return name

    def run(self, name, working_dir, script, args):
        """
        Starting running a command and return the job ID

        The job ID is the PID of the started process.

        Arguments:
          name (str): Name to give the job
          working_dir (str): path to the directory to run
            the job in
          script (str): path to the script file to run
          args (list): arguments to supply to the script

        Returns:
          str: job id for submitted job, or 'None' if job
            failed to start.
        """
        logger.debug(f"{self._runner_name}: submitting job")
        logger.debug("Name       : %s" % name)
        logger.debug("Working_dir: %s" % working_dir)
        logger.debug("Log dir    : %s" % self.log_dir)
        logger.debug("Join logs  : %s" % self._join_logs)
        logger.debug("Nslots     : %s" % self.nslots)
        logger.debug("Script     : %s" % script)
        logger.debug("Arguments  : %s" % str(args))
        # Build command to be submitted
        cmd = [script]
        cmd.extend(args)
        logger.debug(f"{self._runner_name}: command: %s" % cmd)
        # Check working directory
        if working_dir:
            working_dir = os.path.abspath(working_dir)
            if not os.path.exists(working_dir):
                logger.error(f"{self._runner_name}: working dir '%s' "
                              "doesn't exist!" % working_dir)
                return None
        else:
            working_dir = os.getcwd()
        logger.debug(f"{self._runner_name}: executing in %s" % working_dir)
        # Set up log files
        lognames = self._assign_log_files(name,working_dir)
        log = open(lognames[0], "wt")
        if not self._join_logs:
            err = open(lognames[1], "wt")
        else:
            err = subprocess.STDOUT
        # Set up the environment
        env = os.environ.copy()
        env["BCFTBX_RUNNER_NSLOTS"] = "%s" % self.nslots
        # Start the subprocess
        p = subprocess.Popen(cmd,
                             cwd=working_dir,
                             stdout=log,
                             stderr=err,
                             env=env)
        # Capture the job id from the output
        job_id = str(p.pid)
        logger.debug(f"{self._runner_name}: done - job id = %s" % job_id)
        # Do internal house keeping
        self._job_list.append(job_id)
        self._log_files[job_id] = lognames[0]
        self._job_popen[job_id] = p
        self._log_fp[job_id] = log
        if not self._join_logs:
            self._err_files[job_id] = lognames[1]
            self._err_fp[job_id] = err
        else:
            self._err_files[job_id] = None
            self._err_fp[job_id] = None
        # Store name against job id
        if job_id is not None:
            self._names[job_id] = name
        # Return the job id
        return job_id

    def terminate(self, job_id):
        """
        Stop a running job using 'kill -9'

        Arguments:
            job_id (str): id of job to terminate

        Returns:
            Boolean: True if termination was successful, False
            otherwise
        """
        # Check it's one of ours
        if job_id not in self._job_list:
            logger.debug("Don't own job %s, can't delete" % job_id)
            return False
        # Attempt to terminate
        logger.debug(f"{self._runner_name}: deleting job '{job_id}'")
        p = self._job_popen[job_id]
        p.terminate()
        p.wait()
        if job_id not in self.list():
            logger.debug(f"{self._runner_name}: deleted job '{job_id}'")
            return True
        else:
            logger.error(f"{self._runner_name}: failed to delete job '{job_id}'")
            return False

    @property
    def nslots(self):
        """
        Return the number of associated slots

        Returns:
            Integer: number of slots
        """
        return self._nslots

    def name(self, job_id):
        """
        Return the job name

        Arguments:
            job_id (str): id of job

        Returns:
            str: name of the job
        """
        return self._names[job_id]

    def log_file(self, job_id):
        """
        Return the log file path associated with a job

        Arguments:
            job_id (str): id of job

        Returns:
            str: path to log file for the specified job
        """
        return self._log_files[job_id]

    def err_file(self,job_id):
        """
        Return the error file path associated with a job

        Arguments:
            job_id (str): id of job

        Returns:
            str: path to error file for the specified job
        """
        return self._err_files[job_id]

    def list(self):
        """
        Return a list of running jobs

        Returns:
            list: list of job ids for currently running jobs.
        """
        job_ids = []
        for job_id in [jid for jid in self._job_popen]:
            try:
                # Get lock on this job id
                lock = None
                while lock is None:
                    lock = self._job_lock.acquire(job_id)
                logger.debug(f"{self._runner_name}: acquired lock: {lock}")
                # Get the associated Popen instance
                p = self._job_popen[job_id]
            except KeyError:
                # Job has been removed since the list
                # was fetched? Ignore
                logger.debug(f"{self._runner_name}: job '{job_id}' has gone away")
                self._job_lock.release(lock)
                continue
            status = p.poll()
            if status is None:
                job_ids.append(job_id)
            else:
                # Set exit status
                logger.debug("Job id %s: finished (%s)" % (job_id, status))
                self._exit_status[job_id] = status
                # Close output files
                for fp in (self._log_fp,
                           self._err_fp,):
                    try:
                        if fp[job_id] is not None:
                            fp[job_id].close()
                    except KeyError:
                        logger.warning("Job id %s: couldn't get output "
                                       "file to close" % job_id)
                # Remove job records
                for data in (self._job_popen,
                             self._log_fp,
                             self._err_fp,):
                    try:
                        del(data[job_id])
                    except KeyError:
                        logger.warning("Job id %s: record already "
                                       "deleted?" % job_id)
            # Release the lock
            self._job_lock.release(lock)
        return job_ids

    def exit_status(self, job_id):
        """
        Return exit status from a job

        Arguments:
            job_id (str): id of job

        Returns:
            int or None: exit status code from the command
            that was run by the specified job (or None if
            the job hasn't exited yet).
        """
        if job_id in self._job_popen:
            # Job exists but still running
            return None
        # Look for return code
        try:
            return self._exit_status[job_id]
        except KeyError:
            logger.error("Don't know anything about job %s" % job_id)
            return None

    def _assign_log_files(self, name, working_dir):
        """
        Internal: return log file names for stdout and stderr

        Since the job id isn't known before the job starts, create
        names based on the timestamp plus the supplied 'name'
        """
        timestamp = self._log_id
        log_file = "%s.o%s" % (name, timestamp)
        error_file = "%s.e%s" % (name, timestamp)
        if self.log_dir is None:
            log_dir = working_dir
        else:
            log_dir = self.log_dir
        log_file = os.path.join(log_dir, log_file)
        error_file = os.path.join(log_dir, error_file)
        self._log_id += 1
        return (log_file, error_file)


class ResourceLock:
    """
    Class for managing in-process locks on 'resources'

    A 'resource' is identified by an arbitrary string.

    Example usage: create a new ResourceLock instance
    and check if a resource is locked:

    >>> r = ResourceLock()
    >>> r.is_locked("resource1")
    False

    Try to acquire the lock on the resource:

    >>> lock = r.acquire("resource1")
    >>> r.is_locked("resource1")
    True

    Release the lock on the resource:

    >>> r.release(lock)
    >>> r.is_locked("resource1")
    False
    """
    def __init__(self):
        """
        Create a new ResourceLock instance
        """
        self._locks = dict()

    def _get_lock_name(self,resource_name):
        """
        Internal: return a unique lock name

        Returns a unique timestamped lock name
        for the named resource.

        Arguments:
          resource_name (str): name of the resource
            to create a lock name for

        Returns:
          String: lock name for the resource.
        """
        return "%s@%s@%s" % (resource_name,
                             time.time(),
                             uuid.uuid4())

    def _split_lock_name(self,lock):
        """
        Internal: split a lock name into components

        Arguments:
          lock (str): lock name to split

        Returns:
          Tuple: tuple consisting of (resource_name,
            timestamp, unique ID). The timestamp is
            returned as a float.
        """
        resource_name,timestamp,uuid_ = lock.split('@')
        timestamp = float(timestamp)
        return (resource_name,timestamp,uuid_)

    def acquire(self,resource_name,timeout=None):
        """
        Attempt to acquire the lock on a resource

        Arguments:
          resource_name (str): name of the resource
            to acquire the lock name for
          timeout (float): optional, specifies a
            timeout period after which failure to
            acquire the lock raises an exception.

        Returns:
          String: lock name.
        """
        logger.debug("ResourceLock: attempting to get lock for "
                      "resource '%s'" % resource_name)
        start_time = time.time()
        has_lock = False
        while not has_lock:
            # Assume we have the lock, until proven otherwise
            has_lock = True
            # Register a putative lock
            lock = self._get_lock_name(resource_name)
            self._locks[lock] = True
            logger.debug("ResourceLock: made new lock '%s'" % lock)
            # Wait
            time.sleep(0.001)
            # Check all locks for this resource and see if any
            # pre-date the new lock
            resource_name,timestamp,uuid_ = self._split_lock_name(lock)
            for l in list(self._locks.keys()):
                if l == lock:
                    continue
                n,ts,uid = self._split_lock_name(lock)
                if n == resource_name:
                    if ts < timestamp:
                        # Resource is already locked
                        logger.debug("ResourceLock: resource '%s' already "
                                      "locked" % resource_name)
                        # Remove attempted lock
                        self.release(lock)
                        return None
                    elif ts == timestamp:
                        # Deadlock: two locks with same priority
                        logger.debug("ResourceLock: two locks with same "
                                      "priority for resource '%s'" %
                                      resource_name)
                        # We don't have the lock after all
                        has_lock = False
                        # Release the putative lock
                        self.release(lock)
                        # Retry after a random delay
                        time.sleep(random.random())
                        break
            # Check for timeout
            if not has_lock and timeout is not None:
                if (time.time() - start_time) > timeout:
                    raise Exception("ResourceLock: timed out trying to "
                                    "acquire lock for resource '%s'" %
                                    resource_name)
        # This lock has priority
        logger.debug("ResourceLock: acquired lock: '%s'" % lock)
        return lock

    def release(self,lock):
        """
        Release a lock on a resource

        Arguments:
          lock (str): lock to release.
        """
        logger.debug("ResourceLock: releasing '%s'" % lock)
        del self._locks[lock]

    def is_locked(self,resource_name):
        """
        Check if a resource is locked

        Arguments:
          resource_name (str): name of the resource
            to check the lock for

        Returns:
          Boolean: True if resource is locked, False
            if not.
        """
        for lock in [l for l in self._locks.keys()]:
            n,ts,uid = self._split_lock_name(lock)
            if n == resource_name:
                return True
        return False