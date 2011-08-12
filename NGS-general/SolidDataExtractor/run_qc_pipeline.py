#     run_pipeline.py: run pipeline script on file sets
#     Copyright (C) University of Manchester 2011 Peter Briggs
#
########################################################################
#
# run_pipeline.py
#
#########################################################################

"""run_pipeline.py

Implements a program to run a pipeline script or command on the
set of files in a specific directory.

Usage: python run_pipeline.py <script> <data_dir>

<script> must accept two arguments (a csfasta file and a qual file)
<data_dir> must contain pairs of .csfasta and .qual files
"""

#######################################################################
# Import modules that this module depends on
#######################################################################

import sys
import os
import time
import subprocess
import logging

#######################################################################
# Class definitions
#######################################################################

# No classes defined

#######################################################################
# Module Functions
#######################################################################

# RunScript: execute a script or command
def RunScript(script,csfasta,qual):
    """Run a script or command
    """
    cwd=os.path.dirname(csfasta)
    p = subprocess.Popen((script,csfasta,qual),cwd=cwd)
    print "Running..."
    p.wait()
    print "Finished"

# QsubScript: submit a command to the cluster
def QsubScript(name,script,*args):
    """Submit a script or command to the cluster via 'qsub'
    """
    # 
    logging.debug("QsubScript: submitting job")
    cmd_args = [script]
    cmd_args.extend(args)
    cmd = ' '.join(cmd_args)
    qsub=('qsub','-b','y','-cwd','-V','-N',name,cmd)
    ##cwd=os.path.dirname(csfasta)
    cwd = os.getcwd()
    p = subprocess.Popen(qsub,cwd=cwd,stdout=subprocess.PIPE)
    p.wait()
    # Capture the job id from the output
    job_id = None
    for line in p.stdout:
        if line.startswith('Your job'):
            job_id = line.split()[2]
    logging.debug("QsubScript: done - job id = %s" % job_id)
    # Return the job id
    return job_id

# QstatJobs: get number of jobs user has already in queue
def QstatJobs(user=None):
    """Get the number of jobs a user has in the queue
    """
    # Get the results of qstat -u (assume current user if None)
    cmd = ['qstat']
    if user:
        cmd.extend(('-u',user))
    else:
        # Get current user name
        cmd.extend(('-u',os.getlogin()))
    # Run the qstat
    p = subprocess.Popen(cmd,stdout=subprocess.PIPE)
    p.wait()
    # Process the output: count lines
    nlines = 0
    for line in p.stdout:
        nlines += 1
    # Typical output is:
    # job-ID  prior   name       user         ...<snipped>...
    # ----------------------------------------...<snipped>...
    # 620848 -499.50000 qc       myname       ...<snipped>...
    # ...
    # i.e. 2 header lines then one line per job
    return nlines - 2

#######################################################################
# Main program
#######################################################################

if __name__ == "__main__":
    # Initialise
    max_concurrent_jobs = 4
    poll_interval = 30

    # Deal with command line
    if len(sys.argv) != 3:
        print "Usage: %s <script> <dir>" % sys.argv[0]
        sys.exit()
    else:
        script = sys.argv[1]
        data_dir = os.path.abspath(sys.argv[2])
    print "Running %s on data in %s" % (script,data_dir)

    # Set logging format and level
    logging.basicConfig(format='%(levelname)8s %(message)s')
    logging.getLogger().setLevel(logging.INFO)

    # Gather data files from data_dir
    all_files = os.listdir(data_dir)
    all_files.sort()
    run_data = []

    # Look for csfasta and matching qual files
    for filen in all_files:

        root = os.path.splitext(filen)[0]
        ext = os.path.splitext(filen)[1]
        
        if ext == ".qual":
            # Match csfasta names which don't have "_QV" in them
            try:
                i = root.rindex('_QV')
                ##csfasta = os.path.join(data_dir,
                ##                       root[:i]+root[i+3:]+".csfasta")
                ##qual = os.path.join(data_dir,filen)
                csfasta = root[:i]+root[i+3:]+".csfasta"
                qual = filen
                if os.path.exists(csfasta):
                    run_data.append((csfasta,qual))
            except IndexError:
                logging.critical("Unable to process qual file %s" % filen)
            
    # For each pair of files, run the pipeline script
    for data in run_data:
        # Check if queue is "full"
        while QstatJobs() >= max_concurrent_jobs:
            # Wait a while before checking again
            logging.debug("Waiting for free space in queue...")
            time.sleep(poll_interval)
        # Submit
        logging.info("Submitting job: '%s %s %s'" % (script,data[0],data[1]))
        job_id = QsubScript('qc',script,data[0],data[1])
        logging.info("Job id = %s" % job_id)
        
    
