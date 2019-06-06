#!/bin/bash -e
#
# Run test of make_macs2_xls.py
if [ ! -d output ] ; then
  mkdir output
fi
make_macs2_xls.py -h
make_macs2_xls.py --version
make_macs2_xls.py -f xlsx --bed $(dirname $0)/data/MACS2010_20130419.XLS output/MACS2010_20130419.xlsx
make_macs2_xls.py -f xlsx --bed $(dirname $0)/data/MACS2010_20131216.XLS output/MACS2010_20131216.xlsx
make_macs2_xls.py -f xlsx $(dirname $0)/data/MACS2010_20131216_broad.XLS output/MACS2010_20131216_broad.xlsx
##
#
