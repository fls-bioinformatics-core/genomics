#!/usr/bin/env python
#
#     JobRunner.py: classes for starting and managing job runs
#     Copyright (C) University of Manchester 2011-2025 Peter Briggs
#
########################################################################
#
# JobRunner.py
#
#########################################################################

"""
Classes for starting, stopping and managing jobs.

Class BaseJobRunner is a template with methods that need to be implemented
by subclasses. The subclasses implemented here are:

* SimpleJobRunner: run jobs (e.g. scripts) on a local file system.
* GEJobRunner    : run jobs using Grid Engine (GE) i.e. qsub, qdel etc
* SlurmRunner    : run jobs using Slurm i.e. sbatch, scancel etc

A single JobRunner instance can be used to start and manage multiple processes.

Each job is started by invoking the 'run' method of the runner. This returns
an id string which is then used in calls to the 'isRunning', 'terminate' etc
methods to check on and control the job.

The runner's 'list' method returns a list of running job ids.

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

Additionally runners set an 'BCFTBX_RUNNER_NSLOTS' environment variable,
which is set to the number of slots (aka CPUs/cores/threads) available to
processes executed by the runner. For all runners this defaults to one
(i.e. serial jobs); the 'nslots' option can be used when instantiating
'SimpleJobRunner' and 'SlurmRunner' objects to specify more cores, for
example:

>>> multicore_runner = SimpleJobRunner(nslots=4)

For 'GEJobRunner' instances the number of cores is set by specifying
'-pe smp.pe' as part of the 'ge_extra_args' option, for example:

>>> multicore_runner = GEJobRunner(extra_ge_args=('-pe','smp.pe','4'))

"""

#######################################################################
# Import modules that this module depends on
#######################################################################

from builtins import str
import os
import io
import logging
import subprocess
import time
import tempfile
import shutil
import atexit
import uuid
import random

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

    - run        : starts a job running
    - terminate  : kills a running job
    - list       : lists the running job ids
    - logFile    : returns the name of the log file for a job
    - errFile    : returns the name of the error file for a job
    - exit_status: returns the exit status for the command (or
      None if the job is still running)

    Optionally it can also implement the methods:

    - errorState: indicates if running job is in an "error state"
    - isRunning : checks if a specific job is running

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

class SimpleJobRunner(BaseJobRunner):
    """Class implementing job runner for local system

    SimpleJobRunner starts jobs as processes on a local system;
    the status of jobs is determined using the Linux 'ps eu'
    command, and jobs are terminated using 'kill -9'.
    """

    def __init__(self,log_dir=None,join_logs=False,nslots=1):
        """Create a new SimpleJobRunner instance

        Arguments:
          log_dir: Directory to write log files to (set to 'None' to use
                   cwd)
          join_logs: Combine stderr and stdout into a single log file (by
                   default stdout and stderr have their own log files)
          nslots: Number of threads associated with this runner
                   instance

        """
        # Store a list of job ids (= pids) managed by this class
        self.__job_list = []
        # Names
        self.__names = {}
        # Base log id
        self.__log_id = int(time.time())
        # Directory for log files
        self.set_log_dir(log_dir)
        # Join stderr to stdout
        self.__join_logs = join_logs
        # Number of slots
        self.__nslots = nslots
        # Keep track of log files etc
        self.__log_files = {}
        self.__err_files = {}
        self.__log_fp = {}
        self.__err_fp = {}
        self.__exit_status = {}
        self.__job_popen = {}
        # Job id lock
        self.__job_lock = ResourceLock()

    def __repr__(self):
        name = 'SimpleJobRunner'
        args = []
        if self.__nslots > 1:
            args.append('nslots=%s' % self.__nslots)
        args.append('join_logs=%s' % self.__join_logs)
        if args:
            name += '(%s)' % ' '.join(args)
        return name

    def run(self,name,working_dir,script,args):
        """Run a command and return the PID (=job id)

        Arguments:
          name: Name to give the job
          working_dir: Directory to run the job in
          script: Script file to run
          args: List of arguments to supply to the script

        Returns:
          Job id for submitted job, or 'None' if job failed to
          start.
        """
        logging.debug("SimpleJobRunner: submitting job")
        logging.debug("Name       : %s" % name)
        logging.debug("Working_dir: %s" % working_dir)
        logging.debug("Log dir    : %s" % self.log_dir)
        logging.debug("Join logs  : %s" % self.__join_logs)
        logging.debug("Nslots     : %s" % self.nslots)
        logging.debug("Script     : %s" % script)
        logging.debug("Arguments  : %s" % str(args))
        # Build command to be submitted
        cmd = [script]
        cmd.extend(args)
        logging.debug("SimpleJobRunner: command: %s" % cmd)
        # Check working directory
        if working_dir:
            working_dir = os.path.abspath(working_dir)
            if not os.path.exists(working_dir):
                logging.error("SimpleJobRunner: working dir '%s' doesn't "
                              "exist!" % working_dir)
                return None
        else:
            working_dir = os.getcwd()
        logging.debug("SimpleJobRunner: executing in %s" % working_dir)
        # Set up log files
        lognames = self.__assign_log_files(name,working_dir)
        log = io.open(lognames[0],'wt')
        if not self.__join_logs:
            err = io.open(lognames[1],'wt')
        else:
            err = subprocess.STDOUT
        # Set up the environment
        env = os.environ.copy()
        env['BCFTBX_RUNNER_NSLOTS'] = "%s" % self.nslots
        # Start the subprocess
        p = subprocess.Popen(cmd,
                             cwd=working_dir,
                             stdout=log,stderr=err,
                             env=env)
        # Capture the job id from the output
        job_id = str(p.pid)
        logging.debug("SimpleJobRunner: done - job id = %s" % job_id)
        # Do internal house keeping
        self.__job_list.append(job_id)
        self.__log_files[job_id] = lognames[0]
        self.__job_popen[job_id] = p
        self.__log_fp[job_id] = log
        if not self.__join_logs:
            self.__err_files[job_id] = lognames[1]
            self.__err_fp[job_id] = err
        else:
            self.__err_files[job_id] = None
            self.__err_fp[job_id] = None
        # Store name against job id
        if job_id is not None:
            self.__names[job_id] = name
        # Return the job id
        return job_id

    def terminate(self,job_id):
        """Kill a running job using 'kill -9'
        """
        # Check it's one of ours
        if job_id not in self.__job_list:
            logging.debug("Don't own job %s, can't delete" % job_id)
            return False
        # Attempt to terminate
        logging.debug("KillJob: deleting job")
        p = self.__job_popen[job_id]
        p.terminate()
        p.wait()
        if job_id not in self.list():
            logging.debug("KillJob: deleted job %s" % job_id)
            return True
        else:
            logging.error("Failed to delete job %s" % job_id)
            return False

    @property
    def nslots(self):
        """Return the number of associated slots
        """
        return self.__nslots

    def name(self,job_id):
        """Return the name for a job
        """
        return self.__names[job_id]

    def logFile(self,job_id):
        """Return the log file name for a job
        """
        return self.__log_files[job_id]

    def errFile(self,job_id):
        """Return the error file name for a job
        """
        return self.__err_files[job_id]

    def list(self):
        """Return a list of running job_ids
        """
        job_ids = []
        for job_id in [jid for jid in self.__job_popen]:
            try:
                # Get lock on this job id
                lock = None
                while lock is None:
                    lock = self.__job_lock.acquire(job_id)
                logging.debug("SimpleJobRunner: acquired lock: %s" % lock)
                # Get the associated Popen instance
                p = self.__job_popen[job_id]
            except KeyError:
                # Job has been removed since the list
                # was fetched? Ignore
                logging.debug("SimpleJobRunner: job %s has gone away" %
                              job_id)
                self.__job_lock.release(lock)
                continue
            status = p.poll()
            if status is None:
                job_ids.append(job_id)
            else:
                # Set exit status
                logging.debug("Job id %s: finished (%s)" % (job_id,
                                                            status))
                self.__exit_status[job_id] = status
                # Close output files
                for fp in (self.__log_fp,
                           self.__err_fp,):
                    try:
                        if fp[job_id] is not None:
                            fp[job_id].close()
                    except KeyError:
                        logging.warning("Job id %s: couldn't get output "
                                        "file to close" % job_id)
                # Remove job records
                for data in (self.__job_popen,
                             self.__log_fp,
                             self.__err_fp,):
                    try:
                        del(data[job_id])
                    except KeyError:
                        logging.warning("Job id %s: record already "
                                        "deleted?" % job_id)
            # Release the lock
            self.__job_lock.release(lock)
        return job_ids

    def exit_status(self,job_id):
        """Return exit status from command run by a job
        """
        if job_id in self.__job_popen:
            # Job exists but still running
            return None
        # Look for return code
        try:
            return self.__exit_status[job_id]
        except KeyError:
            logging.error("Don't know anything about job %s" % job_id)
            return None

    def __assign_log_files(self,name,working_dir):
        """Internal: return log file names for stdout and stderr

        Since the job id isn't known before the job starts, create
        names based on the timestamp plus the supplied 'name'
        """
        timestamp = self.__log_id
        log_file = "%s.o%s" % (name,timestamp)
        error_file = "%s.e%s" % (name,timestamp)
        if self.log_dir is None:
            log_dir = working_dir
        else:
            log_dir = self.log_dir
        log_file = os.path.join(log_dir,log_file)
        error_file = os.path.join(log_dir,error_file)
        self.__log_id += 1
        return (log_file,error_file)

class GEJobRunner(BaseJobRunner):
    """Class implementing job runner for Grid Engine

    GEJobRunner submits jobs to a Grid Engine cluster using the
    'qsub' command, determines the status of jobs using 'qstat'
    and terminates then using 'qdel'.

    Additionally the runner can be configured for a specific GE
    queue on initialisation.

    Each GEJobRunner instance creates a temporary directory which
    it uses for internal admin; this will be removed at program
    exit via 'atexit'.
    """

    def __init__(self,queue=None,log_dir=None,ge_extra_args=None,
                 poll_interval=5.0,timeout=30.0):
        """Create a new GEJobRunner instance

        Arguments:
          queue:   Name of GE queue to use (set to 'None' to use default queue)
          log_dir: Directory to write log files to (set to 'None' to use cwd)
          ge_extra_args: Arbitrary additional arguments to supply to qsub
          poll_interval: time interval to use when polling Grid Engine e.g.
            to acquire qacct information (default 5s)
          timeout: maximum length of time to wait before giving up when
            polling Grid Engine (default 30s)
        """
        # Internal parameters
        self.__admin_dir = self.__make_admin_dir()
        self.__job_count = 0
        self.__shell = "/bin/bash"
        self.__ge_queue = queue
        # Directory for log files
        self.set_log_dir(log_dir)
        # Keep track of data (names, log dirs etc) for each job
        self.__job_number = {}
        self.__names = {}
        self.__log_dirs = {}
        self.__error_state = {}
        self.__exit_status = {}
        self.__finalizing = {}
        self.__queue = {}
        self.__start_time = {}
        self.__ge_extra_args = ge_extra_args
        # Job id lock
        self.__job_lock = ResourceLock()
        # Job grace period lock
        self.__updating_grace_period = ResourceLock()
        # Job submission lock
        self.__submit_lock = ResourceLock()
        # Cached job list
        self.__cached_job_list_lifetime = 2.0
        self.__cached_job_list_timestamp = 0.0
        self.__cached_job_list = []
        self.__cached_job_list_force_update = True
        # Cached qstat output
        self.__cached_qstat_output_lifetime = 2.0
        self.__cached_qstat_output_timestamp = 0.0
        self.__cached_qstat_output = None
        # Grace period for new jobs
        self.__new_job_grace_period = 2.0
        # Polling intervals and timeout periods (seconds)
        self.__ge_poll_interval = poll_interval
        self.__ge_timeout = timeout
        # Register clean up function
        atexit.register(self.__clean_up_admin_dir)

    def __repr__(self):
        name = 'GEJobRunner'
        if self.__ge_extra_args is not None:
            name += '(%s)' % ' '.join(self.__ge_extra_args)
        return name

    def name(self,job_id):
        """Return the name for a job
        """
        return self.__names[job_id]

    @property
    def ge_extra_args(self):
        """Return the extra GE arguments
        """
        return self.__ge_extra_args

    @property
    def nslots(self):
        """Return the number of associated slots

        This is extracted from the 'ge_extra_args'
        property, by looking for qsub options of the
        form '-pe XXXX N' (e.g. '-pe smp.pe 8'), where
        'nslots' will be N.
        """
        nslots = 1
        if self.ge_extra_args is not None:
            try:
                i = self.ge_extra_args.index('-pe')
                nslots = int(self.ge_extra_args[i+2])
            except ValueError:
                pass
        return nslots

    def run(self,name,working_dir,script,args):
        """Submit a script or command to the cluster via 'qsub'

        Arguments:
          name: Name to give the job
          working_dir: Directory to run the job in
          script: Script file to run
          args: List of arguments to supply to the script

        Returns:
          Job id for submitted job, or 'None' if job failed to
          start.
        """
        logging.debug("GEJobRunner: submitting job")
        logging.debug("Name       : %s" % name)
        logging.debug("Queue      : %s" % self.__ge_queue)
        logging.debug("Extra args : %s" % self.__ge_extra_args)
        logging.debug("Log dir    : %s" % self.log_dir)
        logging.debug("Working_dir: %s" % working_dir)
        logging.debug("Script     : %s" % script)
        logging.debug("Arguments  : %s" % str(args))
        # Wait for lock on job submission
        start_time = time.time()
        submit_lock = None
        while submit_lock is None:
            submit_lock = self.__submit_lock.acquire("job_submission",
                                                     timeout=self.__ge_timeout)
        # Get internal job number
        self.__job_count += 1
        job_number = self.__job_count
        logging.debug("Internal job count: %s" % job_number)
        # Release the lock
        self.__submit_lock.release(submit_lock)
        # Build script to run the command to be submitted
        job_dir = os.path.join(self.__admin_dir,str(job_number))
        logging.debug("Job admin dir     : %s" % job_dir)
        os.mkdir(job_dir)
        cmd_args = [script]
        for arg in args:
            # Quote arguments containing whitespace
            if arg.count(' ') or arg.count('\t'):
                arg = "\"%s\"" % arg
            cmd_args.append(arg)
        cmd = ' '.join(cmd_args)
        job_script = os.path.join(job_dir,"job_script.sh")
        with io.open(job_script,'wt') as fp:
            fp.write(u"""#!{shell}
export BCFTBX_RUNNER_NSLOTS=$NSLOTS
echo "$QUEUE" > {job_dir}/__queue
echo "$BCFTBX_RUNNER_NSLOTS" > {job_dir}/__jobrunner_nslots
{cmd}
exit_code=$?
echo "$exit_code" > {job_dir}/__exit_code.tmp
mv {job_dir}/__exit_code.tmp {job_dir}/__exit_code
exit $exit_code
""".format(shell=self.__shell,job_dir=job_dir,cmd=cmd))
        os.chmod(job_script,0o755)
        # Sanitize name for GE by replacing invalid characters
        # (colon, asterisk...)
        ge_name = self.__ge_name(name)
        logging.debug("GE job name: %s" % ge_name)
        # Build qsub command to submit script
        qsub = ['qsub','-b','y','-V','-N',ge_name]
        if self.__ge_queue:
            qsub.extend(('-q',self.__ge_queue))
        if self.log_dir:
            qsub.extend(('-o',self.log_dir,'-e',self.log_dir))
        if not working_dir:
            qsub.append('-cwd')
        else:
            qsub.extend(('-wd',working_dir))
        if self.__ge_extra_args:
            qsub.extend(self.__ge_extra_args)
        qsub.append(job_script)
        logging.debug("GEJobRunner: qsub command: %s" % qsub)
        # Run the qsub job in the current directory
        cwd = os.getcwd()
        # Check that this exists
        logging.debug("GEJobRunner: executing in %s" % cwd)
        if not os.path.exists(cwd):
            logging.error("GEJobRunner: cwd doesn't exist!")
            return None
        p = subprocess.Popen(qsub,cwd=cwd,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             universal_newlines=True)
        stdoutdata,stderrdata = p.communicate()
        # Check stderr
        error = stderrdata.strip()
        if error:
            # Just echo error message as a warning
            logging.warning("GEJobRunner: '%s'" % error)
        # Capture the job id from the output
        job_id = None
        for line in stdoutdata.split('\n'):
            if line.startswith('Your job'):
                job_id = line.split()[2]
        logging.debug("GEJobRunner: done - job id = %s" % job_id)
        # Store internal number, name and log dir against job id
        if job_id is not None:
            self.__job_number[job_id] = job_number
            self.__names[job_id] = name
            if self.log_dir is None:
                self.__log_dirs[job_id] = working_dir
            else:
                self.__log_dirs[job_id] = self.log_dir
            self.__start_time[job_id] = time.time()
        # Force refresh of job list
        self.__cached_job_list_force_update = True
        # Return the job id
        return job_id

    def terminate(self,job_id):
        """Remove a job from the GE queue using 'qdel'
        """
        logging.debug("GEJobRunner: deleting job")
        qdel=('qdel',job_id)
        p = subprocess.Popen(qdel,stdout=subprocess.PIPE)
        stdoutdata,stderrdata = p.communicate()
        message = stdoutdata.strip()
        logging.debug("GEJobRunner: qdel: %s" % message)
        if job_id in self.__start_time:
            del(self.__start_time[job_id])
        # Write an exit code file for the job
        exit_code_file = os.path.join(self.__admin_dir,
                                      str(self.__job_number[job_id]),
                                      "__exit_code")
        with io.open("%s.tmp" % exit_code_file,'wt') as fp:
            fp.write(u"-1\n")
        os.rename("%s.tmp" % exit_code_file,exit_code_file)
        # Force update of cached job list
        self.__cached_job_list_force_update = True
        return True

    def logFile(self,job_id):
        """Return the log file name for a job

        The name should be '<name>.o<job_id>'
        """
        name = self.__ge_name(self.__names[job_id])
        log_file = "%s.o%s" % (name,job_id)
        if self.__log_dirs[job_id] is not None:
            log_file = os.path.join(self.__log_dirs[job_id],log_file)
        return log_file

    def errFile(self,job_id):
        """Return the error file name for a job

        The name should be '<name>.e<job_id>'
        """
        name = self.__ge_name(self.__names[job_id])
        err_file = "%s.e%s" % (name,job_id)
        if self.__log_dirs[job_id] is not None:
            err_file = os.path.join(self.__log_dirs[job_id],err_file)
        return err_file

    def errorState(self,job_id):
        """Check if the job is in an error state

        Return True if the job is deemed to be in an 'error
        state' (i.e. qstat returns the state as 'E..'),
        False otherwise.
        """
        # Check job is running at all
        if job_id not in self.__job_number:
            return False
        # See if a value was stored for this job
        try:
            return self.__error_state[job_id]
        except KeyError:
            pass
        # Job is in error state if state code starts with E
        in_error_state = self.__job_state_code(job_id).startswith('E')
        if in_error_state:
            self.__error_state[job_id] = True
            return True
        # Not in error state
        return False

    def queue(self,job_id):
        """Fetch the job queue name

        Returns the queue as reported by qstat, or None if
        not found.
        """
        if job_id in self.__queue:
            # Return cached queue
            return self.__queue[job_id]
        # Look for __queue file from job
        queue_file = os.path.join(self.__admin_dir,
                                  str(self.__job_number[job_id]),
                                  "__queue")
        logging.debug("GEJobRunner: queue file: %s" % queue_file)
        if not os.path.exists(queue_file):
            # No queue file available
            logging.debug("GEJobRunner: queue file not found")
            return None
        # Extract queue name from file
        try:
            with io.open(queue_file,'rt') as fp:
                queue = fp.read().strip()
            logging.debug("GEJobRunner: queue: %s" % queue)
        except Exception as ex:
            logging.error("GEJobRunner: exception when reading queue "
                          "for job %s: %s" % (job_id,ex))
            return None
        self.__queue[job_id] = queue
        return queue

    def list(self):
        """
        Get list of job ids which are queued or running
        """
        # Check cached job list
        use_cache = (not self.__cached_job_list_force_update)
        if use_cache:
            if (time.time() - self.__cached_job_list_timestamp) < \
               self.__cached_job_list_lifetime:
                logging.debug("GEJobRunner: using cached job list")
                job_ids = self.__cached_job_list
                # Add the jobs in grace period
                grace_period_jobs = list(self.__start_time.keys())
                for job_id in grace_period_jobs:
                    if job_id not in job_ids:
                        job_ids.append(job_id)
                return job_ids
        # Update jobs in grace period
        for job_id in list(self.__start_time.keys()):
            self.__update_job_grace_period(job_id)
        grace_period_jobs = list(self.__start_time.keys())
        # Build initial list from directory contents
        job_ids = []
        for job_id in list(self.__job_number.keys()):
            try:
                job_number = self.__job_number[job_id]
            except KeyError:
                # Job has been removed since the list was
                # fetched? Ignore
                continue
            job_dir = os.path.join(self.__admin_dir,str(job_number))
            exit_code_file = os.path.join(job_dir,"__exit_code")
            logging.debug("GEJobRunner: checking job %s (#%s)"
                          % (job_id,job_number))
            if os.path.exists(job_dir):
                logging.debug("GEJobRunner: -- found %s" % job_dir)
                # Job dir exists
                if os.path.exists(exit_code_file):
                    # Job has finished, handle completion
                    self.__handle_job_completion(job_id)
                else:
                    # Job still running
                    job_ids.append(job_id)
        # Update cache
        self.__cached_job_list_timestamp = time.time()
        self.__cached_job_list = [j for j in job_ids]
        self.__cached_job_list_force_update = False
        # Add the jobs in the grace period
        for job_id in grace_period_jobs:
            if job_id not in job_ids:
                job_ids.append(job_id)
            else:
                # Job now visible so no longer in grace period
                self.__update_job_grace_period(job_id)
        logging.debug("GEJobRunner: 'list' returning %s" % job_ids)
        return job_ids

    def exit_status(self,job_id):
        """
        Return exit status from command run by a job

        If the job is still running then returns 'None'.
        """
        if self.isRunning(job_id):
            # Return None if job is still running
            return None
        # Check if job is being finalized
        start_time = time.time()
        while job_id in self.__finalizing:
            # Wait until exit_status is ready
            time.sleep(1.0)
            if (time.time() - start_time) > self.__ge_timeout:
                logging.warning("GEJobRunner: timed out waiting "
                                "for job %s to finalize" % job_id)
                return None
        # Return cached exit status
        return self.__exit_status[job_id]

    def __make_admin_dir(self):
        """Internal: create temporary directory for admin etc

        The directory will be created in a '.gejobrunner'
        subdirectory of the current working directory.
        """
        try:
            # Return current value, if set
            return self.__admin_dir
        except AttributeError:
            pass
        # Make new dir in current dir
        parent_dir = os.path.join(os.getcwd(),".gejobrunner")
        try:
            os.mkdir(parent_dir)
        except OSError:
            pass
        admin_dir = tempfile.mkdtemp(dir=parent_dir)
        return admin_dir

    def __clean_up_admin_dir(self):
        """Internal: remove the admin dir

        Shouldn't be called directly; instead register with
        'atexit' to force clean up on program exit
        """
        logging.debug("GEJobRunner: removing admin dir '%s'" %
                      self.__admin_dir)
        # Check if jobs are still being finalized
        start_time = time.time()
        while self.__finalizing:
            # Wait until everything has finalized
            time.sleep(1.0)
            if (time.time() - start_time) > self.__ge_timeout:
                logging.warning("GEJobRunner: timed out waiting "
                                "for jobs to finalize")
                break
        # Try to remove the admin dir and contents
        try:
            shutil.rmtree(self.__admin_dir)
        except Exception as ex:
            logging.warning("GEJobRunner: exception removing "
                            "admin dir '%s': %s" %
                            (self.__admin_dir,ex))

    def __update_job_grace_period(self,job_id):
        """
        Internal: handling update of job in grace period

        Checks if a job is still within the grace period
        (i.e. has an entry in the `__start_time`
        dictionary which is newer than the grace period).

        If the job is no longer in the grace period then
        removes its entry in the `__start_time`
        dictionary.
        """
        logging.debug("GEJobRunner: update grace period for "
                      "for job %s" % job_id)
        lock = None
        while lock is None:
            lock = self.__updating_grace_period.acquire(job_id)
        logging.debug("GEJobRunner: acquired lock for grace period "
                      "update: %s" % lock)
        try:
            start_time = self.__start_time[job_id]
        except KeyError:
            logging.debug("GEJobRunner: update grace period: job %s "
                          "has gone away (ignored)" % job_id)
            self.__updating_grace_period.release(lock)
            return
        if ((time.time() - start_time) > self.__new_job_grace_period):
            # Job no longer in grace period
            logging.debug("GEJobRunner: job %s no longer in grace "
                          "period" % job_id)
            try:
                del(self.__start_time[job_id])
            except KeyError:
                logging.debug("GEJobRunner: update grace period: "
                              "job %s has gone away (ignored)" %
                              job_id)
        # Release update lock
        self.__updating_grace_period.release(lock)

    def __handle_job_completion(self,job_id):
        """
        Internal: deal with completion of job

        Peforms the following operations:

        - checks that an '__exit_code' file exists for
          the job
        - read and store the exit status/return code from
          this file
        - ensure that the queue is set for the job
        - call the clean up function to remove all the
          associated files
        - remove the job from the internal job count

        If the '__exit_code' file associated with the job
        can't be found after a number of attempts to locate
        it, or if the exit status cannot be read from the
        file, then the exit status for the job will be
        set to '127'.
        """
        logging.debug("GEJobRunner: handle job completion for %s"
                      % job_id)
        lock = None
        while lock is None:
            lock = self.__job_lock.acquire(job_id)
        logging.debug("GEJobRunner: acquired lock: %s" % lock)
        if job_id not in self.__job_number:
            # Job has gone away
            logging.debug("GEJobRunner: job %s has gone away" %
                          job_id)
            self.__job_lock.release(lock)
            return
        self.__finalizing[job_id] = True
        # Check there is an exit code file
        exit_code_file = os.path.join(self.__admin_dir,
                                      str(self.__job_number[job_id]),
                                      "__exit_code")
        assert(os.path.exists(exit_code_file))
        try:
            with io.open(exit_code_file,'rt') as fp:
                exit_status = int(fp.read())
        except Exception as ex:
            # Set exit status to 127
            logging.error("GEJobRunner: exception when "
                          "reading exit_status for job "
                          "%s: %s" % (job_id,ex))
            exit_status = 127
        # Update queue information
        self.queue(job_id)
        # Store exit status and clean up
        self.__exit_status[job_id] = exit_status
        self.__clean_up_job(job_id)
        # Release finalization lock
        del(self.__finalizing[job_id])
        # Release job lock
        self.__job_lock.release(lock)

    def __clean_up_job(self,job_id):
        """Internal: clean up internal job files

        Removes the internal directory associated with a job, along
        with any files it contains (e.g. job script, exit code etc).

        This method should only be invoked for jobs that have
        finished running. If the job is still running then returns
        with no action.
        """
        # Do clean up
        logging.debug("GEJobRunner: cleaning up after job %s" % job_id)
        try:
            job_number = self.__job_number[job_id]
        except KeyError:
            logging.error("GEJobRunner: job %d not found, can't do "
                          "clean up" % job_id)
            return
        job_dir = os.path.join(self.__admin_dir,str(job_number))
        try:
            # Remove the directory and contents
            shutil.rmtree(job_dir)
        except Exception as ex:
            logging.warning("GEJobRunner: exception cleaning up for "
                            "job %s (ignored): %s" % (job_id,ex))
        # Clear stored error state
        try:
            del(self.__error_state[job_id])
        except KeyError:
            pass
        # Remove the internally stored job number
        del(self.__job_number[job_id])

    def __run_qstat(self):
        """Internal: run qstat and return data as a list of lists

        Runs 'qstat' command, processes the output and returns a
        list where each item is the data for a job in the form of
        another list, with the items in this list being the data
        returned by qstat.

        NB as 'qstat' calls can be expensive to make, a caching
        mechanism is used which stores the output from 'qstat'
        for a specified period.
        """
        # Should we return the cached data?
        if (time.time() - self.__cached_qstat_output_timestamp) < \
           self.__cached_qstat_output_lifetime:
            logging.debug("GEJobRunner: returning cached qstat output")
            return self.__cached_qstat_output
        # Run qstat and collect the output
        try:
            cmd = ['qstat','-u',os.getlogin()]
        except OSError:
            # os.getlogin() not guaranteed to work in all environments?
            cmd = ['qstat']
        # Run qstat command
        p = subprocess.Popen(cmd,
                             stdout=subprocess.PIPE,
                             universal_newlines=True)
        stdoutdata = p.communicate()[0]
        # Process the output
        qstat_output = []
        # Typical output is:
        # job-ID  prior   name       user         ...<snipped>...
        # ----------------------------------------...<snipped>...
        # 620848 -499.50000 qc       myname       ...<snipped>...
        # ...
        # i.e. 2 header lines then one line per job
        for line in stdoutdata.split('\n'):
            try:
                if line.split()[0].isdigit():
                    qstat_output.append(line.split())
            except IndexError:
                # Skip this line
                pass
        # Update the cache
        self.__cached_qstat_output_timestamp = time.time()
        self.__cached_qstat_output = qstat_output
        return qstat_output

    def __run_qacct(self,job_id):
        """Internal: run qacct and return data as a dictionary

        Runs 'qacct -j' command to get the accounting information
        for the specified job ID, processes the output and returns
        it as a dictionary, for example:

        { 'qname': 'serial.q', 'exit_status': '0', ... }

        The full set of accounting parameters are listed in the
        Grid Engine 'accounting (5)' manpage, for example:

        https://arc.liv.ac.uk/SGE/htmlman/htmlman5/accounting.html

        **Use of this method is deprecated**

        This method is now deprecated for a number of reasons:

        * Use of 'qacct' requires that Grid Engine accounting has
          been turned on, which is not guaranteed.

        * On systems where accounting information is available,
          there may also be a significant delay between job
          completion and the information becoming available via
          'qacct'.

        (According to the documentation this interval is governed
        by the `accounting_flush_time` parameter in the
        `reporting_params` line of the Grid Engine configuration
        file - for example:

        > grep $SGE_ROOT/$SGE_CELL/common/configuration
        reporting_params             accounting=true reporting=false flush_time=00:00:15 joblog=false sharelog=00:00:00
        )

        As a result calls to 'qacct' can be time-consuming and
        expensive to perform, and are best avoided unless absolutely
        necessary.
        """
        cmd = ['qacct','-j',"%s" % job_id]
        # Run the qacct command
        p = subprocess.Popen(cmd,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             universal_newlines=True)
        stdoutdata,stderrdata = p.communicate()
        # Check stderr in case output is not available
        # e.g. "error: job id 18384 not found"
        if stderrdata.startswith("error: job id"):
            logging.debug("Job %s: uable to get qacct info"
                          % job_id)
            return None
        # Process the output
        qacct_dict = {}
        # Typical output is:
        # qname        serial.q
        # hostname     node015.prv.cluster
        # group        users
        # owner        pjb
        # jobname      copy.MH
        # jobnumber    9859
        # taskid       undefined
        # account      sge
        # priority     0
        # qsub_time    Thu Aug 18 11:28:50 2016
        # start_time   Thu Aug 18 11:28:50 2016
        # end_time     Thu Aug 18 12:27:09 2016
        # granted_pe   NONE
        # slots        1
        # failed       0
        # exit_status  0
        # ...
        # i.e. key-value pairs, one pair per line
        for line in p.stdout:
            try:
                i = line.index(" ")
                key = line[:i].strip()
                value = line[i:].strip()
                qacct_dict[key] = value
            except ValueError:
                # Skip this line
                pass
        return qacct_dict

    def __job_state_code(self,job_id):
        """
        Internal: get the state code for a job id

        Will be one of the GE job state codes, or an empty
        string if the job id isn't found.
        """
        # Run qstat and process output to get job states
        logging.debug("GEJobRunner: acquiring state for job %s"
                      % job_id)
        qstat = self.__run_qstat()
        job_ids = []
        job_states = {}
        for job_data in qstat:
            id_ = job_data[0]
            state = job_data[4]
            logging.debug("GEJobRunner: found job %s (state '%s')"
                          % (id_,state))
            if id_ == job_id:
                return state
        # Job not found
        return ""

    def __ge_name(self,name):
        """Internal: sanitize a name for use with GE
        """
        ge_name = str(name)
        for c in ":*@\\?":
            ge_name = ge_name.replace(c,'_')
        if ge_name[0].isdigit():
            # Name cannot start with a digit so
            # prepend an underscore
            ge_name = "_%s" % ge_name
        return ge_name

class SlurmRunner(BaseJobRunner):
    """
    Class implementing job runner for Slurm

    SlurmRunner submits jobs to a Slurm cluster using the 'sbatch'
    command, determines the status of jobs using 'squeue', and
    and terminates them using 'scancel'.

    Additionally the runner can be configured to target a specific
    partition and number of cores on initialisation.

    Each SlurmRunner instance creates a temporary directory which
    it uses for internal admin; this will be removed at program
    exit via 'atexit'.

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
      poll_interval (int): time interval to use when polling Slurm using
        'squeue' etc (default 5s)
      timeout (int): maximum length of time to wait before giving up when
        polling Slurm (default 30s)
    """

    def __init__(self, log_dir=None, nslots=None, partition=None,
                 join_logs=None, slurm_extra_args=None, poll_interval=5.0,
                 timeout=30.0):
        # Internal parameters
        self._name = "SlurmRunner"
        self._admin_dir = None
        self._job_count = 0
        self._shell = "/bin/bash"
        # Directory for log files
        self.set_log_dir(log_dir)
        # Keep track of data (names, log dirs etc) for each job
        self._job_number = {}
        self._names = {}
        self._log_dirs = {}
        self._error_state = {}
        self._exit_status = {}
        self._finalizing = {}
        self._queue = {}
        self._start_time = {}
        # Job id lock
        self._job_lock = ResourceLock()
        # Job grace period lock
        self._updating_grace_period = ResourceLock()
        # Job submission lock
        self._submit_lock = ResourceLock()
        # Cached job list
        self._cached_job_list_lifetime = 2.0
        self._cached_job_list_timestamp = 0.0
        self._cached_job_list = []
        self._cached_job_list_force_update = True
        # Cached qstat output
        self._cached_squeue_output_lifetime = 0.5
        self._cached_squeue_output_timestamp = 0.0
        self._cached_squeue_output = None
        # Grace period for new jobs
        self._new_job_grace_period = 2.0
        # Polling intervals and timeout periods (seconds)
        self._poll_interval = int(poll_interval)
        self._timeout = int(timeout)
        # Handling "missing" jobs (in runner but not in Slurm)
        self._missing = {}
        self._missing_job_timeout = 1.0
        self._missing_job_last_checked = 0.0
        self._missing_job_poll_interval = self._poll_interval*10
        # Register clean up function
        atexit.register(self._clean_up_admin_dir)
        # Slurm-specific variables
        self._join_logs = join_logs
        self._nslots = nslots
        self._partition = partition
        if slurm_extra_args is not None:
            self._slurm_extra_args = [str(x) for x in slurm_extra_args]
        else:
            self._slurm_extra_args = None
        # FIXME clean up extra arguments to remove -n, -p etc?
        self._check_slurm_extra_args()
        # Create admin dir
        self._make_admin_dir()

    def __repr__(self):
        args = []
        if self._nslots:
            args.append(f"nslots={self.nslots}")
        if self._partition:
            args.append(f"partition={self._partition}")
        if self._join_logs:
            args.append(f"join_logs={self.join_logs}")
        if self._slurm_extra_args:
            args.append(f"slurm_args={' '.join(self.slurm_extra_args)}")
        if args:
            return self._name + f"({','.join(args)})"
        else:
            return self._name

    def name(self, job_id):
        """
        Return the name for a specific job

        Arguments:
          job_id (int): Job ID to get the name for
        """
        return self._names[job_id]

    @property
    def nslots(self):
        """
        Return the number of associated slots

        If not set then defaults to 1.
        """
        if self._nslots is None:
            return 1
        else:
            return int(self._nslots)

    @property
    def partition(self):
        """
        Return the assigned partition

        If not set then defaults to 1.
        """
        return self._partition

    @property
    def join_logs(self):
        """
        Return flag for whether to combine stdout and stderr logs

        If not set then defaults to 'False'.
        """
        if self._join_logs is None:
            return False
        else:
            return bool(self._join_logs)

    @property
    def slurm_extra_args(self):
        """
        Return the extra Slurm arguments
        """
        if self._slurm_extra_args:
            return [x for x in self._slurm_extra_args]
        else:
            return None

    def run(self, name, working_dir, script, args):
        """
        Submit a script or command to the cluster via 'sbatch'

        Arguments:
          name (str): name to give the job
          working_dir (str): path to directory to run the job in
          script (str): path to command or script file to run
          args (list): list of arguments to supply to the script

        Returns:
          Job id for submitted job, or 'None' if job failed to
          start.
        """
        logging.debug(f"{self._name:11}: submitting job")
        logging.debug(f"Name       : {name}")
        logging.debug(f"Nslots     : {self.nslots}")
        logging.debug(f"Partition  : {self.partition}")
        logging.debug(f"Join logs  : {self.join_logs}")
        logging.debug(f"Extra args : {self.slurm_extra_args}")
        logging.debug(f"Log dir    : {self.log_dir}")
        logging.debug(f"Working_dir: {working_dir}")
        logging.debug(f"Script     : {script}")
        logging.debug(f"Arguments  : {str(args)}")
        # Wait for lock on job submission
        start_time = time.time()
        submit_lock = None
        while submit_lock is None:
            submit_lock = self._submit_lock.acquire("job_submission",
                                                    timeout=self._timeout)
        # Get internal job number
        self._job_count += 1
        job_number = self._job_count
        logging.debug("Internal job count: %s" % job_number)
        # Release the lock
        self._submit_lock.release(submit_lock)
        # Build script to run the command to be submitted
        job_dir = os.path.join(self._admin_dir, str(job_number))
        logging.debug("Job admin dir     : %s" % job_dir)
        os.mkdir(job_dir)
        cmd_args = [script]
        for arg in args:
            # Quote arguments containing whitespace
            if arg.count(' ') or arg.count('\t'):
                arg = "\"%s\"" % arg
            cmd_args.append(arg)
        cmd = ' '.join(cmd_args)
        job_script = os.path.join(job_dir, "job_script.sh")
        with open(job_script, "wt") as fp:
            fp.write(u"""#!{shell}
export BCFTBX_RUNNER_NSLOTS=$SLURM_NTASKS
echo "$BCFTBX_RUNNER_NSLOTS" > {job_dir}/__jobrunner_nslots
{cmd}
exit_code=$?
echo "$exit_code" > {job_dir}/__exit_code.tmp
mv {job_dir}/__exit_code.tmp {job_dir}/__exit_code
exit $exit_code
""".format(shell=self._shell, job_dir=job_dir, cmd=cmd))
        os.chmod(job_script,0o755)
        job_name = self._sanitize_job_name(name)
        logging.debug("Slurm job name: %s" % job_name)
        # Log file (replicate Grid Engine)
        stdout = "%x.o%j"
        if self.log_dir:
            stdout = os.path.join(self.log_dir, stdout)
        if self.join_logs:
            stderr = None
        else:
            stderr = "%x.e%j"
            if self.log_dir:
                stderr = os.path.join(self.log_dir, stderr)
        # Build sbatch command to submit script
        sbatch = ["sbatch",
                  "--export=ALL",
                  "-J", job_name,
                  "-n", str(self.nslots)]
        if self._partition:
            sbatch.extend(["-p", self._partition])
        sbatch.extend(["-o", stdout])
        if stderr:
            sbatch.extend(["-e", stderr])
        if working_dir:
            sbatch.extend(('--chdir',working_dir))
        if self.slurm_extra_args:
            sbatch.extend(self.slurm_extra_args)
        sbatch.append(job_script)
        logging.debug("SlurmRunner: sbatch command: %s" % sbatch)
        # Run the sbatch job in the current directory
        cwd = os.getcwd()
        if not os.path.exists(cwd):
            logging.error("SlurmRunner: cwd doesn't exist!")
            return None
        logging.debug("SlurmRunner: executing in %s" % cwd)
        p = subprocess.Popen(sbatch, cwd=cwd,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             universal_newlines=True)
        stdoutdata, stderrdata = p.communicate()
        logging.debug(f"SlurmRunner: sbatch output: {stdoutdata}")
        logging.debug(f"SlurmRunner: sbatch error: {stderrdata}")
        # Check stderr to try and detect error with submission
        error = stderrdata.strip()
        if error:
            # Just echo error message as a warning
            logging.warning("SlurmRunner: '%s'" % error)
        # Capture the job id from the output
        job_id = None
        for line in stdoutdata.split('\n'):
            if line.startswith("Submitted batch job"):
                job_id = line.split()[-1]
        if job_id is None:
            logging.error("SlurmRunner: failed to get job ID from "
                          "sbatch output: %r" % stdoutdata)
        logging.debug(f"SlurmRunner: done - job id = {job_id}")
        # Store internal number, name and log dir against job id
        if job_id is not None:
            self._job_number[job_id] = job_number
            self._names[job_id] = name
            if self.log_dir is None:
                self._log_dirs[job_id] = working_dir
            else:
                self._log_dirs[job_id] = self.log_dir
            self._start_time[job_id] = time.time()
        # Force refresh of job list
        self._cached_job_list_force_update = True
        # Return the job id
        return job_id

    def terminate(self, job_id, exit_code=-1):
        """
        Remove a job from the Slurm queue using 'scancel'
        """
        logging.debug("SlurmRunner: deleting job")
        scancel=("scancel", job_id)
        p = subprocess.Popen(scancel, stdout=subprocess.PIPE)
        stdoutdata, stderrdata = p.communicate()
        message = stdoutdata.strip()
        logging.debug("Slurmrunner: scancel: %s" % message)
        if job_id in self._start_time:
            del(self._start_time[job_id])
        # Write an exit code file for the job
        exit_code_file = os.path.join(self._admin_dir,
                                      str(self._job_number[job_id]),
                                      "__exit_code")
        with open("%s.tmp" % exit_code_file, "wt") as fp:
            fp.write(f"{exit_code}\n")
        os.rename("%s.tmp" % exit_code_file, exit_code_file)
        # Force update of cached job list
        self._cached_job_list_force_update = True
        return True

    def logFile(self, job_id):
        """
        Return the log file name for a job

        The name should be '<name>.o<job_id>'
        """
        name = self._names[job_id]
        log_file = "%s.o%s" % (name, job_id)
        if self._log_dirs[job_id] is not None:
            log_file = os.path.join(self._log_dirs[job_id], log_file)
        return log_file

    def errFile(self, job_id):
        """
        Return the error file name for a job

        The name should be '<name>.e<job_id>'
        """
        if self.join_logs:
            return self.logFile(job_id)
        name = self._names[job_id]
        err_file = "%s.e%s" % (name,job_id)
        if self._log_dirs[job_id] is not None:
            err_file = os.path.join(self._log_dirs[job_id], err_file)
        return err_file

    def errorState(self,job_id):
        """
        Check if the job is in an error state

        Return True if the job is deemed to be in an 'error
        state', False otherwise.
        """
        # FIXME don't know how to detect error state for Slurm job
        logging.debug("SlurmRunner: 'errorState' method not implemented")
        return False

    def list(self):
        """
        Get list of job ids which are queued or running
        """
        # Check cached job list
        use_cache = (not self._cached_job_list_force_update and
                     (time.time() - self._cached_job_list_timestamp) <
                     self._cached_job_list_lifetime)
        if use_cache:
            logging.debug("SlurmRunner: using cached job list")
            job_ids = self._cached_job_list
            # Add the jobs in grace period
            for job_id in self._grace_period_jobs():
                if job_id not in job_ids:
                    job_ids.append(job_id)
            return job_ids
        else:
            logging.debug("SlurmRunner: building job list")
        # Update jobs in grace period
        for job_id in self._grace_period_jobs():
            self._update_job_in_grace_period(job_id)
        # Build initial list from directory contents
        job_ids = []
        for job_id in list(self._job_number.keys()):
            logging.debug(f"SlurmRunner: -- checking job {job_id}")
            try:
                job_number = self._job_number[job_id]
            except KeyError:
                # Job has been removed since the list was
                # fetched? Ignore
                continue
            job_dir = os.path.join(self._admin_dir, str(job_number))
            if os.path.exists(job_dir):
                # Job dir exists
                logging.debug("SlurmRunner: -- found %s" % job_dir)
                exit_code_file = os.path.join(job_dir, "__exit_code")
                if os.path.exists(exit_code_file):
                    # Job has finished, handle completion
                    logging.debug("SlurmRunner: -- exit code file exists, "
                                  f"completing job {job_id}")
                    self._handle_job_completion(job_id)
                else:
                    # Job still running
                    logging.debug("SlurmRunner: -- no exit code file, "
                                  f"{job_id} still running")
                    job_ids.append(job_id)
        # Check for "missing" jobs that are in the runner but no
        # longer in the Slurm system
        jobs_still_in_grace_period = bool(self._grace_period_jobs())
        if job_ids and not jobs_still_in_grace_period:
            check_missing_jobs = ((time.time() -
                                   self._missing_job_last_checked) >
                                  self._missing_job_poll_interval)
            if check_missing_jobs:
                logging.debug(f"SlurmRunner: checking for missing jobs")
                job_ids = self._handle_missing_jobs(job_ids)
        # Update cache
        logging.debug("SlurmRunner: updating the cache")
        self._cached_job_list_timestamp = time.time()
        self._cached_job_list = [j for j in job_ids]
        self._cached_job_list_force_update = False
        # Add the jobs in the grace period
        for job_id in self._grace_period_jobs():
            if job_id not in job_ids:
                job_ids.append(job_id)
            else:
                # Job now visible so no longer in grace period
                self._update_job_in_grace_period(job_id)
        logging.debug("SlurmRunner: 'list' returning %s" % job_ids)
        return job_ids

    def exit_status(self,job_id):
        """
        Return exit status from command run by a job

        If the job is still running then returns 'None'.
        """
        if self.isRunning(job_id):
            # Return None if job is still running
            return None
        # Check if job is being finalized
        start_time = time.time()
        while job_id in self._finalizing:
            # Wait until exit_status is ready
            time.sleep(1.0)
            if (time.time() - start_time) > self._timeout:
                logging.warning("SlurmRunner: timed out waiting "
                                "for job %s to finalize" % job_id)
                return None
        # Return cached exit status
        return self._exit_status[job_id]

    def _make_admin_dir(self):
        """
        Internal: create temporary directory for admin

        The directory will be created in a subdirectory of
        the current working directory.
        """
        if self._admin_dir:
            # Return current value, if set
            return self._admin_dir
        # Create a new temporary directory
        self._admin_dir = tempfile.mkdtemp(prefix=".slurmrunner.",
                                           dir=os.getcwd())
        return self._admin_dir

    def _clean_up_admin_dir(self):
        """
        Internal: remove the admin dir

        Shouldn't be called directly; instead register with
        'atexit' to force clean up on program exit
        """
        logging.debug("SlurmRunner: removing admin dir '%s'" %
                      self._admin_dir)
        # Check if jobs are still being finalized
        start_time = time.time()
        while self._finalizing:
            # Wait until everything has finalized
            time.sleep(1.0)
            if (time.time() - start_time) > self._timeout:
                logging.warning("SlurmRunner: timed out waiting "
                                "for jobs to finalize")
                break
        # Try to remove the admin dir and contents
        try:
            shutil.rmtree(self._admin_dir)
        except Exception as ex:
            logging.warning("SlurmRunner: exception removing "
                            "admin dir '%s': %s" %
                            (self._admin_dir, ex))

    def _grace_period_jobs(self):
        """
        Internal: return list of jobs in the grace period

        Returns list of job IDs where each job has an entry
        in the `_start_time` dictionary which is newer than
        the grace period timeout.
        """
        return list(self._start_time.keys())

    def _update_job_in_grace_period(self,job_id):
        """
        Internal: handling update of job in grace period

        Checks if a job is still within the grace period
        (i.e. has an entry in the `_start_time`
        dictionary which is newer than the grace period).

        If the job is no longer in the grace period then
        removes its entry in the `_start_time`
        dictionary.
        """
        logging.debug("SlurmRunner: checking if job %s is still in "
                      "grace period" % job_id)
        lock = None
        while lock is None:
            lock = self._updating_grace_period.acquire(job_id)
        logging.debug("SlurmRunner: acquired lock for grace period "
                      "update: %s" % lock)
        try:
            start_time = self._start_time[job_id]
        except KeyError:
            logging.debug("SlurmRunner: update grace period: job %s "
                          "has gone away (ignored)" % job_id)
            self._updating_grace_period.release(lock)
            return
        if ((time.time() - start_time) > self._new_job_grace_period):
            # Job no longer in grace period
            logging.debug("SlurmRunner: job %s no longer in grace "
                          "period" % job_id)
            try:
                del(self._start_time[job_id])
            except KeyError:
                logging.debug("SlurmRunner: update grace period: "
                              "job %s has gone away (ignored)" %
                              job_id)
        # Release update lock
        self._updating_grace_period.release(lock)

    def _handle_missing_jobs(self, job_list):
        """
        Internal: handle any jobs in runner missing from Slurm

        Jobs present in the runner are checked to see if they
        are also present in Slurm, with jobs that are missing
        being flagged initially and then removed from the runner
        if still missing after a "timeout" period.

        Arguments:
          job_list (list): list of job IDs to check

        Returns:
          List: updated list of job IDs with missing jobs
            removed.
        """
        updated_job_list = []
        squeue_jobs = [j[0] for j in self._run_squeue()]
        for job_id in job_list:
            if job_id not in squeue_jobs:
                logging.debug(f"SlurmRunner: job {job_id} has gone away?")
                if job_id not in self._missing:
                    # Set time when job went missing
                    self._missing[job_id] = time.time()
                    updated_job_list.append(job_id)
                elif (time.time() - self._missing[job_id]) > \
                     self._missing_job_timeout:
                    # Job is still missing after interval, terminate it
                    logging.debug(f"SlurmRunner: forcing job completion "
                                  f"for missing job {job_id} from runner "
                                  f"(timeout was exceeded)")
                    self.terminate(job_id, exit_code=127)
                    # Perform immediate job completion
                    self._handle_job_completion(job_id)
                    # Remove the "missing" flag
                    del(self._missing[job_id])
            else:
                # Job is no longer missing?
                logging.debug(f"SlurmRunner: previously missing job {job_id} "
                              f"has come back?")
                updated_job_list.append(job_id)
                if job_id in self._missing:
                    del(self._missing[job_id])
        return updated_job_list

    def _handle_job_completion(self,job_id):
        """
        Internal: deal with completion of job

        Peforms the following operations:

        - checks that an '__exit_code' file exists for
          the job
        - read and store the exit status/return code from
          this file
        - ensure that the queue is set for the job
        - call the clean up function to remove all the
          associated files
        - remove the job from the internal job count

        If the '__exit_code' file associated with the job
        can't be found after a number of attempts to locate
        it, or if the exit status cannot be read from the
        file, then the exit status for the job will be
        set to '127'.
        """
        logging.debug("SlurmRunner: handle job completion for %s"
                      % job_id)
        lock = None
        while lock is None:
            lock = self._job_lock.acquire(job_id)
        logging.debug("SlurmRunner: acquired lock: %s" % lock)
        if job_id not in self._job_number:
            # Job has gone away
            logging.debug("SlurmRunner: job %s has gone away" %
                          job_id)
            self._job_lock.release(lock)
            return
        self._finalizing[job_id] = True
        # Check there is an exit code file
        exit_code_file = os.path.join(self._admin_dir,
                                      str(self._job_number[job_id]),
                                      "__exit_code")
        assert(os.path.exists(exit_code_file))
        try:
            with open(exit_code_file,'rt') as fp:
                exit_status = int(fp.read())
        except Exception as ex:
            # Set exit status to 127
            logging.error("SlurmRunner: exception when "
                          "reading exit_status for job "
                          "%s: %s" % (job_id, ex))
            exit_status = 127
        # Store exit status and clean up
        self._exit_status[job_id] = exit_status
        self._clean_up_job(job_id)
        # Release finalization lock
        del(self._finalizing[job_id])
        # Release job lock
        self._job_lock.release(lock)

    def _clean_up_job(self,job_id):
        """
        Internal: clean up internal job files

        Removes the internal directory associated with a job, along
        with any files it contains (e.g. job script, exit code etc).

        This method should only be invoked for jobs that have
        finished running. If the job is still running then returns
        with no action.
        """
        # Do clean up
        logging.debug("SlurmRunner: cleaning up after job %s" % job_id)
        try:
            job_number = self._job_number[job_id]
        except KeyError:
            logging.error("SlurmRunner: job %d not found, can't do "
                          "clean up" % job_id)
            return
        job_dir = os.path.join(self._admin_dir, str(job_number))
        try:
            # Remove the directory and contents
            shutil.rmtree(job_dir)
        except Exception as ex:
            logging.warning("SlurmRunner: exception cleaning up for "
                            "job %s (ignored): %s" % (job_id, ex))
        # Clear stored error state
        try:
            del(self._error_state[job_id])
        except KeyError:
            pass
        # Remove the internally stored job number
        del(self._job_number[job_id])

    def _run_squeue(self):
        """
        Internal: run squeue and return data as a list of lists

        Runs 'squeue' command, processes the output and returns a
        list where each item is the data for a job in the form of
        another list, with the items in this list being the data
        returned by squeue.

        NB as 'squeue' calls can be relatively expensive to make,
        the output from 'squeue' is cached for a specified period
        before being refreshed.
        """
        # Should we return the cached data?
        if (time.time() - self._cached_squeue_output_timestamp) < \
           self._cached_squeue_output_lifetime:
            logging.debug("SlurmRunner: returning cached squeue output")
            return self._cached_squeue_output
        # Run squeue and collect the output
        try:
            cmd = ["squeue", "--user", os.getlogin()]
        except OSError:
            # os.getlogin() not guaranteed to work in all environments?
            cmd = ["squeue", "--me"]
        # Run squeue command
        p = subprocess.Popen(cmd,
                             stdout=subprocess.PIPE,
                             universal_newlines=True)
        stdoutdata = p.communicate()[0]
        logging.debug(f"SlurmRunner: output from 'squeue': {stdoutdata}")
        # Process the output
        squeue_output = []
        # Output has a header line with field names then one
        # line per job
        lines = stdoutdata.rstrip("\n").split("\n")
        fields = lines[0].split()
        idx_jobid = fields.index("JOBID")
        idx_state = fields.index("ST")
        for line in lines[1:]:
            # Store tuples of jobid, state
            data = line.split()
            try:
                squeue_output.append((data[idx_jobid], data[idx_state]))
            except IndexError:
                logging.debug(f"SlurmRunner: failed to parse 'squeue' "
                              f"output: '{line}' (ignored)")
        # Update the cache
        self._cached_squeue_output_timestamp = time.time()
        self._cached_squeue_output = squeue_output
        return squeue_output

    def _job_state_code(self, job_id):
        """
        Internal: get the state code for a job id

        Will be one of the Slurm job state codes, or an empty
        string if the job id isn't found.
        """
        # Run squeue and process output to get job states
        logging.debug("SlurmRunner: acquiring state for job %s"
                      % job_id)
        squeue = self._run_squeue()
        job_ids = []
        job_states = {}
        for job_data in squeue:
            id_ = job_data[0]
            state = job_data[1]
            logging.debug(f"SlurmRunner: found job {id_} (state '{state}')")
            if id_ == job_id:
                return state
        # Job not found
        return ""

    def _sanitize_job_name(self, name):
        """
        Internal: sanitize a job name for use with Slurm

        This is copied from the GE runner
        """
        sanitized_name = str(name)
        for c in ":*@\\?":
            sanitized_name = sanitized_name.replace(c,'_')
        if sanitized_name[0].isdigit():
            # If name starts with a digit then prepend
            # an underscore
            sanitized_name = f"_{sanitized_name}"
        return sanitized_name

    def _check_slurm_extra_args(self):
        """
        Internal: check extra arguments provided for Slurm

        The -n and -p options implicitly set the number of
        slots and the target partition, but only if not
        explicitly set when the runner was instantiated
        (otherwise an exception is raised).

        The extra arguments list is updated to remove the
        explicit -n and -p options.

        The -J, -o, -e and --export options are reserved for
        exclusive use by the runner so if these are specified
        then an exception is raised.
        """
        if self._slurm_extra_args is None:
            return
        args = [x for x in self._slurm_extra_args]
        new_args = []
        while args:
            # Grab first argument and update the list
            arg = args[0]
            args = args[1:]
            # Check for specific arguments
            if arg == "-n":
                if self._nslots is None:
                    self._nslots = int(args[0])
                    args = args[1:]
                else:
                    raise Exception(f"SlurmRunner: '-n' not permitted "
                                    f"in extra arguments if nslots is set")
            elif arg == "-p":
                if self._partition is None:
                    self._partition = str(args[0])
                    args = args[1:]
                else:
                    raise Exception(f"SlurmRunner: '-p' not permitted "
                                    f"in extra arguments if partition is set")
            elif arg in ("-J", "-o", "-e") or \
                 arg == "--export" or arg.startswith("--export="):
                raise Exception(f"SlurmRunner: '{arg}' not permitted "
                                f"in extra arguments")
            else:
                new_args.append(arg)
        # Update the extra arguments
        self._slurm_extra_args = new_args


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
        logging.debug("ResourceLock: attempting to get lock for "
                      "resource '%s'" % resource_name)
        start_time = time.time()
        has_lock = False
        while not has_lock:
            # Assume we have the lock, until proven otherwise
            has_lock = True
            # Register a putative lock
            lock = self._get_lock_name(resource_name)
            self._locks[lock] = True
            logging.debug("ResourceLock: made new lock '%s'" % lock)
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
                        logging.debug("ResourceLock: resource '%s' already "
                                      "locked" % resource_name)
                        # Remove attempted lock
                        self.release(lock)
                        return None
                    elif ts == timestamp:
                        # Deadlock: two locks with same priority
                        logging.debug("ResourceLock: two locks with same "
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
        logging.debug("ResourceLock: acquired lock: '%s'" % lock)
        return lock

    def release(self,lock):
        """
        Release a lock on a resource

        Arguments:
          lock (str): lock to release.
        """
        logging.debug("ResourceLock: releasing '%s'" % lock)
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
