#!/bin/bash
#
# Script to run SOLiD_preprocess_filter steps on SOLiD data
#
# Usage: solid_preprocess_truncation_filter.sh [options] <csfasta> <qual>
#
function usage() {
    echo "Usage: solid_preprocess_truncation_filter.sh [options] <csfasta> <qual>"
    echo ""
    echo "Run SOLiD_preprocess_filter_v2.pl script to do truncation and"
    echo "filtering, and calculate filtering statistics."
    echo ""
    echo "Options:"
    echo ""
    echo "  -t <yes|y|on|no|n|off>: (default y) truncate reads before running"
    echo "     the filter step"
    echo "  -u <length>: (default 30) truncation length (bp) for truncation step"
    echo "  -o <basename>: specify base name to use for output files (defaults"
    echo "     to the csfasta name if not specified)"
    echo ""
    echo "Any unrecognised options are passed to the preprocess filter step,"
    echo "over-riding the FLS Bioinf defaults (which are then ignored, with the"
    echo "defaults for any parameter reverting to those in the underlying"
    echo "SOLiD_preprocess_filter_v2.pl program)."
    echo ""
    echo "Input"
    echo "  csfasta and qual file pair"
    echo ""
    echo "Output"
    echo "  <basename>_<length>bp_T_F3.csfasta,"
    echo "  <basename>_<length>bp_QV_T_F3.qual"
    echo "  <basename>_<length>bp_T_F3.fastq"
    echo "  Also writes statistics to 'SOLID_preprocess_truncation_filter.stats'"
}
#
#===========================================================================
# Import function libraries
#===========================================================================
#
export PATH=$PATH:$(dirname $0)/../share
#
# General shell functions
. bcftbx.functions.sh
#
# NGS-specific functions
. bcftbx.ngs_utils.sh
#
#===========================================================================
# Local functions
#===========================================================================
#
# preprocess_truncate: run SOLiD_preprocess_filter_v2.pl to perform
# truncation of reads without any filtering.
#
# Usage: preprocess_truncate <csfasta> <qual> [ <output_basename> ]
function preprocess_truncate() {
    echo "--------------------------------------------------------"
    echo Executing preprocess_truncate
    echo "--------------------------------------------------------"
    # Input files
    local csfasta=$1
    local qual=$2
    # Basename for output files
    if [ ! -z $3 ] ; then
	local output_basename=$3
    else
	local output_basename=$(baserootname $csfasta)
    fi
    # Run preprocessor with truncation options
    local cmd="${SOLID_PREPROCESS_FILTER} -o $output_basename ${TRUNCATE_OPTIONS} -f ${csfasta} -g ${qual}"
    echo $cmd
    $cmd
    return $?
}
#
# preprocess_filter: run SOLiD_preprocess_filter_v2.pl to perform
# filtering of reads.
#
# Usage: preprocess_truncate <csfasta> <qual> [ <output_basename> ]
function preprocess_filter() {
    echo "--------------------------------------------------------"
    echo Executing preprocess_filter
    echo "--------------------------------------------------------"
    # Input files
    local csfasta=$1
    local qual=$2
    # Basename for output files
    if [ ! -z $3 ] ; then
	local output_basename=$3
    else
	local output_basename=$(baserootname $csfasta)
    fi
    # Run preprocessor with filter options
    local cmd="${SOLID_PREPROCESS_FILTER} -o $output_basename ${FILTER_OPTIONS} -f ${csfasta} -g ${qual}"
    echo $cmd
    $cmd
    return $?
}
#
#===========================================================================
# Main script
#===========================================================================
#
# Check command line
if [ $# -lt 2 ] || [ "$1" == "-h" ] || [ "$1" == "--help" ] ; then
    usage
   exit
fi
#
# Set umask to allow group read-write on all new files etc
umask 0002
#
# Initialise flags
do_truncation=y
truncation_length=30
output_basename=
#
# Collect the user arguments to supply to SOLiD_preprocess_filter
while [ $# -gt 2 ] ; do
    if [ "$1" == "-t" ] ; then
	# Truncation option
	if [ "$2" == "yes" ] || [ "$2" == "y" ] || [ "$2" == "on" ] ; then
	    do_truncation=yes
	else
	    do_truncation=
	fi
	shift
    elif [ "$1" == "-u" ] ; then
	# Truncation length
	truncation_length=$2
	shift
    elif [ "$1" == "-o" ] ; then
	# Base output file name
	output_basename=$2
	shift
    else
	# Add other options to the filter step
	FILTER_OPTIONS="$FILTER_OPTIONS $1"
    fi
    # Next argument
    shift
done
#
# Collect inputs
csfasta=$(abs_path $1)
qual=$(abs_path $2)
#
# Check files exist
if [ ! -f "$csfasta" ] ; then
    echo "ERROR csfasta file not found: $csfasta"
    usage
    exit 1
fi
if [ ! -f "$qual" ] ; then
    echo "ERROR qual file not found: $qual"
    usage
    exit 1
fi
#
# Set up environment
import_qc_settings
#
# Set the programs
# Override these defaults by setting them in qc.setup
: ${SOLID2FASTQ:=solid2fastq}
: ${SOLID_PREPROCESS_FILTER:=SOLiD_preprocess_filter_v2.pl}
: ${TRUNCATE_OPTIONS:="-x n -y n -n n -t y -u $truncation_length"}
: ${FILTER_OPTIONS:="-x y -p 3 -q 22 -y y -e 10 -d 9"}
#
# Report
echo ========================================================
echo SOLiD_preprocess_truncation_filter
echo ========================================================
echo Started   : `date`
echo Running in: `pwd`
echo csfasta   : $csfasta
echo qual      : $qual
echo Truncate options: $TRUNCATE_OPTIONS
echo Filter options: $FILTER_OPTIONS
#
# Output file names
if [ -z $output_basename ] ; then
    output_basename=$(baserootname $csfasta)
    if [ ! -z $do_truncation ] ; then
	output_basename=${output_basename}_${truncation_length}bp
    fi
fi
#
# Check if processed files already exist
if [ ! -z "$(solid_preprocess_files $(baserootname $csfasta))" ] ; then
    # Don't repeat the filtering
    echo Filtered csfasta and qual files already exist, skipping preprocess filter
    # Set the csfasta file name for the stats
    processed_csfasta=`echo $(solid_preprocess_files $(baserootname $csfasta)) | cut -d" " -f1`
else
    # Report initial number of reads
    n_reads=$(number_of_reads $csfasta)
    echo "Initial number of reads: $n_reads"
    # Make a temporary directory to run in
    # This stops incomplete processing files being written to the working
    # directory which might be left behind if the preprocessor stops (or
    # is stopped) prematurely
    wd=`pwd`
    tmp=$(make_temp -d --tmpdir=$wd --suffix=.preprocess)
    cd $tmp
    echo "Working in temporary directory ${tmp}"
    # Do truncation, if requested
    if [ ! -z $do_truncation ] ; then
	# Run preprocess truncation
	if ! preprocess_truncate $csfasta $qual "solid_preprocess_truncate" ; then
	    echo "Truncation finished with non-zero exit code indicating error"
	    echo "Stopping"
	    exit 1
	fi
	# Reset the files for next step
	# Output files from preprocess truncation
	preprocess_outputs=$(solid_preprocess_files solid_preprocess_truncate)
	processed_csfasta=`echo $preprocess_outputs | cut -d" " -f1`
	processed_qual=`echo $preprocess_outputs | cut -d" " -f2`
	# Move and rename for input to preprocess filtering step
	truncated_csfasta=`basename $csfasta`
	truncated_qual=`basename $qual`
	/bin/mv $processed_csfasta $truncated_csfasta
	/bin/mv $processed_qual $truncated_qual
	# Number of reads after truncation
	n_reads=$(number_of_reads $truncated_csfasta)
	echo "Number of reads after truncation: $n_reads"
    else
	echo "Skipping explicit truncation step"
    fi
    # Run preprocess filter
    if ! preprocess_filter $truncated_csfasta $truncated_qual $output_basename ; then
	echo "Filter finished with non-zero exit code indicating error"
	echo "Stopping"
	exit 1
    fi
    # Output files
    preprocess_outputs=$(solid_preprocess_files $output_basename)
    # Move back to working dir and copy preprocessed files
    cd $wd
    if [ ! -z "$preprocess_outputs" ] ; then
	processed_csfasta=`echo $preprocess_outputs | cut -d" " -f1`
	processed_qual=`echo $preprocess_outputs | cut -d" " -f2`
	/bin/cp ${tmp}/${processed_csfasta} .
	echo Created ${processed_csfasta}
	/bin/cp ${tmp}/${processed_qual} .
	echo Created ${processed_qual}
	n_reads=$(number_of_reads $processed_csfasta)
	echo "Number of reads after filter: $n_reads"
    else
	echo WARNING no preprocess CSFASTA/QUAL file pair found
    fi
    # Remove temporary dir
    /bin/rm -rf ${tmp}
    # Number of reads after filter
    if [ ! -z "$preprocess_outputs" ] ; then
	run_solid2fastq $processed_csfasta $processed_qual
    else
	echo WARNING unable to run solid2fastq without QUAL file
    fi
fi
#
# Filter statistics: run separate filtering_stats.sh script
FILTERING_STATS=`dirname $0`/filtering_stats.sh
STATS_FILE="SOLiD_preprocess_truncation_filter.stats"
if [ -f "${FILTERING_STATS}" ] ; then
    if [ -f "${processed_csfasta}" ] ; then
	${FILTERING_STATS} ${csfasta} ${processed_csfasta} $STATS_FILE
    else
	echo ERROR output csfasta file not found, filtering stats calculcation skipped
    fi
else
    echo ERROR ${FILTERING_STATS} not found, filtering stats calculation skipped
fi
#
echo solid_preprocess_truncation_filter completed: `date`
exit
##
#
