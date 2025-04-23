#     mockslurm.py: mock Slurm functionality for testing
#     Copyright (C) University of Manchester 2025 Peter Briggs
#
#######################################################################

"""
Utility class for simulating Slurm functionality

Provides a single class `MockSlurm`, which implements methods for
simulating the functionality provided by the Slurm command
line utilities, and a function `setup_mock_slurm`, which creates
mock versions of those utilities ('sbatch', 'squeue', and 'scancel').
"""

#######################################################################
# Imports
#######################################################################

import os
import sys
import sqlite3
import argparse
import subprocess
import getpass
import time
import datetime
import logging
import atexit

#######################################################################
# Classes
#######################################################################

class MockSlurm:
    """
    Class implementing sbatch, squeue & scancel-like functionality

    Job data is stored in an SQLite3 database in the 'database
    directory' (defaults to '$HOME/.mockslurm'); scripts and job
    exit status files are also written to this directory.

    The following methods can be invoked which provide functions
    similar to their Slurm namesakes:

    - sbatch: submits a job to be run
    - squeue: outputs information on active jobs
    - scancel: terminates an active job

    Each time any of these are invoked, the 'update_jobs' method is
    called to check the status of any active jobs and update the
    database accordingly; this method can also be invoked directly.

    NB the 'stop' method should be invoked on the 'MockSlurm'
    instance when it is not longer needed, to ensure that any
    running processes are properly terminated.

    Arguments:
      max_jobs (int): maximum number of jobs to run at
        once; additional jobs will be queued
      sbatch_delay (float): minimum time in seconds that must
        elapse from 'sbatch' command to job registering and
        appearing in 'squeue' output
      shell (str): shell to run internal scripts using
        database_dir (str): path to directory used for
        managing the mockslurm functionality (defaults to
        '$HOME/.mockslurm')
      debug (bool): if True then turn on debugging output
    """
    def __init__(self, max_jobs=4, sbatch_delay=0.0, shell='/bin/bash',
                 database_dir=None, debug=False):
        """
        Create a new MockSlurm instance
        """
        if debug:
            logging.getLogger().setLevel(logging.DEBUG)
        if database_dir is None:
            database_dir = os.path.join(self._user_home(),
                                        ".mockslurm")
        self._database_dir = os.path.abspath(database_dir)
        self._db_file = os.path.join(self._database_dir,
                                     "mockslurm.sqlite")
        self._processes = []
        if not os.path.exists(self._database_dir):
            os.mkdir(self._database_dir)
        init_db = False
        if not os.path.exists(self._db_file):
            init_db = True
        try:
            logging.debug("Connecting to DB")
            self._cx = sqlite3.connect(self._db_file)
            self._cx.row_factory = sqlite3.Row
        except Exception as ex:
            print("Exception connecting to DB: %s" % ex)
            raise ex
        if init_db:
            logging.debug("Setting up DB")
            self._init_db()
        self._shell = shell
        self._max_jobs = max_jobs
        self._sbatch_delay = sbatch_delay
        atexit.register(self.stop)

    def stop(self):
        """
        Terminate running jobs when MockSlurm class no longer needed
        """
        self._cleanup_processes()

    def _init_db(self):
        """
        Set up the persistent database
        """
        sql = """
        CREATE TABLE jobs (
          id          INTEGER PRIMARY KEY,
          user        CHAR,
          state       CHAR,
          name        VARCHAR,
          command     VARCHAR,
          working_dir VARCHAR,
          nslots      INTEGER,
          partition   VARCHAR,
          output_tmpl CHAR,
          error_tmpl  CHAR,
          export      CHAR,
          pid         INTEGER,
          sbatch_time FLOAT,
          start_time  FLOAT,
          end_time    FLOAT,
          exit_code   INTEGER
        )
        """
        try:
            cu = self._cx.cursor()
            cu.execute(sql)
            self._cx.commit()
        except sqlite3.Error as ex:
            print("Failed to set up database: %s" % ex)
            raise ex

    def _init_job(self, name, command, working_dir, nslots, partition,
                  output_tmpl, error_tmpl, export):
        """
        Create a new job id
        """
        cmd = []
        for arg in command:
            try:
                arg.index(' ')
                arg = '"%s"' % arg
            except ValueError:
                pass
            cmd.append(arg)
        command = ' '.join(cmd)
        logging.debug(f"_init_job: cmd: {cmd}")
        try:
            sql = """
            INSERT INTO jobs (user,state,sbatch_time,name,command,working_dir,nslots,partition,output_tmpl,error_tmpl,export)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            cu = self._cx.cursor()
            cu.execute(sql,(self._user(),
                            'PD',
                            time.time(),
                            name,
                            command,
                            working_dir,
                            nslots,
                            partition,
                            output_tmpl,
                            error_tmpl,
                            export))
            self._cx.commit()
            return cu.lastrowid
        except Exception as ex:
            logging.error(f"sbatch failed with exception: {ex}")

    def _start_job(self, job_id):
        """
        Start a job running
        """
        # Get job info
        sql = """
        SELECT name,command,nslots,partition,working_dir,output_tmpl,error_tmpl
        FROM jobs WHERE id==?
        """
        cu = self._cx.cursor()
        cu.execute(sql,(job_id,))
        job = cu.fetchone()
        name = job['name']
        command = job['command']
        nslots = job['nslots']
        partition = job['partition']
        working_dir = job['working_dir']
        output_tmpl = job['output_tmpl']
        error_tmpl = job['error_tmpl']
        # Try to run the job
        try:
            # Output file basename
            out = os.path.join(working_dir, output_tmpl)
            logging.debug(f"Output basename: {out}")
            # Error file basename
            if error_tmpl:
                err = os.path.join(working_dir, error_tmpl)
            else:
                err = None
            # Set up stdout and stderr targets
            stdout_file = out.\
                          replace("%j", str(job_id)).\
                          replace("%x", str(name))
            logging.debug("Stdout: %s" % stdout_file)
            redirect = "1>%s" % stdout_file
            if err:
                stderr_file = err.\
                              replace("%j", str(job_id)).\
                              replace("%x", str(name))
                logging.debug("Stderr: %s" % stderr_file)
                redirect = "%s 2>%s" % (redirect, stderr_file)
            else:
                redirect = "%s 2>&1" % redirect
            # Build a script to run the command
            script_file = os.path.join(self._database_dir,
                                       f"__job{job_id}.sh")
            with open(script_file, "wt") as fp:
                fp.write(u"""#!%s
SLURM_NTASKS=%s SLURM_JOB_ID=%s SLURM_JOB_NAME=%s %s %s
exit_code=$?
echo "$exit_code" 1>%s/__exit_code.%d
""" % (self._shell, nslots, job_id, name, command, redirect,
       self._database_dir, job_id))
            os.chmod(script_file,0o775)
            with open(script_file, "rt") as fp:
                print(f"Job script from {script_file}:")
                for line in fp:
                    line = line.rstrip('\n')
                    print(f">>> {line}")
            # Run the command and capture process id
            process = subprocess.Popen(script_file,
                                       cwd=working_dir,
                                       close_fds=True,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.STDOUT,
                                       preexec_fn=os.setpgrp)
            pid = process.pid
            # Store process object
            self._processes.append(process)
            # Update the database
            sql = """
            UPDATE jobs SET pid=?,state='R',start_time=?
            WHERE id=?
            """
            cu = self._cx.cursor()
            cu.execute(sql,(pid,time.time(),job_id))
            self._cx.commit()
        except Exception as ex:
            # Put job into error state
            logging.debug("Exception trying to start job '%s'"
                          % job_id)
            logging.debug("%s" % ex)
            sql = """
            UPDATE jobs SET state='F',start_time=?
            WHERE id=?
            """
            cu = self._cx.cursor()
            cu.execute(sql,(time.time(),job_id))
            self._cx.commit()

    def update_jobs(self):
        """
        Update all job info
        """
        # Get jobs that have finished running
        cu = self._cx.cursor()
        sql = """
        SELECT id,pid FROM jobs WHERE state=='R'
        """
        cu.execute(sql)
        jobs = cu.fetchall()
        finished_jobs = []
        for job in jobs:
            job_id = job['id']
            pid = job['pid']
            try:
                # See https://stackoverflow.com/a/7647264/579925
                logging.debug("Checking job=%d pid=%d" % (job_id,pid))
                os.kill(pid, 0)
            except Exception as ex:
                logging.debug("Exception: %s" % ex)
                finished_jobs.append(job_id)
        logging.debug("Finished jobs: %s" % finished_jobs)
        for job_id in finished_jobs:
            # Clean up
            script_file = os.path.join(self._database_dir,
                                       "__job%d.sh" % job_id)
            if os.path.exists(script_file):
                os.remove(script_file)
            # Exit code
            exit_code_file = os.path.join(self._database_dir,
                                          "__exit_code.%d" % job_id)
            if os.path.exists(exit_code_file):
                end_time = os.path.getctime(exit_code_file)
                with open(exit_code_file, 'rt') as fp:
                    exit_code = int(fp.read())
                os.remove(exit_code_file)
            else:
                logging.error("Missing __exit_code file for job %s"
                              % job_id)
                end_time = time.time()
                exit_code = 1
            # Update database
            sql = """
            UPDATE jobs SET state='c',exit_code=?,end_time=?
            WHERE id==?
            """
            logging.debug(f"SQL: {sql}")
            cu.execute(sql, (exit_code, end_time, job_id))
        if finished_jobs:
            self._cx.commit()
        # Deal with jobs that are marked for deletion
        sql = """
        SELECT id FROM jobs WHERE state == 'CA'
        """
        cu.execute(sql)
        jobs = cu.fetchall()
        deleted_jobs = [job['id'] for job in jobs]
        for job_id in deleted_jobs:
            sql = """
            SELECT pid FROM jobs WHERE id==?
            """
            cu.execute(sql, (job_id,))
            job = cu.fetchone()
            if job is None:
                continue
            # Try to stop the job
            try:
                pid = int(job['pid'])
                os.kill(pid, 9)
            except Exception:
                pass
            # Update the database
            sql = """
            UPDATE jobs SET state='c' WHERE id=?
            """
            cu.execute(sql, (job_id,))
            self._cx.commit()
            # Remove any files
            for name in ("__job%d.sh" % job_id,
                         "__exit_code.%d" % job_id):
                try:
                    os.remove(os.path.join(self._database_dir,
                                           name))
                except OSError:
                    pass
            # Exit code
            exit_code_file = os.path.join(self._database_dir,
                                          "__exit_code.%d" % job_id)
        # Deal with jobs that are waiting
        sql = """
        SELECT id,sbatch_time FROM jobs WHERE state == 'PD'
        """
        cu.execute(sql)
        waiting_jobs = cu.fetchall()
        for job in waiting_jobs:
            # Adds a delay to jobs going from pending to running
            if (time.time() - job["sbatch_time"]) < self._sbatch_delay:
                logging.debug(f"Job {job['id']} not ready to go to 'R'")
                continue
            sql = """
            SELECT id FROM jobs WHERE state=='R'
            """
            cu.execute(sql)
            nrunning = len(cu.fetchall())
            if nrunning < self._max_jobs:
                self._start_job(job["id"])
            else:
                break

    def _list_jobs(self, user, state=None):
        """
        Get list of the jobs
        """
        sql = """
        SELECT id,name,user,state,sbatch_time,start_time,partition FROM jobs WHERE state != 'c'
        """
        args = []
        if user != "\\*" and user != "*":
            sql += "AND user == ?"
            args.append(user)
        cu = self._cx.cursor()
        cu.execute(sql, args)
        return cu.fetchall()

    def _job_info(self, job_id):
        """
        Return info on a job
        """
        sql = """
        SELECT id,name,user,exit_code,sbatch_time,start_time,end_time,partition
        FROM jobs WHERE id==? AND state=='c'
        """
        cu = self._cx.cursor()
        cu.execute(sql,(job_id,))
        return cu.fetchone()

    def _mark_for_deletion(self, job_id):
        """
        Mark a job for termination/deletion

        Return None if successfully marked, or error message
        if there an error.
        """
        # Look up the job and check it can be deleted
        sql = """
        SELECT state FROM jobs WHERE id=?
        """
        cu = self._cx.cursor()
        cu.execute(sql, (job_id,))
        job = cu.fetchone()
        if job is None:
            return "Invalid job id specified"
        state = job['state']
        if state not in ('PD', 'R', 'F'):
            return "Job/step already completing or completed"
        new_state = 'CA'
        sql = """
        UPDATE jobs SET state=? WHERE id=?
        """
        cu = self._cx.cursor()
        cu.execute(sql,(new_state,job_id,))
        self._cx.commit()
        return None

    def _cleanup_processes(self):
        """
        Do clean up (i.e. termination) of processes on exit
        """
        logging.debug("Doing cleanup for exit")
        # Stop jobs that are still running
        cu = self._cx.cursor()
        sql = """
        SELECT id,pid FROM jobs WHERE state=='r'
        """
        cu.execute(sql)
        jobs = cu.fetchall()
        for job in jobs:
            job_id = job['id']
            pid = job['pid']
            try:
                logging.debug("Checking job=%d pid=%d" % (job_id,pid))
                os.kill(pid,9)
            except Exception as ex:
                pass
        for process in self._processes:
            process.kill()

    def _user(self):
        """
        Get the current user name
        """
        return getpass.getuser()

    def _user_home(self):
        """
        Get the current user home directory
        """
        return os.path.expanduser("~%s" % self._user())

    def sbatch(self, argv):
        """
        Implement sbatch-like functionality
        """
        # Process supplied arguments
        p = argparse.ArgumentParser()
        p.add_argument("-J", "--job-name", action="store", dest="job_name")
        p.add_argument("-p", "--partition", action="store",
                       dest="partition", default="default")
        p.add_argument("-n", "--ntasks", action="store", type=int,
                       dest="ntasks", default=1)
        p.add_argument("-o", "--output", action="store", dest="output")
        p.add_argument("-e", "--error", action="store", dest="error")
        p.add_argument("--export", action="store", default="ALL")
        p.add_argument("--chdir", action="store")
        args,cmd = p.parse_known_args(argv)
        # Command
        logging.debug(f"sbatch: cmd: {cmd}")
        if len(cmd) == 1:
            cmd = cmd[0].split(' ')
        # Job name
        if args.job_name is not None:
            name = str(args.job_name)
        else:
            name = cmd[0].split(' ')[0]
        logging.debug(f"Name: {name}")
        # Working directory
        if args.chdir:
            working_dir = os.path.abspath(args.chdir)
        else:
            working_dir = os.getcwd()
        logging.debug("Working dir: %s" % working_dir)
        # Number of cores
        nslots = args.ntasks
        # Partition
        partition = args.partition
        # Export environment
        export = args.export
        # Output and error file name templates
        if args.output:
            output_tmpl = args.output
        else:
            output_tmpl = "slurm-%j.out"
        if args.error:
            error_tmpl = args.error
        else:
            error_tmpl = None
        # Create an initial entry in job table
        job_id = self._init_job(name, cmd, working_dir, nslots, partition,
                                output_tmpl, error_tmpl, export)
        logging.debug("Created job %s" % job_id)
        # Report the job id
        print(f"Submitted batch job {job_id}")
        self.update_jobs()
        return job_id

    def squeue(self, argv):
        """
        Implement squeue-like functionality
        """
        # Example squeue output (from
        # https://docs.hpc.shef.ac.uk/en/latest/referenceinfo/scheduler/SLURM/Common-commands/squeue.html#gsc.tab=0):
        #        JOBID   PARTITION   NAME      USER  ST       TIME  NODES NODELIST(REASON)
        #        1234567 interacti   bash   foo1bar   R   17:19:40      1 bessemer-node001
        #        1234568 sheffield job.sh   foo1bar   R   17:21:40      1 bessemer-node046
        #        1234569 sheffield job.sh   foo1bar  PD   17:22:40      1 (Resources)
        #        1234570 sheffield job.sh   foo1bar  PD   16:47:06      1 (Priority)
        #        1234571       gpu job.sh   foo1bar   R 1-19:46:53      1 bessemer-node026
        #        1234572       gpu job.sh   foo1bar   R 1-19:46:54      1 bessemer-node026
        #        1234573       gpu job.sh   foo1bar   R 1-19:46:55      1 bessemer-node026
        #        1234574       gpu job.sh   foo1bar   R 1-19:46:56      1 bessemer-node026
        #        1234575       gpu job.sh   foo1bar  PD       9:04      1 (ReqNodeNotAvail, UnavailableNodes:bessemer-node026)
        #        1234576 sheffield job.sh   foo1bar  PD    2:57:24      1 (QOSMaxJobsPerUserLimit)
        #
        # Job states that are relevant here:
        #
        # CA = cancelled by user or admin
        # PD = pending
        # R = running
        # S = suspended
        # CG = completing
        # CD = completed
        #
        # Update the db
        self.update_jobs()
        # Process supplied arguments
        p = argparse.ArgumentParser()
        p.add_argument("--user",action="store")
        p.add_argument("--me",action="store_true")
        args = p.parse_args(argv)
        # User
        user = None
        if args.me:
            user = self._user()
        else:
            user = args.user
        # Get jobs
        jobs = self._list_jobs(user=user)
        # Print header even if there are no jobs to report
        print("             JOBID PARTITION     NAME     USER ST       TIME  NODES NODELIST(REASON)")
        # Print info for each job
        # From manpage, default output string is:
        # "%.18i %.9P %.8j %.8u %.2t %.10M %.6D %R"
        # where . indicates right-justified (otherwise left-justified)
        # and number is minimum field size
        #
        # The letters are:
        # - i = job id
        # - P = partition
        # - j = job name
        # - u = user
        # - t = job state (compact form)
        # - M = time used by the job (H:M:S)
        # - D = number of nodes
        # - R = reason why it's pending (pending jobs), reason for
        #        failure (failed jobs), list of nodes (all others)
        for job in jobs:
            job_id = str(job["id"])
            partition = str(job["partition"])
            name = str(job["name"])
            user = job["user"]
            state = job["state"]
            job_time = job["start_time"]
            if job_time is None:
                job_time = job["sbatch_time"]
            job_time = time.time() - job_time
            num_nodes = 1
            if state == "PD":
                nodelist = "(Resources)"
            else:
                nodelist = "mock-node01"
            line = f"{job_id:>18} {partition:>9} {name:>8} {user:>8} {state:>2} {job_time:>10.2} {num_nodes:>6} {nodelist}"
            print(line)

    def scancel(self,argv):
        """
        Implement scancel-like functionality
        """
        logging.debug("scancel: invoked")
        # Update the db
        self.update_jobs()
        # Process supplied arguments
        p = argparse.ArgumentParser()
        p.add_argument("-v", dest="verbose", action="store_true")
        p.add_argument("job_id",action="store",nargs="+")
        args = p.parse_args(argv)
        # Loop over job ids
        for job_id in args.job_id:
            job_id = int(job_id)
            # Mark the job for deletion
            status = self._mark_for_deletion(job_id)
            if args.verbose:
                print(f"scancel: Terminating job {job_id}")
                if status is not None:
                    # Echo status error message
                    print(f"scancel: error: {status}")

#######################################################################
# Functions
#######################################################################

def _make_mock_slurm_exe(path, f, database_dir=None, debug=None,
                         sbatch_delay=None):
    """
    Internal helper function to create utilities
    """
    args = []
    if database_dir is not None:
        args.append(f"database_dir='{database_dir}'")
    if sbatch_delay is not None:
        args.append(f"sbatch_delay={sbatch_delay}")
    if debug is not None:
        args.append(f"debug={debug}")
    with open(path,'w') as fp:
        fp.write(u"""#!/usr/bin/env python
import sys
from bcftbx.mockslurm import MockSlurm
sys.exit(MockSlurm(%s).%s(sys.argv[1:]))
""" % (','.join(args),f))
    os.chmod(path,0o775)

def setup_mock_slurm(bindir=None, database_dir=None, debug=None,
                     sbatch_delay=None):
    """
    Creates mock 'sbatch', 'squeue' and 'scancel' exes
    """
    # Bin directory
    if bindir is None:
        bindir = os.getcwd()
    bindir = os.path.abspath(bindir)
    # Utilities
    for utility in ("sbatch", "squeue", "scancel"):
        path = os.path.join(bindir,utility)
        _make_mock_slurm_exe(path,
                             utility,
                             database_dir=database_dir,
                             sbatch_delay=sbatch_delay,
                             debug=debug)
