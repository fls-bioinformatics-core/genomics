#!/bin/sh
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
# truncate
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
# filter
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
# run_solid2fastq: create fastq file
#
# Provide names of csfasta and qual files (can include leading
# paths)
#
# Creates fastq file in current directory
#
# Usage: solid2fastq <csfasta> <qual> [ <output_basename> ]
function run_solid2fastq() {
    # Input files
    local csfasta=$(abs_path ${1})
    local qual=$(abs_path ${2})
    #
    local status=0
    #
    # Determine basename for fastq file: if not explicitly
    # specified then is same as csfasta (with leading directory
    # and extension stripped off)
    if [ ! -z $3 ] ; then
	local fastq_base=$3
    else
	local fastq_base=$(baserootname ${csfasta})
    fi
    #
    # Check if fastq file already exists
    local fastq=${fastq_base}.fastq
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
	local wd=`pwd`
	local tmp=`mktemp -d`
	cd $tmp
	# Run solid2fastq
	local cmd="${SOLID2FASTQ} -o $fastq_base $csfasta $qual"
	echo $cmd
	$cmd
	# Termination status
	status=$?
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
    return $status
}
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
processed_csfasta=${output_basename}_T_F3.csfasta
processed_qual=${output_basename}_QV_T_F3.qual
#
# Check if processed files already exist
if [ -f "${processed_csfasta}" ] && [ -f "${processed_qual}" ] ; then
    echo Filtered csfasta and qual files already exist, skipping preprocess filter
else
    # Report initial number of reads
    n_reads=`grep -c "^>" ${csfasta}`
    echo "Initial number of reads: $n_reads"
    # Make a temporary directory to run in
    # This stops incomplete processing files being written to the working
    # directory which might be left behind if the preprocessor stops (or
    # is stopped) prematurely
    wd=`pwd`
    tmp=`mktemp -d`
    cd $tmp
    echo "Working in temporary directory ${tmp}"
    # Do truncation, if requested
    if [ ! -z $do_truncation ] ; then
	# Run preprocess truncation
	preprocess_truncate $csfasta $qual "solid_preprocess_truncate"
	# Reset the files for next step
	csfasta=`basename $csfasta`
	qual=`basename $qual`
	/bin/mv solid_preprocess_truncate_T_F3.csfasta $csfasta
	/bin/mv solid_preprocess_truncate_QV_T_F3.qual $qual
	# Number of reads after truncation
	n_reads=`grep -c "^>" ${csfasta}`
	echo "Number of reads after truncation: $n_reads"
    else
	echo "Skipping explicit truncation step"
    fi
    # Run preprocess filter
    preprocess_filter $csfasta $qual $output_basename
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
    # Number of reads after filter
    n_reads=`grep -c "^>" ${processed_csfasta}`
    echo "Number of reads after filter: $n_reads"
    # Create fastq file
    run_solid2fastq $processed_csfasta $processed_qual
fi
#
# Filter statistics: run separate filtering_stats.sh script
FILTERING_STATS=`dirname $0`/filtering_stats.sh
if [ -f "${FILTERING_STATS}" ] ; then
    if [ -f "${processed_csfasta}" ] ; then
	${FILTERING_STATS} ${csfasta} ${processed_csfasta} SOLiD_preprocess_truncation_filter.stats
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
