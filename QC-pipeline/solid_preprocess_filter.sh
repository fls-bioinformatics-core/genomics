#!/bin/sh
#
# Script to run SOLiD_preprocess_filter steps on SOLiD data
#
# Usage: solid_preprocess_filter.sh [options] <csfasta> <qual>
#
function usage() {
    echo "Usage: solid_process_filter.sh [options] <csfasta> <qual>"
    echo ""
    echo "Run SOLiD_preprocess_filter_v2.pl script and calculate filtering"
    echo "statistics."
    echo ""
    echo "Options:"
    echo ""
    echo "  --nofastq: skip FASTQ generation after filtering"
    echo "  --nostats: skip statistics generation"
    echo ""
    echo "By default the preprocess/filter program is run using FLS Bioinf"
    echo "settings."
    echo ""
    echo "However: any options explicitly specified on the command line are"
    echo "used instead of the FLS Bioinf settings (which are essentially"
    echo "ignored, with the defaults for any parameter reverting to those"
    echo "in the underlying SOLiD_preprocess_filter_v2.pl program)."
    echo ""
    echo "Input"
    echo "  csfasta and qual file pair"
    echo ""
    echo "Output"
    echo "  <csfasta_base>_T_F3.csfasta"
    echo "  <csfasta_base>_QV_T_F3.qual"
    echo "  <csfasta_base>_T_F3.fastq (unless --nofastq option specified)"
    echo "  Also writes statistics to 'SOLID_preprocess_filter.stats'"
}
# Check command line
if [ $# -lt 2 ] || [ "$1" == "-h" ] || [ "$1" == "--help" ] ; then
    usage
    exit
fi
#
#===========================================================================
# Import function libraries
#===========================================================================
##
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
# Process command line options
make_fastq=yes
do_stats=yes
while [ $# -gt 2 ] ; do
    case "$1" in
	--nofastq)
	    # Turn off fastq generation
	    make_fastq=
	    ;;
	--nostats)
	    # Turn off post filtering statistics
	    do_stats=
	    ;;
	*)
	    # Collect all other arguments to pass directly to
	    # SOLiD_preprocess_filter
	    FILTER_OPTIONS="$FILTER_OPTIONS $1"
	    ;;
    esac
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
: ${SOLID_PREPROCESS_FILTER:=SOLiD_preprocess_filter_v2.pl}
: ${FILTER_OPTIONS:="-x y -p 3 -q 22 -y y -e 10 -d 9"}
#
# Report
echo ========================================================
echo SOLiD_preprocess_filter
echo ========================================================
echo Started   : `date`
echo Running in: `pwd`
echo csfasta   : $csfasta
echo qual      : $qual
echo Filter options: $FILTER_OPTIONS
#
# Check if processed files already exist
if [ ! -z "$(solid_preprocess_files $(baserootname $csfasta))" ] ; then
    # Don't repeat the filtering
    echo Filtered csfasta and qual files already exist, skipping preprocess filter
    # Set the csfasta file name for the stats
    processed_csfasta=`echo $(solid_preprocess_files $(baserootname $csfasta)) | cut -d" " -f1`
else
    # Make a temporary directory to run in
    # This stops incomplete processing files being written to the working
    # directory which might be left behind if the preprocessor stops (or
    # is stopped) prematurely
    wd=`pwd`
    tmp=$(make_temp -d --tmpdir=$wd --suffix=.preprocess)
    cd $tmp
    echo "Working in temporary directory ${tmp}"
    # Run preprocessor
    cmd="${SOLID_PREPROCESS_FILTER} -o $(baserootname $csfasta) ${FILTER_OPTIONS} -f ${csfasta} -g ${qual}"
    echo $cmd
    $cmd
    # Report exit status
    status=$?
    echo "Preprocess filter finished: exit status $status"
    # Output files
    preprocess_outputs=$(solid_preprocess_files $(baserootname $csfasta))
    # Move back to working dir and copy preprocessed files
    cd $wd
    if [ ! -z "$preprocess_outputs" ] ; then
	processed_csfasta=`echo $preprocess_outputs | cut -d" " -f1`
	processed_qual=`echo $preprocess_outputs | cut -d" " -f2`
	/bin/cp ${tmp}/${processed_csfasta} .
	echo Created ${processed_csfasta}
	/bin/cp ${tmp}/${processed_qual} .
	echo Created ${processed_qual}
    else
	echo WARNING no preprocess CSFASTA/QUAL file pair found
    fi
    # Remove temporary dir
    /bin/rm -rf ${tmp}
    # Create fastq file
    if [ "$make_fastq" == "yes" ] ; then
	if [ ! -z "$preprocess_outputs" ] ; then
	    run_solid2fastq $processed_csfasta $processed_qual
	else
	    echo WARNING unable to run solid2fastq without QUAL file
	fi
    else
	echo FASTQ generation switched off by --nofastq
    fi
fi
#
# Filter statistics: run separate filtering_stats.sh script
if [ "$do_stats" == "yes" ] ; then
    FILTERING_STATS=`dirname $0`/filtering_stats.sh
    STATS_FILE="SOLiD_preprocess_filter.stats"
    if [ -f "${FILTERING_STATS}" ] ; then
	if [ -f "${processed_csfasta}" ] ; then
	    ${FILTERING_STATS} ${csfasta} ${processed_csfasta} $STATS_FILE
	else
	    echo ERROR output csfasta file not found, filtering stats calculcation skipped
	fi
    else
	echo ERROR ${FILTERING_STATS} not found, filtering stats calculation skipped
    fi
else
    echo Filtering statistics switched off by --nostats
fi
#
echo solid_preprocess_filter completed: `date`
exit
##
#
