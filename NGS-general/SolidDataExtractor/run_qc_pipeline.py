import sys
import os
import time
import subprocess
import logging

def RunScript(script,csfasta,qual):
    # Runs a command
    cwd=os.path.dirname(csfasta)
    p = subprocess.Popen((script,csfasta,qual),cwd=cwd)
    print "Running..."
    p.wait()
    print "Finished"

def QsubScript(name,script,*args):
    # Submits a command to the cluster
    logging.info("Submitting job...")
    cmd_args = [script]
    cmd_args.extend(args)
    cmd = ' '.join(cmd_args)
    qsub=('qsub','-b','y','-cwd','-V','-N',name,cmd)
    cwd=os.path.dirname(csfasta)
    p = subprocess.Popen(qsub,cwd=cwd,stdout=subprocess.PIPE)
    p.wait()
    # Capture the job id from the output
    job_id = None
    for line in p.stdout:
        if line.startswith('Your job'):
            job_id = line.split()[2]
    logging.info("Done - job id = %s" % job_id)
    # Return the job id
    return job_id

def Qstat(user=None):
    # Get the results of qstat (assume current user if None)
    # Return number of queued jobs that user currently has
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
    
if __name__ == "__main__":
    # Deal with command line
    if len(sys.argv) != 3:
        print "Usage: %s <script> <dir>" % sys.argv[0]
        sys.exit()
    else:
        script = sys.argv[1]
        data_dir = sys.argv[2]
    print "Running %s on data from %s" % (script,data_dir)

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
                csfasta = os.path.join(data_dir,
                                       root[:i]+root[i+3:]+".csfasta")
                qual = os.path.join(data_dir,filen)
                if os.path.exists(csfasta):
                    run_data.append((csfasta,qual))
            except IndexError:
                logging.critical("Unable to process qual file %s" % filen)
            
    # For each pair of files, run the qc
    for data in run_data:
        # Check if queue is "full"
        while Qstat() >= 4:
            # Wait for 30 seconds
            logging.debug("Waiting for free space in queue...")
            time.sleep(30)
        # Submit
        logging.info("Submitting job: '%s %s %s'" % (script,data[0],data[1]))
        QsubScript('qc',script,data[0],data[1])
        
    
