#!/bin/bash
#
# Script to run solid2fastq program on SOLiD data
#
# Usage: qc.sh <csfasta> <qual>
#
function usage() {
    echo "Usage: run_solid2fastq.sh OPTIONS <csfasta_file> <qual_file> [<csfasta_file> <qual_file> ] "
    echo ""
    echo "Generate fastq file from csfasta/qual file pair using"
    echo "solid2fastq program."
    echo ""
    echo "If second csfasta/qual pair is provided then create an"
    echo "interleaved fastq (in this case the first pair is assumed"
    echo "to be F3 reads and the second F5). Use the --remove-mispairs"
    echo "option to remove 'singleton' reads from the final fastq."
    echo ""
    echo "Options:"
    echo "  --remove-mispairs: for F3/F5 interleaved fastq, remove"
    echo "      any singleton reads from the final fastq"
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
export PATH=$PATH:$(dirname $0)/../share
#
# General shell functions
. bcftbx.functions.sh
#
# NGS-specific functions
. bcftbx.ngs_utils.sh
#
#===========================================================================
# Main script
#===========================================================================
#
# Set umask to allow group read-write on all new files etc
umask 0002
#
# Check for command line options
options=
do_gzip=
get_cmd_opts=yes
while [ ! -z "$get_cmd_opts" ] ; do
    case "$1" in
	--gzip)
	    do_gzip=yes
	    shift
	    ;;
	--remove-mispairs)
	    options="$options --remove-mispairs"
	    shift
	    ;;
	*)
	    # Assume end of command line options
	    get_cmd_opts=
	    ;;
    esac
done
#
# Get the input files
CSFASTA=$(abs_path $1)
QUAL=$(abs_path $2)
if [ ! -f "$CSFASTA" ] || [ ! -f "$QUAL" ] ; then
    echo "csfasta and/or qual files not found"
    exit
fi
#
# Paired end
if [ ! -z "$3" ] && [ ! -z "$4" ] ; then
    CSFASTA_F5=$(abs_path $3)
    QUAL_F5=$(abs_path $4)
    if [ ! -f "$CSFASTA_F5" ] || [ ! -f "$QUAL_F5" ] ; then
	echo "csfasta and/or qual files not found"
	exit
    fi
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
echo csfasta   : `basename $CSFASTA`
echo qual      : `basename $QUAL`
if [ ! -z "$CSFASTA_F5" ] || [ ! -z "$QUAL_F5" ] ; then
    echo csfasta f5: `basename $CSFASTA_F5`
    echo qual f5   : `basename $QUAL_F5`
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
# Run solid2fastq to make fastq file
solid2fastq_cmd="run_solid2fastq ${options} ${CSFASTA} ${QUAL} ${CSFASTA_F5} ${QUAL_F5}"
echo $solid2fastq_cmd
$solid2fastq_cmd
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
