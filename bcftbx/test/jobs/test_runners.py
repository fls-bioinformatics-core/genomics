#######################################################################
# Tests for jobs/runners.py module
#######################################################################

from bcftbx.jobs.runners import LocalRunner
from bcftbx.jobs.runners import GridEngineRunner
from bcftbx.jobs.runners import ResourceLock
from bcftbx.mockGE import setup_mock_GE
from bcftbx.mockGE import MockGE
import unittest
import tempfile
import time
import shutil
import os

class TestLocalRunner(unittest.TestCase):

    def setUp(self):
        # Create a temporary directory to work in
        self.working_dir = self._make_tmp_dir()
        self.log_dir = None

    def tearDown(self):
        shutil.rmtree(self.working_dir)
        if self.log_dir is not None:
            shutil.rmtree(self.log_dir)

    def _make_tmp_dir(self):
        return tempfile.mkdtemp()

    def _run_job(self, runner, *args):
        return runner.run(*args)

    def _wait_for_jobs(self, runner, *args):
        poll_interval = 0.01
        ntries = 0
        running_jobs = True
        # Check running jobs
        while ntries < 100 and running_jobs:
            running_jobs = False
            for jobid in args:
                if runner.is_running(jobid):
                    running_jobs = True
            if running_jobs:
                time.sleep(poll_interval)
                ntries += 1
        # All jobs finished
        if not running_jobs:
            return
        # Otherwise we've reached the timeout limit
        self.fail("Timed out waiting for test job")

    def test_local_runner_basic_shell_command(self):
        """
        LocalRunner: execute a basic shell command
        """
        # Create a runner and execute the echo command
        runner = LocalRunner()
        jobid = self._run_job(runner, 'test', self.working_dir, 'echo', ('this is a test',))
        self.assertEqual(runner.exit_status(jobid),None)
        self._wait_for_jobs(runner,jobid)
        # Check outputs
        self.assertEqual(runner.name(jobid),'test')
        self.assertTrue(os.path.isfile(runner.log_file(jobid)))
        self.assertTrue(os.path.isfile(runner.err_file(jobid)))
        self.assertEqual(runner.exit_status(jobid),0)
        # Check log files are in the working directory
        self.assertEqual(os.path.dirname(runner.log_file(jobid)), self.working_dir)
        self.assertEqual(os.path.dirname(runner.err_file(jobid)), self.working_dir)

    def test_local_runner_exit_status(self):
        """
        LocalRunner: check exit status of commands
        """
        # Create a runner and execute commands with known exit codes
        runner = LocalRunner()
        jobid_ok = self._run_job(runner, 'test_ok', self.working_dir,
                                 '/bin/bash', ('-c','exit 0',))
        jobid_error = self._run_job(runner, 'test_error', self.working_dir,
                                    '/bin/bash',('-c','exit 1',))
        self._wait_for_jobs(runner, jobid_ok, jobid_error)
        # Check exit codes
        self.assertEqual(runner.exit_status(jobid_ok), 0)
        self.assertEqual(runner.exit_status(jobid_error), 1)

    def test_local_runner_termination(self):
        """
        LocalRunner: test job termination
        """
        # Create a runner and execute the sleep command
        runner = LocalRunner()
        jobid = self._run_job(runner, 'test', self.working_dir, 'sleep', ('60s',))
        # Wait for job to start
        ntries = 0
        while ntries < 100:
            if runner.is_running(jobid):
                break
            ntries += 1
        self.assertTrue(runner.is_running(jobid))
        # Terminate job
        runner.terminate(jobid)
        self.assertFalse(runner.is_running(jobid))
        self.assertNotEqual(runner.exit_status(jobid), 0)

    def test_local_runner_join_logs(self):
        """
        LocalRunner: test 'join_logs' option
        """
        # Create a runner and execute the echo command
        runner = LocalRunner(join_logs=True)
        jobid = self._run_job(runner, 'test', self.working_dir, 'echo', ('this is a test',))
        self._wait_for_jobs(runner, jobid)
        # Check outputs
        self.assertEqual(runner.name(jobid),'test')
        self.assertTrue(os.path.isfile(runner.log_file(jobid)))
        self.assertEqual(runner.err_file(jobid), None)
        # Check log file is in the working directory
        self.assertEqual(os.path.dirname(runner.log_file(jobid)),
                         self.working_dir)

    def test_local_runner_set_log_dir(self):
        """
        LocalRunner: test explicitly setting log directory
        """
        # Create a temporary log directory
        self.log_dir = self._make_tmp_dir()
        # Create a runner and execute the echo command
        runner = LocalRunner()
        # Reset the log directory
        runner.set_log_dir(self.log_dir)
        jobid = self._run_job(runner, 'test', self.working_dir, 'echo', ('this is a test',))
        self._wait_for_jobs(runner, jobid)
        # Check outputs
        self.assertEqual(runner.name(jobid), 'test')
        self.assertTrue(os.path.isfile(runner.log_file(jobid)))
        self.assertTrue(os.path.isfile(runner.err_file(jobid)))
        # Check log files are in the log directory, not the working directory
        self.assertEqual(os.path.dirname(runner.log_file(jobid)), self.log_dir)
        self.assertEqual(os.path.dirname(runner.err_file(jobid)), self.log_dir)

    def test_local_runner_set_log_dir_multiple_times(self):
        """
        LocalRunner: test explicitly setting log directory multiple times
        """
        # Create a temporary log directory
        self.log_dir = self._make_tmp_dir()
        # Create a runner and execute the echo command
        runner = LocalRunner()
        # Reset the log directory
        runner.set_log_dir(self.log_dir)
        jobid1 = self._run_job(runner, 'test1', self.working_dir, 'echo', ('this is a test',))
        # Rest the log directory again and run second job
        runner.set_log_dir(self.working_dir)
        jobid2 = self._run_job(runner, 'test2', self.working_dir, 'echo',('this is a test',))
        # Rest the log directory again and run 3rd job
        runner.set_log_dir(self.log_dir)
        jobid3 = self._run_job(runner, 'test3', self.working_dir, 'echo', ('this is a test',))
        # Wait for jobs to finish
        self._wait_for_jobs(runner, jobid1, jobid2, jobid3)
        # Check outputs
        self.assertEqual(runner.name(jobid1),'test1')
        self.assertTrue(os.path.isfile(runner.log_file(jobid1)))
        self.assertTrue(os.path.isfile(runner.err_file(jobid1)))
        self.assertEqual(runner.name(jobid2), 'test2')
        self.assertTrue(os.path.isfile(runner.log_file(jobid2)))
        self.assertTrue(os.path.isfile(runner.err_file(jobid2)))
        self.assertEqual(runner.name(jobid3), 'test3')
        self.assertTrue(os.path.isfile(runner.log_file(jobid3)))
        self.assertTrue(os.path.isfile(runner.err_file(jobid3)))
        # Check log files are in the correct directories
        self.assertEqual(os.path.dirname(runner.log_file(jobid1)), self.log_dir)
        self.assertEqual(os.path.dirname(runner.err_file(jobid1)), self.log_dir)
        self.assertEqual(os.path.dirname(runner.log_file(jobid2)), self.working_dir)
        self.assertEqual(os.path.dirname(runner.err_file(jobid2)), self.working_dir)
        self.assertEqual(os.path.dirname(runner.log_file(jobid3)), self.log_dir)
        self.assertEqual(os.path.dirname(runner.err_file(jobid3)), self.log_dir)

    def test_local_runner_nslots(self):
        """
        LocalRunner: test setting 'BCFTBX_RUNNER_NSLOTS' environment variable
        """
        # Create a runner and check default nslots
        runner = LocalRunner()
        self.assertEqual(runner.nslots, 1)
        jobid = self._run_job(runner,
                              'test',
                              self.working_dir,
                              '/bin/bash',
                              ('-c','echo $BCFTBX_RUNNER_NSLOTS',))
        self._wait_for_jobs(runner,jobid)
        with open(runner.log_file(jobid), "rt") as fp:
            self.assertEqual("1\n", fp.read())
        # Create a runner with multiple nslots
        runner = LocalRunner(nslots=8)
        self.assertEqual(runner.nslots, 8)
        jobid = self._run_job(runner,
                              'test',
                              self.working_dir,
                              '/bin/bash',
                              ('-c', 'echo $BCFTBX_RUNNER_NSLOTS',))
        self._wait_for_jobs(runner, jobid)
        with open(runner.log_file(jobid), "rt") as fp:
            self.assertEqual("8\n", fp.read())

    def test_local_runner_repr(self):
        """
        LocalRunner: test '__repr__' built-in
        """
        self.assertEqual(str(LocalRunner()),
                         'LocalRunner(join_logs=False)')
        self.assertEqual(str(LocalRunner(nslots=8)),
                         'LocalRunner(nslots=8 join_logs=False)')
        self.assertEqual(str(LocalRunner(join_logs=True)),
                         'LocalRunner(join_logs=True)')
        self.assertEqual(str(LocalRunner(nslots=8, join_logs=True)),
                         'LocalRunner(nslots=8 join_logs=True)')


class TestGridEngineRunner(unittest.TestCase):

    def setUp(self):
        # Set up mockGE utilities
        self.database_dir = self._make_tmp_dir()
        self.bin_dir = self._make_tmp_dir()
        self.old_path = os.environ['PATH']
        os.environ['PATH'] = self.bin_dir + os.pathsep + self.old_path
        setup_mock_GE(bindir=self.bin_dir,
                      database_dir=self.database_dir,
                      qsub_delay=0.4,
                      qacct_delay=15.0,
                      debug=False)
        self.mock_ge = MockGE(database_dir=self.database_dir)
        # Create a temporary directory to work in
        self.working_dir = self._make_tmp_dir()
        self.log_dir = None
        # Extra arguments: edit this for local setup requirements
        self.ge_extra_args = []

    def tearDown(self):
        self.mock_ge.stop()
        os.environ['PATH'] = self.old_path
        shutil.rmtree(self.database_dir)
        shutil.rmtree(self.bin_dir)
        shutil.rmtree(self.working_dir)
        if self.log_dir is not None:
            shutil.rmtree(self.log_dir)

    def _make_tmp_dir(self):
        return tempfile.mkdtemp(dir=os.getcwd())

    def _update_jobs(self,timeout=1.0):
        poll_interval = 0.1
        ntries = 0
        while (ntries*poll_interval < timeout):
            time.sleep(poll_interval)
            ntries += 1
            self.mock_ge.update_jobs()

    def _run_job(self,runner,*args):
        try:
            return runner.run(*args)
        except OSError:
            self.fail("Unable to run GE job")

    def _wait_for_jobs(self,runner,*args):
        poll_interval = 0.1
        timeout = 10.0
        ntries = 0
        running_jobs = True
        # Check running jobs
        while (ntries*poll_interval < timeout) and running_jobs:
            self.mock_ge.update_jobs()
            running_jobs = False
            for jobid in args:
                if runner.is_running(jobid):
                    running_jobs = True
            if running_jobs:
                time.sleep(poll_interval)
                ntries += 1
        # All jobs finished
        if not running_jobs:
            return
        # Otherwise we've reached the timeout limit
        for jobid in args:
            # Terminate jobs
            if runner.is_running(jobid):
                runner.terminate(jobid)
        self.fail("Timed out waiting for test job")

    def test_grid_engine_runner_fast_command(self):
        """
        GridEngineRunner: test with fast shell command
        """
        # Create a runner and execute the echo command
        runner = GridEngineRunner(ge_extra_args=self.ge_extra_args)
        jobid = self._run_job(runner,'test',self.working_dir,'echo',('this is a quick test',))
        self.assertTrue(runner.is_running(jobid))
        self._wait_for_jobs(runner,jobid)
        # Check outputs
        self.assertEqual(runner.name(jobid),'test')
        self.assertTrue(os.path.isfile(runner.log_file(jobid)),
                        "Stdout file '%s': not a file" %
                        runner.err_file(jobid))
        self.assertTrue(os.path.isfile(runner.err_file(jobid)),
                        "Stderr file '%s': not a file" %
                        runner.err_file(jobid))
        self.assertEqual(runner.exit_status(jobid),0)
        # Check log files are in the working directory
        self.assertEqual(os.path.dirname(runner.log_file(jobid)),self.working_dir)
        self.assertEqual(os.path.dirname(runner.err_file(jobid)),self.working_dir)

    def test_grid_engine_runner_fast_command_with_initial_delay(self):
        """
        GridEngineRunner: test with fast shell command & initial delay
        """
        # Create a runner and execute the echo command
        runner = GridEngineRunner(ge_extra_args=self.ge_extra_args)
        jobid = self._run_job(runner,'test',self.working_dir,'echo',('this is a quick test',))
        # Do some updates so the job finishes before the
        # first check
        self._update_jobs()
        self.assertTrue(runner.is_running(jobid))
        self._wait_for_jobs(runner,jobid)
        # Check outputs
        self.assertEqual(runner.name(jobid),'test')
        self.assertTrue(os.path.isfile(runner.log_file(jobid)),
                        "Stdout file '%s': not a file" %
                        runner.err_file(jobid))
        self.assertTrue(os.path.isfile(runner.err_file(jobid)),
                        "Stderr file '%s': not a file" %
                        runner.err_file(jobid))
        self.assertEqual(runner.exit_status(jobid),0)
        # Check log files are in the working directory
        self.assertEqual(os.path.dirname(runner.log_file(jobid)),self.working_dir)
        self.assertEqual(os.path.dirname(runner.err_file(jobid)),self.working_dir)

    def test_grid_engine_runner_slow_command(self):
        """
        GridEngineRunner: test with a slow shell command
        """
        # Create a runner and execute the sleep command
        runner = GridEngineRunner(ge_extra_args=self.ge_extra_args)
        jobid = self._run_job(runner,'test',self.working_dir,'sleep',('5',))
        self._wait_for_jobs(runner,jobid)
        # Check outputs
        self.assertEqual(runner.name(jobid),'test')
        self.assertTrue(os.path.isfile(runner.log_file(jobid)),
                        "Stdout file '%s': not a file" %
                        runner.err_file(jobid))
        self.assertTrue(os.path.isfile(runner.err_file(jobid)),
                        "Stderr file '%s': not a file" %
                        runner.err_file(jobid))
        self.assertEqual(runner.exit_status(jobid),0)
        # Check log files are in the working directory
        self.assertEqual(os.path.dirname(runner.log_file(jobid)),self.working_dir)
        self.assertEqual(os.path.dirname(runner.err_file(jobid)),self.working_dir)

    def test_grid_engine_runner_exit_status(self):
        """
        GridEngineRunner: returns correct exit status
        """
        # Create a runner and execute commands with known exit codes
        runner = GridEngineRunner(ge_extra_args=self.ge_extra_args)
        jobid_ok = self._run_job(runner,'test_ok',self.working_dir,
                                       '/bin/bash',('-c','exit 0',))
        jobid_error = self._run_job(runner,'test_error',self.working_dir,
                                   '/bin/bash',('-c','exit 1',))
        self._wait_for_jobs(runner,jobid_ok,jobid_error)
        # Check exit codes
        self.assertEqual(runner.exit_status(jobid_ok),0)
        self.assertEqual(runner.exit_status(jobid_error),1)

    def test_grid_engine_runner_termination(self):
        """
        GridEngineRunner: test terminating a running job
        """
        # Create a runner and execute the sleep command
        runner = GridEngineRunner(ge_extra_args=self.ge_extra_args)
        jobid = self._run_job(runner,'test',self.working_dir,'sleep',('60s',))
        # Wait for job to start
        ntries = 0
        while ntries < 100:
            if runner.is_running(jobid):
                break
            ntries += 1
        self.assertTrue(runner.is_running(jobid))
        # Terminate job
        runner.terminate(jobid)
        self._update_jobs()
        self.assertFalse(runner.is_running(jobid))
        self.assertNotEqual(runner.exit_status(jobid),0)

    def test_grid_engine_runner_join_logs(self):
        """
        GridEngineRunner: test '-j y' option (i.e. join stderr and stdout)
        """
        # Create a runner and execute the echo command
        self.ge_extra_args.extend(('-j','y'))
        runner = GridEngineRunner(ge_extra_args=self.ge_extra_args)
        self.assertEqual(runner.ge_extra_args,self.ge_extra_args)
        jobid = self._run_job(runner,'test',self.working_dir,'echo',('this is a test',))
        self._wait_for_jobs(runner,jobid)
        # Check outputs
        self.assertEqual(runner.name(jobid),'test')
        self.assertTrue(os.path.isfile(runner.log_file(jobid)))
        self.assertFalse(os.path.isfile(runner.err_file(jobid)))
        # Check log files are in the working directory
        self.assertEqual(os.path.dirname(runner.log_file(jobid)),self.working_dir)

    def test_grid_engine_runner_set_log_dir(self):
        """
        GridEngineRunner: explicit set log directory
        """
        # Create a temporary log directory
        self.log_dir = self._make_tmp_dir()
        # Create a runner and execute the echo command
        runner = GridEngineRunner(ge_extra_args=self.ge_extra_args)
        # Reset the log directory
        runner.set_log_dir(self.log_dir)
        jobid = self._run_job(runner,'test',self.working_dir,'echo',('this is a test',))
        self._wait_for_jobs(runner,jobid)
        # Check outputs
        self.assertEqual(runner.name(jobid),'test')
        self.assertTrue(os.path.isfile(runner.log_file(jobid)))
        self.assertTrue(os.path.isfile(runner.err_file(jobid)))
        # Check log files are the log directory, not the working directory
        self.assertEqual(os.path.dirname(runner.log_file(jobid)),self.log_dir)
        self.assertEqual(os.path.dirname(runner.err_file(jobid)),self.log_dir)

    def test_grid_engine_runner_set_log_dir_multiple_times(self):
        """
        GridEngineRunner: explicit set log directory multiple times
        """
        # Create a temporary log directory
        self.log_dir = self._make_tmp_dir()
        # Create a runner and execute the echo command
        runner = GridEngineRunner(ge_extra_args=self.ge_extra_args)
        # Reset the log directory
        runner.set_log_dir(self.log_dir)
        jobid1 = self._run_job(runner,'test1',self.working_dir,'echo',('this is a test',))
        # Rest the log directory again and run second job
        runner.set_log_dir(self.working_dir)
        jobid2 = self._run_job(runner,'test2',self.working_dir,'echo',('this is a test',))
        # Rest the log directory again and run 3rd job
        runner.set_log_dir(self.log_dir)
        jobid3 = self._run_job(runner,'test3',self.working_dir,'echo',('this is a test',))
        self._wait_for_jobs(runner,jobid1,jobid2,jobid3)
        # Check outputs
        self.assertEqual(runner.name(jobid1),'test1')
        self.assertTrue(os.path.isfile(runner.log_file(jobid1)))
        self.assertTrue(os.path.isfile(runner.err_file(jobid1)))
        self.assertEqual(runner.name(jobid2),'test2')
        self.assertTrue(os.path.isfile(runner.log_file(jobid2)))
        self.assertTrue(os.path.isfile(runner.err_file(jobid2)))
        self.assertEqual(runner.name(jobid3),'test3')
        self.assertTrue(os.path.isfile(runner.log_file(jobid3)))
        self.assertTrue(os.path.isfile(runner.err_file(jobid3)))
        # Check log files are in the correct directories
        self.assertEqual(os.path.dirname(runner.log_file(jobid1)),self.log_dir)
        self.assertEqual(os.path.dirname(runner.err_file(jobid1)),self.log_dir)
        self.assertEqual(os.path.dirname(runner.log_file(jobid2)),self.working_dir)
        self.assertEqual(os.path.dirname(runner.err_file(jobid2)),self.working_dir)
        self.assertEqual(os.path.dirname(runner.log_file(jobid3)),self.log_dir)
        self.assertEqual(os.path.dirname(runner.err_file(jobid3)),self.log_dir)

    def test_grid_engine_runner_error_state(self):
        """
        GridEngineRunner: detect job in error state
        """
        # Create a runner and execute a command in a non-existent
        # working directory
        runner = GridEngineRunner(ge_extra_args=self.ge_extra_args)
        jobid = self._run_job(runner,'test_eqw',
                             '/non/existent/dir',
                             'echo',('this should fail',))
        # Wait for job to go into error state
        ntries = 0
        while ntries < 100:
            if runner.error_state(jobid):
                # Success - job errored
                return
            time.sleep(0.1)
            ntries += 1
        self.fail("Job failed to go into error state")

    def test_grid_engine_runner_queue(self):
        """
        GridEngineRunner: fetch the queue of running job
        """
        # Create a runner and execute the sleep command
        runner = GridEngineRunner(ge_extra_args=self.ge_extra_args)
        jobid = self._run_job(runner,'test_queue',
                             self.working_dir,
                             'sleep',('10s',))
        # Wait for job to return queue
        ntries = 0
        while ntries < 100:
            self._update_jobs()
            if runner.is_running(jobid):
                queue = runner.queue(jobid)
                if queue is not None:
                    self.assertEqual(queue,"mock.q")
                    return
            time.sleep(0.1)
            ntries += 1
        self.fail("Job failed to return queue before time out")

    def test_grid_engine_runner_queue_after_completion(self):
        """
        GridEngineRunner: fetch the queue of completed job
        """
        # Create a runner and execute the sleep command
        runner = GridEngineRunner(ge_extra_args=self.ge_extra_args)
        jobid = self._run_job(runner,'test_queue',
                             self.working_dir,
                             'sleep',('1s',))
        # Wait for job to finish
        self._wait_for_jobs(runner,jobid)
        # Check the queue
        self.assertEqual(runner.queue(jobid),"mock.q")

    def test_grid_engine_runner_nslots(self):
        """Test GridEngineRunner sets BCFTBX_RUNNER_NSLOTS (-pe smp.pe)
        """
        # Create a runner and check default nslots
        runner = GridEngineRunner()
        self.assertEqual(runner.nslots,1)
        jobid = self._run_job(runner,
                             'test',
                             self.working_dir,
                             '/bin/bash',
                             ('-c','echo $BCFTBX_RUNNER_NSLOTS',))
        self._wait_for_jobs(runner,jobid)
        with open(runner.log_file(jobid),'rt') as fp:
            self.assertEqual(u"1\n",fp.read())
        # Create a runner with multiple nslots
        runner = GridEngineRunner(ge_extra_args=['-pe','smp.pe','8'])
        self.assertEqual(runner.nslots,8)
        jobid = self._run_job(runner,
                             'test',
                             self.working_dir,
                             '/bin/bash',
                             ('-c','echo $BCFTBX_RUNNER_NSLOTS',))
        self._wait_for_jobs(runner,jobid)
        with open(runner.log_file(jobid),'rt') as fp:
            self.assertEqual(u"8\n",fp.read())

    def test_grid_engine_runner_nslots_amd_pe(self):
        """
        GridEngineRunner: sets BCFTBX_RUNNER_NSLOTS (-pe amd.pe)
        """
        # Create a runner and check default nslots
        runner = GridEngineRunner()
        self.assertEqual(runner.nslots,1)
        jobid = self._run_job(runner,
                             'test',
                             self.working_dir,
                             '/bin/bash',
                             ('-c','echo $BCFTBX_RUNNER_NSLOTS',))
        self._wait_for_jobs(runner,jobid)
        with open(runner.log_file(jobid),'rt') as fp:
            self.assertEqual(u"1\n",fp.read())
        # Create a runner with multiple nslots
        runner = GridEngineRunner(ge_extra_args=['-pe','amd.pe','8'])
        self.assertEqual(runner.nslots,8)
        jobid = self._run_job(runner,
                             'test',
                             self.working_dir,
                             '/bin/bash',
                             ('-c','echo $BCFTBX_RUNNER_NSLOTS',))
        self._wait_for_jobs(runner,jobid)
        with open(runner.log_file(jobid),'rt') as fp:
            self.assertEqual(u"8\n",fp.read())


class TestResourceLock(unittest.TestCase):
    """
    Tests for the ResourceLock class
    """
    def test_resource_lock(self):
        """
        ResourceLock: check acquiring and releasing a lock
        """
        resource_lock = ResourceLock()
        self.assertFalse(resource_lock.is_locked("test"))
        lock = resource_lock.acquire("test")
        self.assertEqual(lock.split('@')[0],"test")
        self.assertTrue(resource_lock.is_locked("test"))
        resource_lock.release(lock)
        self.assertFalse(resource_lock.is_locked("test"))

    def test_resource_lock_timeout(self):
        """
        ResourceLock: check lock acquisition timeout
        """
        resource_lock = ResourceLock()
        # Get a lock
        lock = resource_lock.acquire("test")
        self.assertTrue(resource_lock.is_locked("test"))
        # Try to acquire a second lock without releasing
        # the first, specifying a timeout
        self.assertRaises(Exception,
                          resource_lock.acquire,
                          "test",
                          timeout=1.0)