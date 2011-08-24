#!/bin/sh
#
# Wrapper for running make_macs_xls.py
#
# Get the location for these scripts
BIN_DIR=`dirname $0`
#
if [ -z "$PYTHONPATH" ] ; then
    export PYTHONPATH=${BIN_DIR}/../share
else
    export PYTHONPATH=${PYTHONPATH}:${BIN_DIR}/../share
fi
#
# Run the spreadsheet generator
python ${BIN_DIR}/make_macs_xls.py $@
##
#
