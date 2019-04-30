#!/usr/bin/env python
#
#     cluster_load.py: wrap qstat for reporting current Grid Engine usage
#     Copyright (C) University of Manchester 2013-2019 Peter Briggs
#
########################################################################
#
# cluster_load.py
#
#########################################################################

"""cluster_load.py

Wrap qstat and generate high-level report on current Grid Engine usage,
of the form:

--
6 jobs running (r)
44 jobs queued (q)
0 jobs suspended (S)
0 jobs pending deletion (d)

Jobs by queue:
    queue1.q    1 (0/0)
    queue2.q    5 (0/0)

Jobs by user:
             	Total   r	q	S	d
        user1   2	1	1	0	0
        user2   15      1	14      0	0
        user3   32	4	28	0	0
        user4   1	0	1	0	0

Jobs by node:
             	Total   queue1.q        queue2.q
                         r (S/d)         r (S/d)
      node01    1        0 (0/0)         1 (0/0)
      node02    1        0 (0/0)         1 (0/0)
      node03    1        1 (0/0)         0 (0/0)
      node04    1        0 (0/0)         1 (0/0)
      node05    1        0 (0/0)         1 (0/0)
      node06    1        0 (0/0)         1 (0/0)
                         1 (0/0)         5 (0/0)
--

"""

#######################################################################
# Import modules that this module depends on
#######################################################################

import os
import subprocess
import logging

#######################################################################
# Classes
#######################################################################

class Qstat(object):
    """Class for acquiring and filtering qstat data

    'qstat' is a command line utility that reports per-job Grid Engine
    usage. The Qstat class provides an interface for handling this
    information programmatically.

    To get current usage for all jobs:

    >>> q = Qstat()
    
    To get information about the nodes and queues that are currently in
    use, and the on the system respectively:

    >>> nodes = q.nodes
    >>> queues = q.queues
    >>> user = q.users

    The 'jobs' attribute holds a list of jobs in the system, with each
    job represented by a QstatJob object. To get all jobs:

    >>> jobs = q.jobs

    To get a subset of jobs use the 'filter' option, e.g. to only get
    jobs where the status is running ('r'):

    >>> running_jobs = q.filter('queue','r').jobs
    
    """

    def __init__(self,user=None,jobs=None):
        if jobs is None:
            self.jobs = qstat(user=user)
        else:
            self.jobs = jobs

    @property
    def queues(self):
        """Return list of queue names

        """
        queues = []
        for j in self.jobs:
            if j.queue != '':
                q = j.queue_name
                if q not in queues:
                    queues.append(q)
        queues.sort()
        return queues

    @property
    def nodes(self):
        """Return list of nodes

        """
        nodes = []
        for j in self.jobs:
            if j.queue != '':
                n = j.queue_host
                if n not in nodes:
                    nodes.append(n)
        nodes.sort()
        return nodes

    @property
    def users(self):
        """Return list of users

        """
        users = []
        for j in self.jobs:
            u = j.user
            if u not in users:
                users.append(u)
        users.sort()
        return users

    def filter(self,attr,value):
        """Return subset of jobs based on filter criterion

        filter returns a new Qstat object which only contains the
        jobs that match the filter criterion, i.e. where the specified
        job attribute matches the specified value.

        'attr' can be any job attribute (id, user, node, queue, queue_host,
        queue_name, state).

        'value' can be string (for exact match) or include wildcard
        characters ('*') to match the start and/or end of a value.

        """
        try:
            if value.startswith('*') and value.endswith('*'):
                subset = [j for j in self.jobs if value.strip('*') in j.__dict__[attr]]
            elif value.startswith('*'):
                subset = [j for j in self.jobs if j.__dict__[attr].endswith(value.lstrip('*'))]
            elif value.endswith('*'):
                subset = [j for j in self.jobs if j.__dict__[attr].startswith(value.rstrip('*'))]
            else:
                subset = [j for j in self.jobs if j.__dict__[attr] == value]
        except KeyError:
            subset = []
        return Qstat(jobs=subset)

    def __len__(self):
        # Implement len built-in
        return len(self.jobs)
    
class QstatJob(object):
    """Class representing a job reported by Qstat.

    QstatJob has the following properties:

    id: the id number of the job
    name: the name of the job
    user: the name of the user running the job
    state: the state code for the job (e.g. 'r', 'S' etc)
    queue: the full name of the queue

    The full queue name can contain both the host and the
    queue name, these can be accessed individually using
    two additional properties:

    queue_host: host for the queue
    queue_name: name of the queue

    """
    def __init__(self,jobid,name,user,state,queue):
        self.id = jobid
        self.name = name
        self.user = user
        self.state = state
        self.queue = queue
        try:
            self.queue_name = self.queue.split('@')[0]
        except IndexError:
            self.queue_name = ''
        try:
            self.queue_host = self.queue.split('@')[1].split('.')[0]
        except IndexError:
            self.queue_host = ''

    def __repr__(self):
        # Implement repr built-in
        fields = [self.id,self.name,self.user,self.state,
                  self.queue_name,self.queue_host]
        return '\t'.join(fields)

#######################################################################
# Functions
#######################################################################

def qstat(user=None):
        """Run qstat and return data as a list of lists

        Runs 'qstat' command, processes the output and returns a
        list where each item is the data for a job in the form of
        another list, with the items in this list being the data
        returned by qstat.
        """
        if user is None:
            user = os.getlogin()
        cmd = ['qstat','-u',user]
        # Run the qstat
        try:
            p = subprocess.Popen(cmd,stdout=subprocess.PIPE)
        except Exception,ex:
            logging.error("Exception when running qstat: %s" % ex)
            return []
        # Use communicate rather than wait as we don't know how
        # much output we'll get, and wait can deadlock if output
        # buffer exceeds 4K
        stdout,stderr = p.communicate()
        # Process the output
        jobs = []
        # Typical output is:
        # job-ID  prior   name       user         ...<snipped>...
        # ----------------------------------------...<snipped>...
        # 620848 -499.50000 qc       myname       ...<snipped>...
        # ...
        # i.e. 2 header lines then one line per job
        for line in stdout.split('\n'):
            #print line
            try:
                if line.split()[0].isdigit():
                    jobid = line.split()[0]
                    name = line.split()[2]
                    user = line.split()[3]
                    state = line.split()[4]
                    if len(line.split()) > 8:
                        queue = line.split()[7]
                    else:
                        queue = ''
                    jobs.append(QstatJob(jobid,name,user,state,queue))
            except IndexError:
                # Skip this line
                pass
        return jobs

#######################################################################
# Main program
#######################################################################

if __name__ == "__main__":
    # Get list of all jobs
    qstatus = Qstat('*')
    # Summarise
    print "%d jobs running (r)" % len(qstatus.filter('state','r*'))
    print "%d jobs queued (q)" % len(qstatus.filter('state','*q*'))
    print "%d jobs suspended (S)" % len(qstatus.filter('state','S*'))
    print "%d jobs pending deletion (d)" % len(qstatus.filter('state','d*'))
    print ""
    # Total number assigned to each queue across all instances
    print "Jobs by queue:"
    for q in qstatus.queues:
        qstatus_queue = qstatus.filter('queue_name',q)
        print "%12s\t%d (%d/%d)" % (q,
                                 len(qstatus_queue.filter('state','r*')),
                                 len(qstatus_queue.filter('state','S*')),
                                 len(qstatus_queue.filter('state','d*')))

    print ""
    # Jobs for each user (total, running, queued and suspended)
    print "Jobs by user:"
    print "%12s\tTotal\tr\tq\tS\td" % ''
    for u in qstatus.users:
        qstatus_user = qstatus.filter('user',u)
        n_total = len(qstatus_user)
        n_r = len(qstatus_user.filter('state','r'))
        n_q = len(qstatus_user.filter('state','*q*'))
        n_S = len(qstatus_user.filter('state','S'))
        n_d = len(qstatus_user.filter('state','d*'))
        print "%12s\t%d\t%d\t%d\t%s\t%s" % (u,n_total,n_r,n_q,n_S,n_d)
    print ""
    # Jobs for each node by queue instance
    print "Jobs by node:"
    out_line = ["%12s" % '',"Total"]
    for queue in qstatus.queues:
        out_line.append("%8s" % queue)
    print str('\t'.join(out_line))
    out_line = [" "*12 , " "*len("Total")]
    for queue in qstatus.queues:
        out_line.append("%8s" % 'r (S/d)')
    print str('\t'.join(out_line))
    for n in qstatus.nodes:
        # Breakdown into queues on this node
        out_line = ["%12s" % n, "%d" % len(qstatus.filter('queue_host',n))]
        for q in qstatus.queues:
            qstatus_queue = qstatus.filter('queue_host',n).filter('queue_name',q)
            n_q = len(qstatus_queue)
            n_r = len(qstatus_queue.filter('state','r*'))
            n_S = len(qstatus_queue.filter('state','S*'))
            n_d = len(qstatus_queue.filter('state','d*'))
            out_line.append("%8s" % ("%d (%d/%d)" % (n_r,n_S,n_d)))
        print str('\t'.join(out_line))
    out_line = ["%12s" % '',""]
    for q in qstatus.queues:
        qstatus_queue = qstatus.filter('queue_name',q)
        out_line.append("%8s" % ("%d (%d/%d)" % 
                                 (len(qstatus_queue.filter('state','r*')),
                                  len(qstatus_queue.filter('state','S*')),
                                  len(qstatus_queue.filter('state','d*')))))
    print str('\t'.join(out_line))
