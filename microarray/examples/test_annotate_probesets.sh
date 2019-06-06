#!/bin/bash -e
#
# Run test of annotate_probesets.py
if [ ! -d output ] ; then
  mkdir output
fi
annotate_probesets.py $(dirname $0)/data/probesets.txt -o output/annotated_probesets.txt
##
#
