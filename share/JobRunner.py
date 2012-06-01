#!/bin/env python
#
#     JobRunner.py: classes for starting and managing job runs
#     Copyright (C) University of Manchester 2011 Peter Briggs
#
########################################################################
#
# JobRunner.py
#
#########################################################################

"""JobRunner

Classes for starting, stopping and managing jobs.

Class BaseJobRunner is a template with methods that need to be implemented
by subclasses. The subclasses implemented here are:

   SimpleJobRunner: run jobs (e.g. scripts) on a local file system.
   GEJobRunner    : run jobs using Grid Engine (GE) i.e. qsub, qdel etc
   DRMAAJobRunner : run jobs using the DRMAA interface to Grid Engine

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

class BaseJobRunner:
    """Base class for implementing job runners

    This class can be used as a template for implementing custom
    job runners. The idea is that the runners wrap the specifics
    of interacting with an underlying job control system and thus
    provide a generic interface to be used by higher level classes.

    A job runner needs to implement the following methods:

      run      : starts a job running
      terminate: kills a running job
      list     : lists the running job ids
      logFile  : returns the name of the log file for a job
      errFile  : returns the name of the error file for a job

    Optionally it can also implement the methods:

      errorState: indicates if running job is in an "error state"
      isRunning : checks if a specific job is running

    if the default implementations are not sufficient.
    """

    def __init__(self):
        pass

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
        raise NotImplementedError, "Subclass must implement 'run'"

    def terminate(self,job_id):
        """Terminate a job

        Returns True if termination was successful, False
        otherwise
        """
        raise NotImplementedError, "Subclass must implement 'terminate'"

    def list(self):
        """Return a list of running job_ids
        """
        raise NotImplementedError, "Subclass must implement 'list'"

    def logFile(self,job_id):
        """Return name of log file relative to working directory
        """
        raise NotImplementedError, "Subclass must implement 'logFile'"

    def errFile(self,job_id):
        """Return name of error file relative to working directory
        """
        raise NotImplementedError, "Subclass must implement 'errFile'"

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

class SimpleJobRunner(BaseJobRunner):
    """Class implementing job runner for local system

    SimpleJobRunner starts jobs as processes on a local system;
    the status of jobs is determined using the Linux 'ps eu'
    command, and jobs are terminated using 'kill -9'.
    """

    def __init__(self):
        """Create a new SimpleJobRunner instance
        """
        # Store a list of job ids (= pids) managed by this class
        self.__job_list = []
        # Base log id
        self.__log_id = int(time.time())
        # Keep track of log files etc
        self.__log_files = {}
        self.__err_files = {}

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
        logging.debug("Script     : %s" % script)
        logging.debug("Arguments  : %s" % str(args))
        # Build command to be submitted
        cmd = [script]
        cmd.extend(args)
        # Build qsub command to submit it
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
        lognames = self.__assign_log_files(name)
        log = open(lognames[0],'w')
        err = open(lognames[1],'w')
        # Start the subprocess
        p = subprocess.Popen(cmd,cwd=cwd,stdout=log,stderr=err)
        # Capture the job id from the output
        job_id = str(p.pid)
        logging.debug("RunScript: done - job id = %s" % job_id)
        # Do internal house keeping
        self.__job_list.append(job_id)
        self.__log_files[job_id] = lognames[0]
        self.__err_files[job_id] = lognames[1]
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
        kill=('kill','-9',job_id)
        p = subprocess.Popen(kill)
        p.wait()
        if not Pstat().hasJob(job_id):
            logging.debug("KillJob: deleted job %s" % job_id)
            return True
        else:
            logging.error("Failed to delete job %s" % job_id)
            return False

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
        jobs = self.__run_ps()
        # Process the output to get job ids
        job_ids = []
        for job_data in jobs:
            # Id is second item for each job
            job_id = job_data[1]
            if job_id in self.__job_list:
                job_ids.append(job_id)
        return job_ids

    def __run_ps(self):
        """Internal: run 'ps eu' and return output as list of lines
        """
        cmd = ['ps','eu']
        p = subprocess.Popen(cmd,stdout=subprocess.PIPE)
        # Process the output
        jobs = []
        # Typical output is:
        #USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
        #mee       2451  0.0  0.0 116424  1928 pts/0    Ss   Oct14   0:00 bash LANG=....
        # ...
        # i.e. 1 header line then one line per job/process
        for line in p.stdout:
            try:
                if line.split()[1].isdigit():
                    jobs.append(line.split())
            except IndexError:
                # Skip this line
                pass
        return jobs

    def __assign_log_files(self,name):
        """Internal: return log file names for stdout and stderr

        Since the job id isn't known before the job starts, create
        names based on the timestamp plus the supplied 'name'
        """
        timestamp = self.__log_id
        log_file = "%s.o%s" % (name,timestamp)
        error_file = "%s.e%s" % (name,timestamp)
        self.__log_id += 1
        return (log_file,error_file)

class GEJobRunner(BaseJobRunner):
    """Class implementing job runner for Grid Engine

    GEJobRunner submits jobs to a Grid Engine cluster using the
    'qsub' command, determines the status of jobs using 'qstat'
    and terminates then using 'qdel'.

    Additionally the runner can be configured for a specific GE
    queue on initialisation.
    """

    def __init__(self,queue=None):
        """Create a new GEJobRunner instance

        Arguments:
          queue: Name of GE queue to use (set to 'None' to use default queue)
        """
        self.__queue = queue
        self.__names = {}

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
        logging.debug("Working_dir: %s" % working_dir)
        logging.debug("Script     : %s" % script)
        logging.debug("Arguments  : %s" % str(args))
        # Build command to be submitted
        cmd_args = [script]
        cmd_args.extend(args)
        cmd = ' '.join(cmd_args)
        # Build qsub command to submit it
        qsub = ['qsub','-b','y','-V','-N',name]
        if self.__queue:
            qsub.extend(('-q',self.__queue))
        if not working_dir:
            qsub.append('-cwd')
        else:
            qsub.extend(('-wd',working_dir))
        qsub.append(cmd)
        logging.debug("QsubScript: qsub command: %s" % qsub)
        # Run the qsub job in the current directory
        cwd = os.getcwd()
        # Check that this exists
        logging.debug("QsubScript: executing in %s" % cwd)
        if not os.path.exists(cwd):
            logging.error("QsubScript: cwd doesn't exist!")
            return None
        p = subprocess.Popen(qsub,cwd=cwd,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        p.wait()
        # Check stderr
        error = p.stderr.read().strip()
        if error:
            # Just echo error message as a warning
            logging.warning("QsubScript: '%s'" % error)
        # Capture the job id from the output
        job_id = None
        for line in p.stdout:
            if line.startswith('Your job'):
                job_id = line.split()[2]
        logging.debug("QsubScript: done - job id = %s" % job_id)
        # Store name against job id
        if job_id is not None:
            self.__names[job_id] = name
        # Return the job id
        return job_id

    def terminate(self,job_id):
        """Remove a job from the GE queue using 'qdel'
        """
        logging.debug("QdelJob: deleting job")
        qdel=('qdel',job_id)
        p = subprocess.Popen(qdel,stdout=subprocess.PIPE)
        p.wait()
        message = p.stdout.read()
        logging.debug("qdel: %s" % message)
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
        jobs = self.__run_qstat()
        # Process the output to get job ids
        job_ids = []
        for job_data in jobs:
            # Check for state being 'r' (=running)
            if job_data[4] == 'r':
                # Id is first item for each job
                job_ids.append(job_data[0])
        return job_ids

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
        # Run the qstat
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
            if self.__session.jobStatus(job) == drmaa.JobState.RUNNING:
                job_ids.append(job)
        return job_ids

#######################################################################
# Main program
#######################################################################

if __name__ == "__main__":
    # Example of usage
    import sys
    logging.getLogger().setLevel(logging.DEBUG)
    if len(sys.argv) < 2:
        print "Supply script and arguments to run"
        sys.exit()
    args = sys.argv[1:]
    runner = SimpleJobRunner()
    ##runner = GEJobRunner()
    ##runner = DRMAAJobRunner()
    pid = runner.run(os.path.basename(sys.argv[1]),None,args)
    print "Submitted job: %s" % pid
    print "Outputs: %s %s" % (runner.logFile(pid),runner.errFile(pid))
    print "%s" % runner.list()
    while runner.isRunning(pid):
        time.sleep(10)
    print "Finished"
