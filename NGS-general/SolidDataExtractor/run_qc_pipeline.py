import sys
import os
import time
import subprocess

def RunScript(script,csfasta,qual):
    # Runs a command
    cwd=os.path.dirname(csfasta)
    p = subprocess.Popen((script,csfasta,qual),cwd=cwd)
    print "Running..."
    p.wait()
    print "Finished"

def QsubScript(name,script,*args):
    # Submits a command to the cluster
    cmd = [script]
    cmd.extend(args)
    ##cmd=' '.join((script,csfasta,qual))
    cmd = ' '.join(cmd)
    qsub=('qsub','-b','y','-cwd','-V','-N',name,cmd)
    cwd=os.path.dirname(csfasta)
    p = subprocess.Popen(qsub,cwd=cwd)
    print "Running..."
    p.wait()
    print "Finished"

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
    # Process the output
    ##print ">> Output from qstat:"
    nlines = 0
    for line in p.stdout:
        ##print str(line).strip()
        nlines += 1
    ##print ">> Output ends"
    ##print "Number of lines = %d" % i
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

    # Gather data files from data_dir
    all_files = os.listdir(data_dir)
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
                    run_data.append((csfasta,filen))
            except IndexError:
                print "Unable to process qual file %" % filen
            
    # For each pair of files, run the qc
    ##count = 0
    for data in run_data:
        # Check if queue is "full"
        while Qstat() >= 4:
            # Wait for 30 seconds
            print "Waiting for queue"
            time.sleep(30)
        # Submit
        print "Submitting job: '%s %s %s'" % (script,data[0],data[1])
        QsubScript('qc',script,data[0],data[1])
        ##count += 1
        # Don't submit everything
        ##if count == 4:
        ##    sys.exit()
        
    
