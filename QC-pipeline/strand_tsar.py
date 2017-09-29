#!/usr/bin/env python
#
#     strand_tsar.py: determine strandedness of fastq pair using STAR
#     Copyright (C) University of Manchester 2017 Peter Briggs
#

__version__ = "0.0.1"

#######################################################################
# Imports
#######################################################################

import sys
import os
import argparse
import tempfile
import random
import subprocess
import shutil
import logging
from bcftbx.utils import find_program
from bcftbx.ngsutils import getreads
from bcftbx.ngsutils import getreads_subset

#######################################################################
# Main script
#######################################################################

if __name__ == "__main__":
    # Process command line
    p = argparse.ArgumentParser(
        description="Generate strandedness statistics "
        "for FASTQ pair",
        version=__version__)
    p.add_argument("r1",metavar="R1",
                   default=None,
                   help="R1 Fastq file")
    p.add_argument("r2",metavar="R2",
                   default=None,
                   help="R2 Fastq file")
    p.add_argument("star_genomedir",metavar="STAR_GENOMEDIR",
                   default=None,
                   help="STAR genomeDir")
    p.add_argument("--subset",
                   type=int,
                   default=10000,
                   help="use a random subset of read pairs "
                   "from the input Fastqs (default: 10000)")
    p.add_argument("-o","--outdir",
                   default=None,
                   help="specify directory to write final "
                   "outputs to (default: current directory)")
    p.add_argument("-n",
                   type=int,
                   default=1,
                   help="number of threads to run STAR with "
                   "(default: 1)")
    args = p.parse_args()
    # Check that STAR is on the path
    star_exe = find_program("STAR")
    if star_exe is None:
        logging.critical("STAR not found")
        sys.exit(1)
    print "Using STAR from %s" % star_exe
    # Output directory
    if args.outdir is None:
        outdir = os.getcwd()
    else:
        outdir = os.path.abspath(args.outdir)
    if not os.path.exists(outdir):
        logging.critical("Output directory doesn't exist: %s" %
                         outdir)
        sys.exit(1)
    # Prefix for output
    prefix = "strand_tsar_"
    # Create a temporary working directory
    working_dir = tempfile.mkdtemp(suffix=".strand_tsar",
                                   dir=os.getcwd())
    # Make subset of input read pairs
    nreads = sum(1 for i in getreads(os.path.abspath(args.r1)))
    print "%d reads" % nreads
    if args.subset > nreads:
        print "Actual number of read pairs smaller than requested subset"
        subset = nreads
    else:
        subset = args.subset
        print "Using random subset of %d read pairs" % subset
    subset_indices = random.sample(xrange(nreads),subset)
    fastqs = []
    for fq in (args.r1,args.r2):
        fq_subset = os.path.join(working_dir,
                                 os.path.basename(fq))
        if fq_subset.endswith(".gz"):
            fq_subset = '.'.join(fq_subset.split('.')[:-1])
        fq_subset = "%s.subset.fq" % '.'.join(fq_subset.split('.')[:-1])
        with open(fq_subset,'w') as fp:
            for read in getreads_subset(os.path.abspath(fq),
                                        subset_indices):
                fp.write('\n'.join(read) + '\n')
        fastqs.append(fq_subset)
    # Build a command line to run STAR
    star_cmd = [star_exe,
                '--runMode','alignReads',
                '--genomeLoad','NoSharedMemory',
                '--genomeDir',os.path.abspath(args.star_genomedir),
                '--readFilesIn',
                fastqs[0],
                fastqs[1],
                '--quantMode','GeneCounts',
                '--outSAMtype','BAM','Unsorted',
                '--outSAMstrandField','intronMotif',
                '--outFileNamePrefix',prefix,
                '--runThreadN',str(args.n)]
    print "Running %s" % ' '.join(star_cmd)
    subprocess.check_output(star_cmd,cwd=working_dir)
    # Process the STAR output
    out_file = os.path.join(working_dir,
                            "%sReadsPerGene.out.tab" % prefix)
    if not os.path.exists(out_file):
        raise Exception("Failed to find .out file: %s" % out_file)
    sum_col2 = 0
    sum_col3 = 0
    sum_col4 = 0
    with open(out_file) as out:
        for i,line in enumerate(out):
            if i < 4:
                # Skip first four lines
                continue
            # Process remaining delimited columns
            cols = line.rstrip('\n').split('\t')
            sum_col2 += int(cols[1])
            sum_col3 += int(cols[2])
            sum_col4 += int(cols[3])
    print "Sums:"
    print "- col2: %d" % sum_col2
    print "- col3: %d" % sum_col3
    print "- col4: %d" % sum_col4
    forward_1st = float(sum_col3)/float(sum_col4)*100.0
    reverse_2nd = float(sum_col2)/float(sum_col4)*100.0
    print "Strand percentages:"
    print "- 1st forward: %.2f%%" % forward_1st
    print "- 2nd reverse: %.2f%%" % reverse_2nd
    # Write output file
    outfile = "%s_strand_tsar.txt" % os.path.join(
        outdir,
        os.path.basename(strip_ngs_extensions(args.r1)))
    with open(outfile,'w') as fp:
        # Header
        fp.write("#Strand_tsar version: %s\t"
                 "#Aligner: %s\t"
                 "#Reads in subset: %s\n" % (__version__,
                                             "STAR",
                                             subset))
        fp.write("#Genome\t1st forward\t2nd reverse\n")
        fp.write("%s\t%.2f\t%.2f\n" % (args.star_genomedir,
                                       forward_1st,
                                       reverse_2nd))
    # Clean up the working dir
    shutil.rmtree(working_dir)
