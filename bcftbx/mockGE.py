#     mockGE.py: mock Grid Engine functionality for testing
#     Copyright (C) University of Manchester 2018-2020 Peter Briggs
#
#######################################################################

"""
Utility class for simulating Grid Engine (GE) functionality

Provides a single class `MockGE`, which implements methods for
simulating the functionality provided by the Grid Engine command
line utilities, and a function `setup_mock_GE`, which creates
mock versions of those utilities ('qsub', 'qstat', 'qacct' and
'qdel').
"""

#######################################################################
# Imports
#######################################################################

from builtins import str
import os
import io
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

class MockGE(object):
    """
    Class implementing qsub, qstat, qacct & qdel-like functionality

    Job data is stored in an SQLite3 database in the 'database
    directory' (defaults to '$HOME/.mockGE'); scripts and job
    exit status files are also written to this directory.

    The following methods can be invoked which provide functions
    similar to their SGE namesakes:

    - qsub: submits a job to be run
    - qstat: outputs information on active jobs
    - qacct: outputs accounting information for completed jobs
    - qdel: terminates an active job

    Each time any of these are invoked, the 'update_jobs' method is
    called to check the status of any active jobs and update the
    database accordingly; this method can also be invoked directly.

    NB the 'stop' method should be invoked on the 'MockGE' instance
    when it is not longer needed, to ensure that any running
    processes are properly terminated.
    """
    def __init__(self,max_jobs=4,qsub_delay=0.0,qacct_delay=15.0,
                 shell='/bin/bash',database_dir=None,debug=False):
        """
        Create a new MockGE instance

        Arguments:
          max_jobs (int): maximum number of jobs to run at
            once; additional jobs will be queued
          qsub_delay (float): minimum time in seconds that must
            elapse from 'qsub' command to job registering and
            appearing in 'qstat' output
          qacct_delay (float): number of seconds that must elapse
            from job finishing to providing 'qacct' info
          shell (str): shell to run internal scripts using
          database_dir (str): path to directory used for
            managing the mockGE functionality (defaults to
            '$HOME/.mockGE')
          debug (bool): if True then turn on debugging output
        """
        if debug:
            logging.getLogger().setLevel(logging.DEBUG)
        if database_dir is None:
            database_dir = os.path.join(self._user_home(),
                                        ".mockGE")
        self._database_dir = os.path.abspath(database_dir)
        self._db_file = os.path.join(self._database_dir,
                                     "mockGE.sqlite")
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
        self._qsub_delay = qsub_delay
        self._qacct_delay = qacct_delay
        atexit.register(self.stop)

    def stop(self):
        """
        Terminate running jobs when MockGE class no longer needed
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
          output_name VARCHAR,
          nslots      INTEGER,
          queue       VARCHAR,
          join_output CHAR,
          pid         INTEGER,
          qsub_time   FLOAT,
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

    def _init_job(self,name,command,working_dir,nslots,queue,
                  output_name,join_output):
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
        logging.debug("_init_job: cmd: %s" % cmd)
        try:
            sql = """
            INSERT INTO jobs (user,state,qsub_time,name,command,working_dir,nslots,queue,output_name,join_output)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            cu = self._cx.cursor()
            cu.execute(sql,(self._user(),
                            't',
                            time.time(),
                            name,
                            command,
                            working_dir,
                            nslots,
                            queue,
                            output_name,
                            join_output))
            self._cx.commit()
            return cu.lastrowid
        except Exception as ex:
            logging.error("qsub failed with exception: %s" % ex)

    def _start_job(self,job_id):
        """
        Start a job running
        """
        # Get job info
        sql = """
        SELECT name,command,nslots,queue,working_dir,output_name,join_output
        FROM jobs WHERE id==?
        """
        cu = self._cx.cursor()
        cu.execute(sql,(job_id,))
        job = cu.fetchone()
        name = job['name']
        command = job['command']
        nslots = job['nslots']
        queue = job['queue']
        working_dir = job['working_dir']
        output_name = job['output_name']
        join_output = job['join_output']
        # Try to run the job
        try:
            # Output file basename
            if output_name:
                out = os.path.abspath(output_name)
                if os.path.isdir(out):
                    out = os.path.join(out,name)
                elif not os.path.isabs(out):
                    out = os.path.join(working_dir,out)
            else:
                out = os.path.join(working_dir,name)
            logging.debug("Output basename: %s" % out)
            # Set up stdout and stderr targets
            stdout_file = "%s.o%s" % (out,job_id)
            redirect = "1>%s" % stdout_file
            logging.debug("Stdout: %s" % stdout_file)
            if join_output == 'y':
                redirect = "%s 2>&1" % redirect
            else:
                stderr_file = "%s.e%s" % (out,job_id)
                redirect = "%s 2>%s" % (redirect,stderr_file)
                logging.debug("Stderr: %s" % stderr_file)
            # Build a script to run the command
            script_file = os.path.join(self._database_dir,
                                       "__job%d.sh" % job_id)
            with io.open(script_file,'wt') as fp:
                fp.write(u"""#!%s
NSLOTS=%s QUEUE=%s %s %s
exit_code=$?
echo "$exit_code" 1>%s/__exit_code.%d
""" % (self._shell,nslots,queue,command,redirect,self._database_dir,job_id))
            os.chmod(script_file,0o775)
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
            UPDATE jobs SET pid=?,state='r',start_time=?
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
            UPDATE jobs SET state='Eqw',start_time=?
            WHERE id=?
            """
            cu = self._cx.cursor()
            cu.execute(sql,(time.time(),job_id))
            self._cx.commit()

    def update_jobs(self):
        """
        Update all job info
        """
        # Get jobs that are waiting with state 't' and
        # set them to 'qw'
        cu = self._cx.cursor()
        sql = """
        SELECT id,qsub_time FROM jobs WHERE state=='t'
        """
        cu.execute(sql)
        jobs = cu.fetchall()
        for job in jobs:
            if (time.time() - job['qsub_time']) < self._qsub_delay:
                logging.debug("Job %d not ready to go to 'qw'",
                              job['id'])
                continue
            logging.debug("Setting state to 'qw' for job %d" %
                          job['id'])
            sql = """
            UPDATE jobs SET state='qw' WHERE id=?
            """
            cu.execute(sql,(job['id'],))
            self._cx.commit()
        # Get jobs that have finished running
        sql = """
        SELECT id,pid FROM jobs WHERE state=='r'
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
                os.kill(pid,0)
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
                with io.open(exit_code_file,'rt') as fp:
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
            logging.debug("SQL: %s" % sql)
            cu.execute(sql,(exit_code,end_time,job_id))
        if finished_jobs:
            self._cx.commit()
        # Deal with jobs that are marked for deletion
        sql = """
        SELECT id FROM jobs WHERE state == 'd'
        """
        cu.execute(sql)
        jobs = cu.fetchall()
        deleted_jobs = [job['id'] for job in jobs]
        for job_id in deleted_jobs:
            sql = """
            SELECT pid FROM jobs WHERE id==?
            """
            cu.execute(sql,(job_id,))
            job = cu.fetchone()
            if job is None:
                continue
            # Try to stop the job
            try:
                pid = int(job['pid'])
                os.kill(pid,9)
            except Exception:
                pass
            # Update the database
            sql = """
            UPDATE jobs SET state='c' WHERE id=?
            """
            cu.execute(sql,(job_id,))
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
        SELECT id FROM jobs WHERE state == 'qw'
        """
        cu.execute(sql)
        jobs = cu.fetchall()
        waiting_jobs = [job['id'] for job in jobs]
        for job_id in waiting_jobs:
            sql = """
            SELECT id,pid FROM jobs WHERE state=='r'
            """
            cu.execute(sql)
            nrunning = len(cu.fetchall())
            if nrunning < self._max_jobs:
                self._start_job(job_id)
            else:
                break
        
    def _list_jobs(self,user,state=None):
        """
        Get list of the jobs
        """
        sql = """
        SELECT id,name,user,state,qsub_time,start_time,queue FROM jobs WHERE state != 'c'
        """
        args = []
        if user != "\\*" and user != "*":
            sql += "AND user == ?"
            args.append(user)
        cu = self._cx.cursor()
        cu.execute(sql,args)
        return cu.fetchall()

    def _job_info(self,job_id):
        """
        Return info on a job
        """
        sql = """
        SELECT id,name,user,exit_code,qsub_time,start_time,end_time,queue
        FROM jobs WHERE id==? AND state=='c'
        """
        cu = self._cx.cursor()
        cu.execute(sql,(job_id,))
        return cu.fetchone()

    def _mark_for_deletion(self,job_id):
        """
        Mark a job for termination/deletion
        """
        # Look up the job and check it can be deleted
        sql = """
        SELECT state FROM jobs WHERE id=?
        """
        cu = self._cx.cursor()
        cu.execute(sql,(job_id,))
        job = cu.fetchone()
        if job is None:
            return
        state = job['state']
        if state not in ('t','qw','r','Eqw'):
            return
        new_state = 'd'
        sql = """
        UPDATE jobs SET state=? WHERE id=?
        """
        cu = self._cx.cursor()
        cu.execute(sql,(new_state,job_id,))
        self._cx.commit()

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

    def qsub(self,argv):
        """
        Implement qsub-like functionality
        """
        # Process supplied arguments
        p = argparse.ArgumentParser()
        p.add_argument("-b",action="store")
        p.add_argument("-V",action="store_true")
        p.add_argument("-N",action="store")
        p.add_argument("-cwd",action="store_true")
        p.add_argument("-wd",action="store")
        p.add_argument("-pe",action="store",nargs=2)
        p.add_argument("-j",action="store")
        p.add_argument("-o",action="store")
        p.add_argument("-e",action="store")
        args,cmd = p.parse_known_args(argv)
        # Command
        logging.debug("qsub: cmd: %s" % cmd)
        if len(cmd) == 1:
            cmd = cmd[0].split(' ')
        # Job name
        if args.N is not None:
            name = str(args.N)
        else:
            name = cmd[0].split(' ')[0]
        logging.debug("Name: %s" % name)
        # Working directory
        if args.wd:
            working_dir = os.path.abspath(args.wd)
        else:
            working_dir = os.getcwd()
        logging.debug("Working dir: %s" % working_dir)
        # Parallel environment
        if args.pe:
            nslots = args.pe[1]
        else:
            nslots = 1
        # Queue
        queue = "mock.q"
        # Output options
        if args.o:
            output_name = args.o
        else:
            output_name = ''
        if args.j == 'y':
            join_output = 'y'
        else:
            join_output = 'n'
        # Create an initial entry in job table
        job_id = self._init_job(name,cmd,working_dir,nslots,queue,
                                output_name,join_output)
        logging.debug("Created job %s" % job_id)
        # Report the job id
        print("Your job %s (\"%s\") has been submitted" % (job_id,
                                                           name))
        self.update_jobs()

    def qstat(self,argv):
        """
        Implement qstat-like functionality
        """
        # Example qstat output
        # job-ID  prior   name       user         state submit/start at     queue                          slots ja-task-ID 
        #-----------------------------------------------------------------------------------------------------------------
        # 1119861 0.39868 myawesomej user1        r     07/09/2018 16:53:03 serial.q@node001               48
        # ...
        #
        # Update the db
        self.update_jobs()
        # Process supplied arguments
        p = argparse.ArgumentParser()
        p.add_argument("-u",action="store")
        args = p.parse_args(argv)
        # User
        user = args.u
        if user is None:
            user = self._user()
        # Get jobs
        jobs = self._list_jobs(user=user)
        if not jobs:
            return
        # Print job info
        print("""job-ID  prior   name       user         state submit/start at     queue                          slots ja-task-ID
-----------------------------------------------------------------------------------------------------------------""")
        for job in jobs:
            job_id = str(job["id"])
            name = str(job["name"])
            user = str(job["user"])
            state = str(job["state"])
            start_time = job["start_time"]
            queue = job["queue"]
            if start_time is None:
                start_time = job["qsub_time"]
            start_time = datetime.datetime.fromtimestamp(start_time).strftime("%m/%d/%Y %H:%M:%S")
            line = []
            line.append("%s%s" % (job_id[:7],' '*(7-len(job_id))))
            line.append("0.00001")
            line.append("%s%s" % (name[:10],' '*(10-len(name))))
            line.append("%s%s" % (user[:12],' '*(12-len(user))))
            line.append("%s%s" % (state[:5],' '*(5-len(state))))
            line.append("%s" % start_time)
            line.append("%s%s" % (queue[:30],' '*(30-len(queue))))
            line.append("1")
            print(' '.join(line))

    def qacct(self,argv):
        """
        Implement qacct-like functionality
        """
        # Example qacct output
        # ==============================================================
        # qname        mock.q  
        # hostname     node001
        # group        mygroup               
        # owner        user1            
        # project      NONE                
        # department   defaultdepartment   
        # jobname      echo                
        # jobnumber    1162479             
        # taskid       undefined
        # account      sge                 
        # priority     0                   
        # qsub_time    Mon Jul 16 15:56:45 2018
        # start_time   Mon Jul 16 15:56:46 2018
        # end_time     Mon Jul 16 15:56:47 2018
        # granted_pe   NONE                
        # slots        1                   
        # failed       0    
        # exit_status  0
        # ....
        #
        logging.debug("qacct: invoked")
        # Update the db
        self.update_jobs()
        # Process supplied arguments
        p = argparse.ArgumentParser()
        p.add_argument("-j",action="store")
        args = p.parse_args(argv)
        # Job id
        job_id = int(args.j)
        # Get job info
        job_info = self._job_info(job_id)
        if job_info is None:
            logging.debug("qacct: no info returned for job %s" %
                         job_id)
            sys.stderr.write("error: job id %s not found\n" % job_id)
            return
        # Check delay time
        elapsed_since_job_end = time.time() - job_info[6]
        logging.debug("qacct: elapsed time: %s" % elapsed_since_job_end)
        if elapsed_since_job_end < self._qacct_delay:
            return
        # Print info
        job_id = job_info['id']
        name = job_info['name']
        user = job_info['user']
        exit_code = job_info['exit_code']
        qsub_time = datetime.datetime.fromtimestamp(job_info['qsub_time']).strftime("%c")
        start_time = datetime.datetime.fromtimestamp(job_info['start_time']).strftime("%c")
        end_time = datetime.datetime.fromtimestamp(job_info['end_time']).strftime("%c")
        queue = job_info['queue']
        print("""==============================================================
qname        %s  
hostname     node001
group        mygroup               
owner        %s            
project      NONE                
department   defaultdepartment   
jobname      %s                
jobnumber    %s             
taskid       undefined
account      sge                 
priority     0                   
qsub_time    %s
start_time   %s
end_time     %s
granted_pe   NONE                
slots        1                   
failed       0    
exit_status  %s""" % (queue,user,name,job_id,
                      qsub_time,start_time,end_time,
                      exit_code))

    def qdel(self,argv):
        """
        Implement qdel-like functionality
        """
        logging.debug("qdel: invoked")
        # Update the db
        self.update_jobs()
        # Process supplied arguments
        p = argparse.ArgumentParser()
        p.add_argument("job_id",action="store",nargs="+")
        args = p.parse_args(argv)
        # Loop over job ids
        for job_id in args.job_id:
            job_id = int(job_id)
            # Mark the job for deletion
            self._mark_for_deletion(job_id)
            print("Job %s has been marked for deletion" % job_id)

#######################################################################
# Functions
#######################################################################

def _make_mock_GE_exe(path,f,database_dir=None,debug=None,
                      qsub_delay=None,qacct_delay=None):
    """
    Internal helper function to create utilities
    """
    args = []
    if database_dir is not None:
        args.append("database_dir='%s'" % database_dir)
    if qsub_delay is not None:
        args.append("qsub_delay=%s" % qsub_delay)
    if qacct_delay is not None:
        args.append("qacct_delay=%s" % qacct_delay)
    if debug is not None:
        args.append("debug=%s" % debug)
    with io.open(path,'w') as fp:
        fp.write(u"""#!/usr/bin/env python
import sys
from bcftbx.mockGE import MockGE
sys.exit(MockGE(%s).%s(sys.argv[1:]))
""" % (','.join(args),f))
    os.chmod(path,0o775)

def setup_mock_GE(bindir=None,database_dir=None,debug=None,
                  qsub_delay=None,qacct_delay=None):
    """
    Creates mock 'qsub', 'qstat', 'qacct' and 'qdel' exes
    """
    # Bin directory
    if bindir is None:
        bindir = os.getcwd()
    bindir = os.path.abspath(bindir)
    # Utilities
    for utility in ("qsub","qstat","qacct","qdel"):
        path = os.path.join(bindir,utility)
        _make_mock_GE_exe(path,
                          utility,
                          database_dir=database_dir,
                          qsub_delay=qsub_delay,
                          qacct_delay=qacct_delay,
                          debug=debug)
