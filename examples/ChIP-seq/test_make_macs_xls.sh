#!/bin/bash -e
#
# Run test of make_macs_xls.py
if [ ! -d output ] ; then
  mkdir output
fi
make_macs_xls.py -h
make_macs_xls.py --version
make_macs_xls.py $(dirname $0)/data/MACS140beta.XLS output/MACS140beta.xls
##
#
