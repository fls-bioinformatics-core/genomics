#!/bin/bash -e
#
# Run test of run_qc_pipeline.py
if [ ! -d output ] ; then
  mkdir output
fi
run_qc_pipeline.py -h
run_qc_pipeline.py --version
run_qc_pipeline.py --runner=simple --log-dir=output $(dirname $0)/data/echo.sh $(dirname $0)/data/testdir
##
#
