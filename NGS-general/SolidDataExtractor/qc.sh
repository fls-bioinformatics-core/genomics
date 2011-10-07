#!/bin/sh
#
# Script to run QC steps on SOLiD data
#
# Usage: qc.sh <csfasta> <qual>
#
# Set umask to allow group read-write on all new files etc
umask 0002
#
# Get the input files
csfasta=`basename $1`
qual=`basename $2`
#
# Get the data directory i.e. location of the input files
csfastadir=`dirname $1`
if [ "$csfastadir" == "." ] ; then
    csfastadir=`pwd`
fi
qualdir=`dirname $2`
if [ "$qualdir" == "." ] ; then
    qualdir=`pwd`
fi
datadir=$csfastadir
#
# Report
echo ========================================================
echo QC pipeline
echo ========================================================
echo Started   : `date`
echo Running in: `pwd`
echo data dir  : $datadir
echo csfasta   : $csfasta
echo qual      : $qual
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
# Set the programs
# Override these defaults by setting them in qc.setup
: ${FASTQ_SCREEN:=fastq_screen}
: ${FASTQ_SCREEN_CONF_DIR:=}
: ${SOLID2FASTQ:=solid2fastq}
: ${QC_BOXPLOTTER:=colour_QC_script.sh}
#
# Check: both files should be in the same directory
if [ "$qualdir" != "$csfastadir" ] ; then
    echo ERROR csfasta and qual are in different directories
    exit 1
fi
#
# solid2fastq: create fastq file
#
# Determine basename for fastq file: same as csfasta, with
# any leading directory and extension stripped off
csfasta_base=${csfasta%.*}
#
# Check if fastq file already exists
fastq=${csfasta_base}.fastq
if [ -f "${fastq}" ] ; then
    echo Fastq file already exists, skipping solid2fastq
else
    echo "--------------------------------------------------------"
    echo Executing solid2fastq
    echo "--------------------------------------------------------"
    cmd="${SOLID2FASTQ} -o $csfasta_base ${datadir}/${csfasta} ${datadir}/${qual}"
    echo $cmd
    $cmd
fi
#
# Create 'qc' subdirectory
if [ ! -d "qc" ] ; then
    mkdir qc
fi
#
# fastq_screen
#
# Run separate fastq_screen.sh script
FASTQ_SCREEN_QC=`dirname $0`/fastq_screen.sh
if [ -f "${FASTQ_SCREEN_QC}" ] ; then
    ${FASTQ_SCREEN_QC} ${fastq}
else
    echo ERROR ${FASTQ_SCREEN_QC} not found, fastq_screen step skipped
fi
#
# QC_boxplotter
#
# Move to qc directory
cd qc
#
# Check if boxplot files already exist
if [ -f "${qual}_seq-order_boxplot.pdf" ] ; then
    echo Boxplot pdf already exists, skipping boxplotter
else
    echo "--------------------------------------------------------"
    echo Executing QC_boxplotter
    echo "--------------------------------------------------------"
    # Make a link to the input qual file
    if [ ! -f "${qual}" ] ; then
	echo Making symbolic link to qual file
	/bin/ln -s ${datadir}/${qual} ${qual}
    fi
    cmd="${QC_BOXPLOTTER} $qual"
    $cmd
    # Clean up
    if [ -L "${qual}" ] ; then
	echo Removing symbolic link to qual file
	/bin/rm -f ${qual}
    fi
fi
#
echo QC pipeline completed: `date`
exit
#
