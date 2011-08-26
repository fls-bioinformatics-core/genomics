#!/bin/sh
#
# Wrapper for running make_macs_xls.py
#
# Get the location for the Python modules (i.e. Spreadsheet.py)
# Edit this if your local setup is different
PYTHON_LIBS=`dirname $0`/../share
#
# Update PYTHONPATH
if [ -z "$PYTHONPATH" ] ; then
    export PYTHONPATH=${PYTHON_LIBS}
else
    export PYTHONPATH=${PYTHONPATH}:${PYTHON_LIBS}
fi
#
# Run the spreadsheet generator
python `dirname $0`/make_macs_xls.py $@
##
#
