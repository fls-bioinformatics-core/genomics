#!/bin/sh
#
# Wrapper for running make_macs_xls.sh
#
# Get the location for these scripts
BIN_DIR=`dirname $0`
#
# See if Python virtualenv is available
virtualenv=`which virtualenv`
if [ "$virtualenv" == "" ] ; then
    echo "virtualenv not found"
    exit 1
fi
#
# Create and activate virtualenv for this run
python_env=make_macs_xls_venv
if [ ! -d $python_env ] ; then
    virtualenv --no-site-packages $python_env
fi
if [ ! -e ${python_env}/bin/activate ] ; then
    echo "unable to activate virtualenv"
    exit 1
fi
. ${python_env}/bin/activate
#
# Get xlwt
pip install xlwt
#
# Run the spreadsheet generator
python ${BIN_DIR}/make_macs_xls.py $@
#
# Exit and destroy the virtualenv
deactivate
##rm -rf ${python_env}
exit
##