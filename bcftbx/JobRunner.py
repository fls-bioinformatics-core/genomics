#!/usr/bin/env python
#
#     JobRunner.py: classes for starting and managing job runs
#     Copyright (C) University of Manchester 2011-2018 Peter Briggs
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
* DRMAAJobRunner : run jobs using the DRMAA interface to Grid Engine

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

"""

#######################################################################
# Import modules that this module depends on
#######################################################################

import os
import logging
import subprocess
import time
import tempfile
import shutil
import atexit
try:
    import drmaa
except ImportError:
    # No drmaa module
    pass
except Exception, ex:
    # DRMAA_LIBRARY_PATH not defined or invalid
    logging.warning("Exception from dramma module: %s", ex)
    pass

#######################################################################
# Classes
#######################################################################

class BaseJobRunner(object):
    """Base class for implementing job runners

    This class can be used as a template for implementing custom
    job runners. The idea is that the runners wrap the specifics
    of interacting with an underlying job control system and thus
    provide a generic interface to be used by higher level classes.

    A job runner needs to implement the following methods:

      run        : starts a job running
      terminate  : kills a running job
      list       : lists the running job ids
      logFile    : returns the name of the log file for a job
      errFile    : returns the name of the error file for a job
      exit_status: returns the exit status for the command (or
                   None if the job is still running)

    Optionally it can also implement the methods:

      errorState: indicates if running job is in an "error state"
      isRunning : checks if a specific job is running

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

    def __init__(self,log_dir=None,join_logs=False):
        """Create a new SimpleJobRunner instance

        Arguments:
          log_dir: Directory to write log files to (set to 'None' to use
                   cwd)
          join_logs: Combine stderr and stdout into a single log file (by
                   default stdout and stderr have their own log files)

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
        # Keep track of log files etc
        self.__log_files = {}
        self.__err_files = {}
        self.__exit_status = {}
        self.__job_popen = {}

    def __repr__(self):
        return 'SimpleJobRunner'

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
        logging.debug("Script     : %s" % script)
        logging.debug("Arguments  : %s" % str(args))
        # Build command to be submitted
        cmd = [script]
        cmd.extend(args)
        # Capture current dir
        current_dir = os.getcwd()
        if working_dir:
            # Move to working directory
            os.chdir(working_dir)
        logging.debug("RunScript: command: %s" % cmd)
        cwd = os.getcwd()
        # Check that this exists
        logging.debug("RunScript: executing in %s" % cwd)
        if not os.path.exists(cwd):
            logging.error("RunScript: cwd doesn't exist!")
            return None
        # Set up log files
        lognames = self.__assign_log_files(name,working_dir)
        log = open(lognames[0],'w')
        if not self.__join_logs:
            err = open(lognames[1],'w')
        else:
            err = subprocess.STDOUT
        # Start the subprocess
        p = subprocess.Popen(cmd,cwd=cwd,stdout=log,stderr=err)
        # Capture the job id from the output
        job_id = str(p.pid)
        logging.debug("RunScript: done - job id = %s" % job_id)
        # Do internal house keeping
        self.__job_list.append(job_id)
        self.__log_files[job_id] = lognames[0]
        self.__job_popen[job_id] = p
        if not self.__join_logs:
            self.__err_files[job_id] = lognames[1]
        else:
            self.__err_files[job_id] = None
        # Return to original dir if necessary
        if working_dir:
            # Move to working directory
            os.chdir(current_dir)
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
            p = self.__job_popen[job_id]
            status = p.poll()
            if status is None:
                job_ids.append(job_id)
            else:
                logging.debug("Job id %s: finished (%s)" % (job_id,
                                                            status))
                self.__exit_status[job_id] = status
                try:
                    del(self.__job_popen[job_id])
                except KeyError:
                    logging.warning("Job id %s: already deleted"
                                    % job_id)
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
            log_dir = os.getcwd()
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
        self.__queue = queue
        # Directory for log files
        self.set_log_dir(log_dir)
        # Keep track of data (names, log dirs etc) for each job
        self.__job_number = {}
        self.__names = {}
        self.__log_dirs = {}
        self.__exit_status = {}
        self.__start_time = {}
        self.__ge_extra_args = ge_extra_args
        # Cached job list
        self.__cached_job_list_lifetime = 2.0
        self.__cached_job_list_timestamp = 0.0
        self.__cached_job_list = []
        self.__cached_job_list_force_update = True
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
        logging.debug("Queue      : %s" % self.__queue)
        logging.debug("Extra args : %s" % self.__ge_extra_args)
        logging.debug("Log dir    : %s" % self.log_dir)
        logging.debug("Working_dir: %s" % working_dir)
        logging.debug("Script     : %s" % script)
        logging.debug("Arguments  : %s" % str(args))
        # Build script to run the command to be submitted
        self.__job_count += 1
        logging.debug("Internal job count: %s" % self.__job_count)
        job_dir = os.path.join(self.__admin_dir,str(self.__job_count))
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
        with open(job_script,'w') as fp:
            fp.write("""#!%s
%s
exit_code=$?
echo "$exit_code" > %s/__exit_code
exit $exit_code
""" % (self.__shell,cmd,job_dir))
        os.chmod(job_script,0755)
        # Sanitize name for GE by replacing invalid characters
        # (colon, asterisk...)
        ge_name = self.__ge_name(name)
        logging.debug("GE job name: %s" % ge_name)
        # Build qsub command to submit script
        qsub = ['qsub','-b','y','-V','-N',ge_name]
        if self.__queue:
            qsub.extend(('-q',self.__queue))
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
                             stderr=subprocess.PIPE)
        p.wait()
        # Check stderr
        error = p.stderr.read().strip()
        if error:
            # Just echo error message as a warning
            logging.warning("GEJobRunner: '%s'" % error)
        # Capture the job id from the output
        job_id = None
        for line in p.stdout:
            if line.startswith('Your job'):
                job_id = line.split()[2]
        logging.debug("GEJobRunner: done - job id = %s" % job_id)
        # Store internal number, name and log dir against job id
        if job_id is not None:
            self.__job_number[job_id] = self.__job_count
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
        p.wait()
        message = p.stdout.read()
        logging.debug("GEJobRunner: qdel: %s" % message)
        if job_id in self.__start_time:
            del(self.__start_time[job_id])
        self.__exit_status[job_id] = -1
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
        # Job is in error state if state code starts with E
        return self.__job_state_code(job_id).startswith('E')

    def queue(self,job_id):
        """Fetch the job queue name

        Returns the queue as reported by qstat, or None if
        not found.
        """
        jobs = self.__run_qstat()
        for job_data in jobs:
            # Id is first item, Queue is 8th item for each job
            if job_data[0] == job_id:
                try:
                    return job_data[7]
                except Exception:
                    return None
        # No match
        return None

    def list(self):
        """Get list of job ids in the queue.
        """
        # Check cached job list
        use_cache = (not self.__cached_job_list_force_update)
        if use_cache:
            if (time.time() - self.__cached_job_list_timestamp) < \
               self.__cached_job_list_lifetime:
                logging.debug("GEJobRunner: using cached job list")
                job_ids = self.__cached_job_list
                # Add the jobs in grace period
                grace_period_jobs = self.__start_time.keys()
                for job_id in grace_period_jobs:
                    if job_id not in job_ids:
                        job_ids.append(job_id)
                return job_ids
        # Sort out jobs which are still in "grace period"
        # i.e. they have been submitted but might not show up
        # in qstat output yet
        now = time.time()
        for job_id in self.__start_time.keys():
            if ((now - self.__start_time[job_id]) >
                self.__new_job_grace_period):
                # Job no longer in grace period
                logging.debug("GEJobRunner: job %s no longer in grace "
                              "period" % job_id)
                del(self.__start_time[job_id])
        grace_period_jobs = self.__start_time.keys()
        logging.debug("GEJobRunner: jobs in grace period: %s" %
                      grace_period_jobs)
        # Run qstat and process the output to get job ids
        logging.debug("GEJobRunner: refreshing job list")
        jobs = self.__run_qstat()
        job_ids = []
        for job_data in jobs:
            # Check for state being 'r' (=running), or 'S' (=suspended),
            # or 'qw'(=queued, waiting), 't' (=transferring)
            # **or**
            # Starts with 'E' (=error, e.g. 'Eqw') or 'd' (=deleted,
            # e.g. 'dr')
            if job_data[4] in ('r','S','qw','t') or \
               job_data[4][0] in ('E','d'):
                # Id is first item for each job
                job_ids.append(job_data[0])
        # Update cache
        self.__cached_job_list_timestamp = time.time()
        self.__cached_job_list = [j for j in job_ids]
        self.__cached_job_list_force_update = False
        # Add the jobs in grace period
        for job_id in grace_period_jobs:
            if job_id not in job_ids:
                job_ids.append(job_id)
            else:
                # Job now appearing in qstat output
                # so can remove from grace period
                del(self.__start_time[job_id])
        return job_ids

    def exit_status(self,job_id):
        """Return exit status from command run by a job

        Attempts to read the exit status/return code for
        a job.

        The exit status is read from the '__exit_code'
        file associated with the job; if this file can't
        be found after a number of attempts to locate it
        - or if the exit status cannot be read from the
        file - then the exit status for the job will be
        set to '127'.

        Once the exit status has been read from the file,
        the value is cached and the files will be removed;
        future calls to 'exit_status' will return the
        cached value.

        If the job is still running then returns 'None'.
        """
        if job_id in self.__exit_status:
            # Return cached exit status
            return self.__exit_status[job_id]
        if self.isRunning(job_id):
            # Return None if job is still running
            return None
        # Look for __exit_code file from job
        exit_code_file = os.path.join(self.__admin_dir,
                                      str(self.__job_number[job_id]),
                                      "__exit_code")
        retries = 0
        while not os.path.exists(exit_code_file):
            # Check for time out
            if (retries*self.__ge_poll_interval) > self.__ge_timeout:
                logging.debug("GEJobRunner: timed out waiting for "
                              "exit code file (%d attempts made)" %
                              retries)
                break
            # Wait before trying again
            time.sleep(self.__ge_poll_interval)
            retries += 1
        # Extract exit code from file and clean up
        try:
            with open(exit_code_file,'r') as fp:
                exit_status = int(fp.read())
        except Exception as ex:
            logging.error("GEJobRunner: exception when reading exit_status "
                          "for job %s: %s" % (job_id,ex))
            # Set exit status
            exit_status = 127
        # Set internally
        self.__exit_status[job_id] = exit_status
        self.__clean_up_job(job_id)
        return exit_status

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
        try:
            shutil.rmtree(self.__admin_dir)
        except Exception as ex:
            logging.warning("GEJobRunner: exception removing "
                            "admin dir '%s': %s" %
                            (self.__admin_dir,ex))

    def __clean_up_job(self,job_id):
        """Internal: clean up internal job files

        Removes the internal directory associated with a job, along
        with any files it contains (e.g. job script, exit code etc).

        This method should only be invoked for jobs that have
        finished running. If the job is still running then returns
        with no action.
        """
        # Check job is not still running
        if self.isRunning(job_id):
            logging.warning("GEJobRunner: ignored attempt to clean up "
                            "job %s while still running" % job_id)
            return
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

    def __run_qstat(self):
        """Internal: run qstat and return data as a list of lists

        Runs 'qstat' command, processes the output and returns a
        list where each item is the data for a job in the form of
        another list, with the items in this list being the data
        returned by qstat.
        """
        try:
            cmd = ['qstat','-u',os.getlogin()]
        except OSError:
            # os.getlogin() not guaranteed to work in all environments?
            cmd = ['qstat']
        # Run qstat command
        p = subprocess.Popen(cmd,stdout=subprocess.PIPE)
        p.wait()
        # Process the output
        jobs = []
        # Typical output is:
        # job-ID  prior   name       user         ...<snipped>...
        # ----------------------------------------...<snipped>...
        # 620848 -499.50000 qc       myname       ...<snipped>...
        # ...
        # i.e. 2 header lines then one line per job
        for line in p.stdout:
            try:
                if line.split()[0].isdigit():
                    jobs.append(line.split())
            except IndexError:
                # Skip this line
                pass
        return jobs

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
                             stderr=subprocess.PIPE)
        p.wait()
        # Check stderr in case output is not available
        # e.g. "error: job id 18384 not found"
        stderr = p.stderr.read()
        if stderr.startswith("error: job id"):
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
        """Internal: get the state code for the specified job id

        Will be one of the GE job state codes, or an empty
        string if the job id isn't found.
        """
        jobs = self.__run_qstat()
        for job_data in jobs:
            if job_data[0] == job_id:
                # State code is index 4
                return job_data[4]
        # Job not found
        return ''

    def __ge_name(self,name):
        """Internal: sanitize a name for use with GE
        """
        ge_name = str(name)
        for c in ":*":
            ge_name = ge_name.replace(c,'_')
        return ge_name

class DRMAAJobRunner(BaseJobRunner):
    """Class implementing job runner using DRMAA

    DRMAAJobRunner submits jobs to a Grid Engine cluster using the
    Python interface to Distributed Resource Management Application
    API (DRMAA), as an alternative to the GEJobRunner.

    The DRMAAJobRunner requires:
    - the drmaa libraries (e.g. libdrmaa.so), pointed to by the
      environment variable DRMAA_LIBRARY_PATH
    - the Python drmma library, see http://code.google.com/p/drmaa-python/
    """

    def __init__(self,queue=None):
        """Create a new DRMAAJobRunner instance

        Arguments:
          queue: Name of GE queue to use (set to 'None' to use default queue)
        """
        self.__queue = queue
        self.__names = {}
        # Initialise DRMAA session
        self.__session = drmaa.Session()
        self.__session.initialize()

    def __repr__(self):
        return 'DRMAAJobRunner'

    def __del__(self):
        # Clean up on object deletion
        if self.__session: self.__session.exit()

    def run(self,name,working_dir,script,args):
        """Submit a script or command to the cluster via DRMAA

        Arguments:
          name: Name to give the job
          working_dir: Directory to run the job in
          script: Script file to run
          args: List of arguments to supply to the script

        Returns:
          Job id for submitted job, or 'None' if job failed to
          start.
        """
        logging.debug("DRMAAJobRunner: submitting job")
        logging.debug("Name       : %s" % name)
        logging.debug("Queue      : %s" % self.__queue)
        logging.debug("Working_dir: %s" % working_dir)
        logging.debug("Script     : %s" % script)
        logging.debug("Arguments  : %s" % str(args))
        # Create a job template
        jt = self.__session.createJobTemplate()
        # Build command within the job template
        jt.remoteCommand = script
        jt.args = args
        jt.joinFiles = True
        # Add the options to normally used for qsub
        qsub_args = "-b y -V -N %s" % name
        if self.__queue:
            qsub_args += " -q %s" % self.__queue
        if not working_dir:
            qsub_args += " -cwd"
        else:
            qsub_args += " -wd %s" % working_dir
        logging.debug("Qsub_args = %s" % qsub_args)
        jt.nativeSpecification = qsub_args
        # Submit the job
        job_id = self.__session.runJob(jt)
        # Clean up - delete the job template
        self.__session.deleteJobTemplate(jt)
        # Store name against job id
        if job_id is not None:
            self.__names[job_id] = name
        logging.debug("Names: %s" % self.__names)
        # Return the job id
        return job_id

    def terminate(self,job_id):
        """Remove a job from the GE queue
        """
        logging.debug("DRMAA: deleting job")
        self.__session.control(job_id,drmaa.JobControlAction.TERMINATE)
        return True

    def logFile(self,job_id):
        """Return the log file name for a job

        The name should be '<name>.o<job_id>'
        """
        return "%s.o%s" % (self.__names[job_id],job_id)

    def errFile(self,job_id):
        """Return the error file name for a job

        The name should be '<name>.e<job_id>'
        """
        return "%s.e%s" % (self.__names[job_id],job_id)

    def errorState(self,job_id):
        """Check if the job is in an error state

        Return True if the job is deemed to be in an 'error state',
        False otherwise.
        """
        # Not implemented
        return False

    def queue(self,job_id):
        """Fetch the job queue name

        Returns the queue as reported by qstat, or None if
        not found.
        """
        # Not implemented
        return None

    def list(self):
        """Get list of job ids in the queue.
        """
        job_ids = []
        for job in self.__names:
            if self.__session.jobStatus(job) == drmaa.JobState.RUNNING or \
                    self.__session.jobStatus(job) == drmaa.JobState.SYSTEM_SUSPENDED:
                job_ids.append(job)
        return job_ids

#######################################################################
# Functions
#######################################################################

def fetch_runner(definition):
    """Return job runner instance based on a definition string

    Given a definition string, returns an appropriate runner
    instance.

    Definitions are of the form:

      RunnerName[(args)]

    RunnerName can be 'SimpleJobRunner' or 'GEJobRunner'.
    If '(args)' are also supplied then these are passed to
    the job runner on instantiation (only works for
    GE runners).

    """
    if definition.startswith('SimpleJobRunner'):
        return SimpleJobRunner(join_logs=True)
    elif definition.startswith('GEJobRunner'):
        if definition.startswith('GEJobRunner(') and definition.endswith(')'):
            ge_extra_args = definition[len('GEJobRunner('):len(definition)-1].split(' ')
            return GEJobRunner(ge_extra_args=ge_extra_args)
        else:
            return GEJobRunner()
    raise Exception("Unrecognised runner definition: %s" % definition)
