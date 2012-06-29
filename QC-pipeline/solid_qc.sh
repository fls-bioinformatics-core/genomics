#!/bin/sh
#
# Script to run QC steps on SOLiD data
#
# Usage: solid_qc.sh <csfasta> <qual>
#
function usage() {
    echo "Usage: solid_qc.sh <csfasta_file> <qual_file> [ <csfasta_f5> <qual_f5> ]"
    echo ""
    echo "Run FASTQ generation and QC pipeline for SOLiD data:"
    echo ""
    echo "* create fastq file"
    echo "* check for contamination using fastq_screen"
    echo "* generate QC boxplots"
    echo "* preprocess/filter using polyclonal and error tests"
    echo "  and generate fastq and boxplots for filtered data"
    echo ""
    echo "If F5 files are also supplied then run in paired-end mode"
}
#
# QC pipeline consists of the following steps:
#
# Primary data:
# * create fastq files (solid2fastq)
# * check for contamination (fastq_screen)
# * generate QC boxplots (qc_boxplotter)
# * filter primary data and make new csfastq/qual files
#   (SOLiD_preprocess_filter)
# * remove unwanted filter files
# * generate QC boxplots for filtered data (qc_boxplotter)
# * compare number of reads after filtering with original
#   data files
#
# Check command line
if [ $# -lt 2 ] || [ $# -gt 4 ] || [ "$1" == "-h" ] || [ "$1" == "--help" ] ; then
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
#===========================================================================
# Main script
#===========================================================================
#
# Set umask to allow group read-write on all new files etc
umask 0002
#
# Get the input files
CSFASTA=$(abs_path $1)
QUAL=$(abs_path $2)
if [ ! -f "$CSFASTA" ] || [ ! -f "$QUAL" ] ; then
    echo "csfasta and/or qual files not found"
    exit
fi
#
paired_end=no
if [ ! -z "$3" ] && [ ! -z "$4" ] ; then
    paired_end=yes
    CSFASTA_F5=$(abs_path $3)
    QUAL_F5=$(abs_path $4)
    if [ ! -f "$CSFASTA_F5" ] || [ ! -f "$QUAL_F5" ] ; then
	echo "F5 csfasta and/or qual files not found"
	exit
    fi
fi
#
# Get the data directory i.e. location of the input files
datadir=`dirname $CSFASTA`
#
# Report
echo ========================================================
echo SOLiD QC pipeline
echo ========================================================
echo Started   : `date`
echo Running in: `pwd`
echo data dir  : $datadir
echo csfasta   : `basename $CSFASTA`
echo qual      : `basename $QUAL`
if [ "$paired_end" == "yes" ] ; then
    echo F5 csfasta: `basename $CSFASTA_F5`
    echo F5 qual   : `basename $QUAL_F5`
fi
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
: ${SOLID2FASTQ:=solid2fastq}
: ${QC_BOXPLOTTER:=qc_boxplotter.sh}
: ${SOLID_PREPROCESS_FILTER:=SOLiD_preprocess_filter_v2.pl}
: ${REMOVE_MISPAIRS:=remove_mispairs.pl}
: ${SEPARATE_PAIRED_FASTQ:=separate_paired_fastq.pl}
#
# Check: all files should be in the same directory
if [ `dirname $CSFASTA` != `dirname $QUAL` ] ; then
    echo ERROR one or more csfasta and qual files are in different directories
    exit 1
elif [ "$paired_end" == "yes" ] ; then
    if [ `dirname $CSFASTA_F5` != `dirname $QUAL_F5` ] || \
	[ `dirname $CSFASTA` != `dirname $CSFASTA_F5` ] ; then
	echo ERROR one or more csfasta and qual files are in different directories
	exit 1
    fi
fi
#
#############################################
# FASTQ GENERATION
#############################################
#
# Run solid2fastq to make fastq file
if [ "$paired_end" == "no" ] ; then
    echo Running single end pipeline
    # Single end data
    # Fastq generation (all reads)
    fastq=$(baserootname $CSFASTA).fastq
    run_solid2fastq ${CSFASTA} ${QUAL}
    # SOLiD_preprocess_filter
    solid_preprocess_filter --nofastq --nostats ${CSFASTA} ${QUAL}
    # Collect filter file names
    preprocess_filter_files=$(solid_preprocess_files $(baserootname $CSFASTA))
    csfasta_filt=`echo $preprocess_filter_files | cut -d" " -f1`
    qual_filt=`echo $preprocess_filter_files | cut -d" " -f2`
    # Fastq generation for filtered data
    run_solid2fastq ${csfasta_filt} ${qual_filt}
    # Generate filtering statistics
    fastq_filt=`echo $(baserootname $csfasta_filt)`.fastq
    `dirname $0`/fastq_stats.sh -f SOLiD_preprocess_filter.stats $fastq $fastq_filt
else
    echo Running paired end pipeline
    # Paired end data
    # Fastq generation (all reads)
    fastq=`echo $(baserootname $CSFASTA) | sed 's/_F3//g'`_paired.fastq
    run_solid2fastq --separate-pairs ${CSFASTA} ${QUAL} ${CSFASTA_F5} ${QUAL_F5} $(rootname $fastq)
    # SOLiD_preprocess_filter on F3 and F5 separately
    solid_preprocess_filter --nofastq --nostats ${CSFASTA} ${QUAL}
    solid_preprocess_filter --nofastq --nostats ${CSFASTA_F5} ${QUAL_F5}
    # Collect filter file names
    preprocess_filter_files=$(solid_preprocess_files $(baserootname $CSFASTA))
    csfasta_filt_f3=`echo $preprocess_filter_files | cut -d" " -f1`
    qual_filt_f3=`echo $preprocess_filter_files | cut -d" " -f2`
    preprocess_filter_files=$(solid_preprocess_files $(baserootname $CSFASTA_F5))
    csfasta_filt_f5=`echo $preprocess_filter_files | cut -d" " -f1`
    qual_filt_f5=`echo $preprocess_filter_files | cut -d" " -f2`
    # Fastq generation for filtered data
    # "Strict" filtering = combine for F3 and F5 after filtering both
    fastq_strict=`echo $(baserootname $CSFASTA) | sed 's/_F3//g'`_paired_F3_and_F5_filt.fastq
    run_solid2fastq --remove-mispairs --separate-pairs ${csfasta_filt_f3} ${qual_filt_f3} \
	${csfasta_filt_f5} ${qual_filt_f5} $(rootname $fastq_strict)
    # "Lenient" filtering = combine filtered F3 with all F5
    fastq_lenient=`echo $(baserootname $CSFASTA) | sed 's/_F3//g'`_paired_F3_filt.fastq
    run_solid2fastq --remove-mispairs --separate-pairs ${csfasta_filt_f3} ${qual_filt_f3} \
	${CSFASTA_F5} ${QUAL_F5} $(rootname $fastq_lenient)
    # Generate filtering statistics
    `dirname $0`/fastq_stats.sh -f SOLiD_preprocess_filter_paired.stats \
	$fastq $fastq_lenient $fastq_strict
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
run_fastq_screen --color $fastq
#
# QC_boxplots
#
# Move to qc directory
cd qc
#
# Boxplots for original primary data
qc_boxplotter $QUAL
if [ "$paired_end" == "yes" ] ; then
    qc_boxplotter $QUAL_F5
fi
#
# Boxplots for filtered data
qual=`echo $(solid_preprocess_files ${WORKING_DIR}/$(baserootname $CSFASTA)) | cut -d" " -f2`
if [ ! -z "$qual" ] ; then
    qc_boxplotter $qual
else
    echo Unable to locate preprocess filtered QUAL file, boxplot skipped
fi
if [ "$paired_end" == "yes" ] ; then
    qual=`echo $(solid_preprocess_files ${WORKING_DIR}/$(baserootname $CSFASTA_F5)) | cut -d" " -f2`
    if [ ! -z "$qual" ] ; then
	qc_boxplotter $qual
    else
	echo Unable to locate preprocess filtered F5 QUAL file, boxplot skipped
    fi
fi
#
# Return to parent directory
cd ..
#
# Set permissions and group (if specified)
if [ ! -z "$SET_GROUP" ] ; then
    echo Recursively setting group to $SET_GROUP
    chgrp -R --quiet $SET_GROUP *
fi
if [ ! -z "$SET_PERMISSIONS" ] ; then
    echo Recursively setting permissions to $SET_PERMISSIONS
    chmod -R $SET_PERMISSIONS *
fi
#
echo SOLiD QC pipeline completed: `date`
exit
#
