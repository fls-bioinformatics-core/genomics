#!/usr/bin/env python

import sys
import os
import argparse
import itertools
import tempfile
import logging

def split_chrom_name(s):
    s0 = s.split('_')
    if s0[0].startswith('chr'):
        s0[0] = s0[0][3:]
        try:
            s0[0] = int(s0[0])
        except ValueError:
            pass
    return s0

def cmp_chrom_names(x,y):
    for i,j in itertools.izip_longest(split_chrom_name(x),
                                      split_chrom_name(y)):
        c = cmp(i,j)
        if c != 0:
            return c
    return 0

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("fasta",
                   help="FASTA file to reorder")
    args = p.parse_args()
    fasta = os.path.abspath(args.fasta)
    if not os.path.exists(fasta):
        logging.critical("%s: file not found" % fasta)
        sys.exit(1)
    print "Extracting chromosomes..."
    chroms = list()
    wd = tempfile.mkdtemp()
    print "Using working dir %s" % wd
    with open(fasta,'rU') as fp:
        chromfile = None
        for line in fp:
            if line.startswith(">"):
                if chromfile is not None:
                    chromfile.close()
                chrom = line.strip()[1:]
                print "\t%s" % chrom
                chroms.append(chrom)
                chromfile = open(os.path.join(wd,"%s.fa" % chrom),'w')
            chromfile.write(line)
    if chromfile is not None:
        chromfile.close()
    print "Found %d chromosomes" % len(chroms)
    chroms = sorted(chroms,cmp=cmp_chrom_names)
    print "Reordering chromosomes..."
    fasta_reordered = "%s.%s%s" % (
        os.path.splitext(os.path.basename(fasta))[0],
        "karyotypic",
        os.path.splitext(os.path.basename(fasta))[1])
    with open(fasta_reordered,'w') as fp:
        for chrom in chroms:
            chromfile = os.path.join(wd,"%s.fa" % chrom)
            print "\t%s (%s)" % (chrom,chromfile)
            with open(chromfile,'r') as fpp:
                fp.write(fpp.read())
    print "Wrote reordered FASTA file to %s" % fasta_reordered
    print "Finished"
