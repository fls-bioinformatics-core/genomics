#!/bin/bash -e
#
# Run test of extract_reads.py
if [ ! -d output ] ; then
  mkdir output
fi
# Fastqs
extract_reads.py -n 5 $(dirname $0)/data/test_R1.fastq $(dirname $0)/data/test_R2.fastq
# Gzipped Fastqs
extract_reads.py -n 5 $(dirname $0)/data/test_R1.fastq.gz $(dirname $0)/data/test_R2.fastq.gz
##
#
