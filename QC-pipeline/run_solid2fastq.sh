#!/bin/sh
#
# Script to run solid2fastq program on SOLiD data
#
# Usage: qc.sh <csfasta> <qual>
#
function usage() {
    echo "Usage: run_solid2fastq.sh [--gzip] <csfasta_file> <qual_file>"
    echo ""
    echo "Generate fastq file from csfasta/qual file pair using"
    echo "solid2fastq program"
    echo ""
    echo "Options:"
    echo "  --gzip: compress the output fastq file using gzip"
}
#
# Check command line
if [ $# -lt 2 ] || [ "$1" == "-h" ] || [ "$1" == "--help" ] ; then
    usage
    exit
fi
#
#===========================================================================
# Import function libraries
#===========================================================================
#
# General shell functions
if [ -f functions.sh ] ; then
    # Import local copy
    . functions.sh
else
    # Import version in share
    . `dirname $0`/../share/functions.sh
fi
#
# NGS-specific functions
if [ -f ngs_utils.sh ] ; then
    # Import local copy
    . ngs_utils.sh
else
    # Import version in share
    . `dirname $0`/../share/ngs_utils.sh
fi
#
#
#===========================================================================
# Main script
#===========================================================================
#
# Set umask to allow group read-write on all new files etc
umask 0002
#
# Check for --gzip option
do_gzip=
if [ "$1" == "--gzip" ] ; then
    do_gzip=yes
    shift
fi
#
# Get the input files
CSFASTA=$(abs_path $1)
QUAL=$(abs_path $2)
#
#
if [ ! -f "$CSFASTA" ] || [ ! -f "$QUAL" ] ; then
    echo "csfasta and/or qual files not found"
    exit
fi
#
# Get the data directory i.e. location of the input files
datadir=`dirname $CSFASTA`
#
# Report
echo ========================================================
echo Generate FASTQ file
echo ========================================================
echo Started   : `date`
echo Running in: `pwd`
echo data dir  : $datadir
echo csfasta   : `basename $CSFASTA`
echo qual      : `basename $QUAL`
#
# Set up environment
QC_SETUP=`dirname $0`/qc.setup
if [ -f "${QC_SETUP}" ] ; then
    echo Sourcing qc.setup to set up environment
    . ${QC_SETUP}
else
    echo WARNING qc.setup not found in `dirname $0`
fi
#
# Run solid2fastq to make fastq file
run_solid2fastq ${CSFASTA} ${QUAL}
#
# Compress if requested
if [ "$do_gzip" == "yes" ] ; then
    fastq=$(baserootname ${CSFASTA}).fastq
    zip=${fastq}.gz
    if [ ! -f $fastq ] ; then
	echo ERROR no fastq file: $fastq
	exit 1
    fi
    if [ -f $zip ] ; then
	echo "Zipped fastq already exists, skipping"
    else
	echo "Compressing fastq file using gzip"
	gzip $fastq
	if [ ! -f $zip ] ; then
	    echo ERROR failed to make $zip
	    exit 1
	fi
    fi
fi
##
#