#!/bin/sh -e
#
# QC pipeline script for Illumina data
#
# Usage: illumina_qc.sh <fastq>
#
function usage() {
    echo "Usage: illumina_qc.sh <fastq>"
    echo ""
    echo "Run QC pipeline for Illumina data:"
    echo ""
    echo "* check for contamination using fastq_screen"
    echo "* generate QC metrics using FASTQC"
    echo ""
    echo "<fastq> can be either fastq or fastq.gz file"
}
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
#===========================================================================
# Main script
#===========================================================================
#
# Check command line
if [ $# -ne 1 ] || [ "$1" == "-h" ] || [ "$1" == "--help" ] ; then
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
    echo "fastq file not found"
    exit 1
fi
#
# Get the data directory i.e. location of the input file
datadir=`dirname $FASTQ`
#
# Report
echo ========================================================
echo ILLUMINA QC pipeline
echo ========================================================
echo Started   : `date`
echo Running in: `pwd`
echo data dir  : $datadir
echo fastq     : `basename $FASTQ`
echo hostname  : $HOSTNAME
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
# Working directory
WORKING_DIR=`pwd`
#
# Set the programs
# Override these defaults by setting them in qc.setup
: ${FASTQ_SCREEN:=fastq_screen}
: ${FASTQ_SCREEN_CONF_DIR:=}
: ${FASTQC:=fastqc}
#
#############################################
# FASTQ MANIPULATIONS
#############################################
#
# Unpack gzipped fastq file
ext=$(getextension $FASTQ)
if [ "$ext" == "gz" ] ; then
    echo Input FASTQ is gzipped, making unzipped version
    uncompressed_fastq=$(baserootname $FASTQ)
    gzip -dc $FASTQ > $uncompressed_fastq
fi
#
#############################################
# QC
#############################################
#
# Create 'qc' subdirectory
if [ ! -d "qc" ] ; then
    mkdir qc
fi
#
# Run fastq_screen
run_fastq_screen $FASTQ
#
# Run FASTQC
echo "Running FastQC command: ${FASTQC}"
${FASTQC} --version
${FASTQC} --outdir qc $FASTQ
#
# Update permissions and group (if specified)
set_permissions_and_group "$SET_PERMISSIONS" "$SET_GROUP"
#
echo ILLUMINA QC pipeline completed: `date`
exit
##
#
