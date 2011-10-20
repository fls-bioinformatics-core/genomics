#!/bin/sh
#
# Script to run QC steps on SOLiD data
#
# Usage: qc.sh <csfasta> <qual>
#
function usage() {
    echo "Usage: qc.sh <csfasta_file> <qual_file>"
    echo ""
    echo "Run QC pipeline:"
    echo ""
    echo "* create fastq file"
    echo "* check for contamination using fastq_screen"
    echo "* generate QC boxplots"
    echo "* preprocess/filter using polyclonal and error tests"
    echo "  and generate fastq and boxplots for filtered data"
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
if [ $# -ne 2 ] || [ "$1" == "-h" ] || [ "$1" == "--help" ] ; then
    usage
    exit
fi
#
#===========================================================================
# Import function libraries
#===========================================================================
#
if [ -f functions.sh ] ; then
    # Import local copies
    . functions.sh
else
    # Import versions in share
    . `dirname $0`/../share/functions.sh
fi
#
#===========================================================================
# Local functions
#===========================================================================
#
# run_solid2fastq: create fastq file
#
# Provide names of csfasta and qual files (can include leading
# paths)
#
# Creates fastq file in current directory
#
# Usage: solid2fastq <csfasta> <qual>
function run_solid2fastq() {
    # Input files
    csfasta=$(abs_path ${1})
    qual=$(abs_path ${2})
    #
    # Determine basename for fastq file: same as csfasta, with
    # any leading directory and extension stripped off
    fastq_base=$(baserootname ${csfasta})
    #
    # Check if fastq file already exists
    fastq=${fastq_base}.fastq
    if [ -f "${fastq}" ] ; then
	echo Fastq file already exists, skipping solid2fastq
    else
	echo "--------------------------------------------------------"
	echo Executing solid2fastq
	echo "--------------------------------------------------------"
	# Make a temporary directory to run in
	# This stops incomplete fastq files being written to the working
	# directory which might be left behind if solid2fastq stops (or
	# is stopped) prematurely
	wd=`pwd`
	tmp=`mktemp -d`
	cd $tmp
	# Run solid2fastq
	cmd="${SOLID2FASTQ} -o $fastq_base $csfasta $qual"
	echo $cmd
	$cmd
	# Move back to working dir and copy preprocessed files
	cd $wd
	if [ -f "${tmp}/${fastq}" ] ; then
	    /bin/cp ${tmp}/${fastq} .
	    echo Created ${fastq}
	else
	    echo WARNING no file ${fastq}
	fi
	# Remove temporary dir
	/bin/rm -rf ${tmp}
    fi
}
#
# Run SOLiD_preprocess_filter
#
# Filter original SOLiD data using polyclonal and error tests
#
# Usage: solid_preprocess_filter <csfasta> <qual>
function solid_preprocess_filter() {
    # Input file names
    csfasta=$1
    qual=$2
    # Output file names
    processed_csfasta=$(baserootname $csfasta)_T_F3.csfasta
    processed_qual=$(baserootname $csfasta)_QV_T_F3.qual
    # Check if processed files already exist
    if [ -f "${processed_csfasta}" ] && [ -f "${processed_qual}" ] ; then
	echo Filtered csfasta and qual files already exist, skipping preprocess filter
    else
	echo "--------------------------------------------------------"
	echo Executing SOLiD_preprocess_filter
	echo "--------------------------------------------------------"
	# Make a temporary directory to run in
	# This stops incomplete processing files being written to the working
	# directory which might be left behind if the preprocessor stops (or
	# is stopped) prematurely
	wd=`pwd`
	tmp=`mktemp -d`
	cd $tmp
	# Run preprocessor
	FILTER_OPTIONS="-x y -p 3 -q 22 -y y -e 10 -d 9"
	cmd="${SOLID_PREPROCESS_FILTER} -o $(baserootname $csfasta) ${FILTER_OPTIONS} -f ${csfasta} -g ${qual}"
	echo $cmd
	$cmd
	# Move back to working dir and copy preprocessed files
	cd $wd
	if [ -f "${tmp}/${processed_csfasta}" ] ; then
	    /bin/cp ${tmp}/${processed_csfasta} .
	    echo Created ${processed_csfasta}
	else
	    echo WARNING no file ${processed_csfasta}
	fi
	if [ -f "${tmp}/${processed_qual}" ] ; then
	    /bin/cp ${tmp}/${processed_qual} .
	    echo Created ${processed_qual}
	else
	    echo WARNING no file ${processed_csfasta}
	fi
	# Remove temporary dir
	/bin/rm -rf ${tmp}
    fi
}
#
# Compare reads for original and preprocess filtered data
#
# Usage: filtering_stats <csfasta>
function filtering_stats() {
    # Input csfasta
    csfasta_file=$1
    # Run separate filtering_stats.sh script
    FILTERING_STATS=`dirname $0`/filtering_stats.sh
    if [ -f "${FILTERING_STATS}" ] ; then
	${FILTERING_STATS} ${csfasta} SOLiD_preprocess_filter.stats
    else
	echo ERROR ${FILTERING_STATS} not found, filtering stats calculation skipped
    fi
}
#
# Run boxplotter
#
# Supply full path of input qual_file
#
# Usage: qc_boxplotter <qual_file>
function qc_boxplotter() {
    # Input qual file
    qual=$(abs_path ${1})
    # Qual base name
    qual_base=`basename $qual`
    # Check if boxplot files already exist
    if [ -f "${qual_base}_seq-order_boxplot.pdf" ] ; then
	echo Boxplot pdf already exists for ${qual_base}, skipping boxplotter
    else
	echo "--------------------------------------------------------"
	echo Executing QC_boxplotter: ${qual_base}
	echo "--------------------------------------------------------"
	# Make a link to the input qual file
	if [ ! -f "${qual_base}" ] ; then
	    echo Making symbolic link to qual file
	    /bin/ln -s ${qual} ${qual_base}
	fi
	cmd="${QC_BOXPLOTTER} $qual_base"
	$cmd
        # Clean up
	if [ -L "${qual_base}" ] ; then
	    echo Removing symbolic link to qual file
	    /bin/rm -f ${qual_base}
	fi
    fi
}
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
echo QC pipeline
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
#
# Check: both files should exist
if [ ! -f "$CSFASTA" ] || [ ! -f "$QUAL" ] ; then
    echo ERROR one or both of csfasta or qual files not found
    exit 1
fi
# Check: both files should be in the same directory
if [ `dirname $CSFASTA` != `dirname $QUAL` ] ; then
    echo ERROR csfasta and qual are in different directories
    exit 1
fi
#
# Run solid2fastq to make fastq file
run_solid2fastq ${CSFASTA} ${QUAL}
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
    fastq=$(baserootname $CSFASTA).fastq
    ${FASTQ_SCREEN_QC} ${fastq}
else
    echo ERROR ${FASTQ_SCREEN_QC} not found, fastq_screen step skipped
fi
#
# SOLiD_preprocess_filter
solid_preprocess_filter ${CSFASTA} ${QUAL}
#
# Filtering statistics
filtering_stats ${CSFASTA}
#
# Run solid2fastq to make fastq file from filtered files
run_solid2fastq $(baserootname $CSFASTA)_T_F3.csfasta $(baserootname $CSFASTA)_QV_T_F3.qual
#
# QC_boxplots
#
# Move to qc directory
cd qc
#
# Boxplots for original primary data
qc_boxplotter $QUAL
#
# Boxplots for filtered data
qc_boxplotter ${WORKING_DIR}/$(baserootname $CSFASTA)_QV_T_F3.qual
#
echo QC pipeline completed: `date`
exit
#
