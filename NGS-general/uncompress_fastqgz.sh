#!/bin/bash -e
#
# Uncompress fastq.gz file
#
# Usage: illumina_qc.sh <fastq>
#
function usage() {
    echo "Usage: $(basename $0) <fastq>"
    echo ""
    echo "Create uncompressed copies of fastq.gz file (if"
    echo "input is fastq.gz)."
    echo ""
    echo "<fastq> can be either fastq or fastq.gz file"
    echo ""
    echo "The original file will not be removed or altered."
    echo ""
}
export PATH=$PATH:$(dirname $0)/../share
function import_functions() {
    if [ -z "$1" ] ; then
	echo ERROR no filename supplied to import_functions >2
    else
	echo Sourcing $1
	. $1
	if [ $? -ne 0 ] ; then
	    echo ERROR failed to import $1 >2
	fi
    fi
}
#
#===========================================================================
# Import function libraries
#===========================================================================
#
# General shell functions
import_functions bcftbx.functions.sh
#
# NGS-specific functions
import_functions bcftbx.ngs_utils.sh
#
#===========================================================================
# Main script
#===========================================================================
#
# Check command line
if [ $# -lt 1 ] || [ "$1" == "-h" ] || [ "$1" == "--help" ] ; then
    usage
    exit
fi
#
# Set umask to allow group read-write on all new files etc
umask 0002
#
# Get the input fastq file
FASTQ=$(abs_path $1)
if [ ! -f "$FASTQ" ] ; then
    echo "$FASTQ: fastq file not found"
    exit 1
fi
#
# Get the data directory i.e. location of the input file
datadir=`dirname $FASTQ`
#
# Report
echo ========================================================
echo UNCOMPRESS FASTQ.GZ
echo ========================================================
echo Started   : `date`
echo Running in: `pwd`
echo data dir  : $datadir
echo fastq     : `basename $FASTQ`
echo hostname  : $HOSTNAME
echo job id    : $JOB_ID
#
# Working directory
WORKING_DIR=`pwd`
#
# Base name for script
uncompress=$(baserootname $0)
#
# Base name for fastq files etc
fastq_base=`basename ${FASTQ%%.fastq*}`
#
# Unpack gzipped fastq file
ext=$(getextension $FASTQ)
if [ "$ext" == "gz" ] ; then
    uncompressed_fastq=$(baserootname $FASTQ)
    if [ ! -f $uncompressed_fastq ] ; then
	echo Input FASTQ is gzipped, making ungzipped version
	gzip -dc $FASTQ > $uncompressed_fastq.part
	mv $uncompressed_fastq.part $uncompressed_fastq
    else
	echo Ungzipped version of input FASTQ found
    fi
else
    echo Input FASTQ not gzipped
fi
#
# Update permissions and group (if specified)
set_permissions_and_group -R --quiet "$SET_PERMISSIONS" "$SET_GROUP"
#
echo UNCOMPRESS FASTQ.GZ completed: `date`
exit
##
#
