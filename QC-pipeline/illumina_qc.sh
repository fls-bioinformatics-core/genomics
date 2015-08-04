#!/bin/bash -e
#
# QC pipeline script for Illumina data
#
# Usage: illumina_qc.sh <fastq>
#
VERSION=1.2.2
#
function usage() {
    echo "Usage: $(basename $0) <fastq[.gz]> [options]"
    echo "       $(basename $0) --version"
    echo "       $(basename $0) --help|-h"
    echo ""
    echo "Run QC pipeline for Illumina data:"
    echo ""
    echo "* check for contamination using fastq_screen"
    echo "* generate QC metrics using FASTQC"
    echo "* create uncompressed copies of fastq file (if"
    echo "  input is fastq.gz and --ungzip-fastqs option"
    echo "  is specified)"
    echo ""
    echo "<fastq> can be either fastq or fastq.gz file"
    echo ""
    echo "Options:"
    echo "  -h,--help     print this help text and exit"
    echo "  --version     print version and exit"
    echo "  --ungzip-fastqs"
    echo "                create uncompressed versions of"
    echo "                fastq files, if gzipped copies"
    echo "                exist"
    echo "  --no-ungzip   don't create uncompressed fastqs"
    echo "                (ignored, this is the default)"
    echo "  --threads N   number of threads (i.e. cores)"
    echo "                available to the script (default"
    echo "                is N=1)"
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
# Generic command line options
#===========================================================================
#
if [ $# -lt 1 ] || [ "$1" == "-h" ] || [ "$1" == "--help" ] ; then
    usage
    exit
elif  [ "$1" == "--version" ] ; then
    echo $(basename $0) version $VERSION
    exit
fi
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
# Program version functions
import_functions bcftbx.versions.sh
#
#===========================================================================
# Main script
#===========================================================================
#
# Announce ourselves
echo ========================================================
echo ILLUMINA QC pipeline: version $VERSION
echo ========================================================
echo Started   : `date`
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
# Check for additional options
do_ungzip=no
threads=1
while [ ! -z "$2" ] ; do
    case "$2" in
	--no-ungzip)
	    if [ $do_ungzip == "yes" ] ; then
		echo "--no-ungzip: now the default (ignored)" >&2
	    else
		echo "ERROR cannot combine --no-ungzip and --ungzip-fastqs" >&2
		exit 1
	    fi
	    ;;
	--ungzip-fastqs)
	    do_ungzip=yes
	    ;;
	--threads)
	    shift
	    threads=$2
	    ;;
	*)
	    echo "Unrecognised option: $2"
	    exit 1
	    ;;
    esac
    shift
done
#
# Get the data directory i.e. location of the input file
datadir=`dirname $FASTQ`
#
# Set up environment
import_qc_settings
#
# Get the data directory i.e. location of the input file
datadir=`dirname $FASTQ`
#
# Base name for fastq files etc - strip leading path
# and trailing .fastq(.gz)
fastq_base=$(basename ${FASTQ%%.gz})
fastq_base=${fastq_base%%.fastq}
#
# Working directory
WORKING_DIR=`pwd`
#
# Local temp dir
local_tmp=$WORKING_DIR/tmp.$fastq_base
if [ ! -z "$JOB_ID" ] ; then
    local_tmp=$local_tmp.$JOB_ID
fi
if [ ! -d $local_tmp ] ; then
    mkdir $local_tmp
fi
export TEMP=$local_tmp
export TMP=$TEMP
export TMPDIR=$TEMP
export TMP_DIR=$TEMP
#
# Set the programs
# Override these defaults by setting them in qc.setup
: ${FASTQ_SCREEN:=fastq_screen}
: ${FASTQ_SCREEN_CONF_DIR:=}
: ${FASTQC:=fastqc}
#
# Explicitly set Java temp dir
if [ -z "$_JAVA_OPTIONS" ] ; then
    export _JAVA_OPTIONS=-Djava.io.tmpdir=$TEMP
fi
#
# Base name for script
qc=$(baserootname $0)
#
# Report settings
echo "--------------------------------------------------------"
echo Running in: $WORKING_DIR
echo data dir  : $datadir
echo fastq     : `basename $FASTQ`
echo fastq_screen: $FASTQ_SCREEN
echo fastq_screen conf files in: $FASTQ_SCREEN_CONF_DIR
echo fastqc    : $FASTQC
echo fastqc contaminants: $FASTQC_CONTAMINANTS_FILE
echo ungzip fastq: $do_ungzip
echo threads   : $threads
echo "--------------------------------------------------------"
echo hostname  : $HOSTNAME
echo job id    : $JOB_ID
echo TEMP      : $TMP
echo TMP       : $TMP
echo TMPDIR    : $TMPDIR
echo TMP_DIR   : $TMP_DIR
echo _JAVA_OPTIONS: $_JAVA_OPTIONS
echo "--------------------------------------------------------"
#
#############################################
# SET UP QC DIRECTORY
#############################################
#
# Create 'qc' subdirectory
if [ ! -d "qc" ] ; then
    echo Making qc subdirectory
    mkdir qc
fi
#
#############################################
# Report program paths and versions
#############################################
#
program_info=qc/$fastq_base.$qc.programs
echo "# Program versions and paths used for $fastq_base:" > $program_info
report_program_info $FASTQ_SCREEN >> $program_info
report_program_info $FASTQC >> $program_info
#
# Echo to log
cat $program_info
echo "--------------------------------------------------------"
#
#############################################
# FASTQ MANIPULATIONS
#############################################
#
# Unpack gzipped fastq file
ext=$(getextension $FASTQ)
if [ "$ext" == "gz" ] && [ "$do_ungzip" == "yes" ] ; then
    uncompressed_fastq=$(baserootname $FASTQ)
    if [ ! -f $uncompressed_fastq ] ; then
	echo Input FASTQ is gzipped, making ungzipped version
	gzip -dc $FASTQ > $uncompressed_fastq.part
	mv $uncompressed_fastq.part $uncompressed_fastq
    else
	echo Ungzipped version of input FASTQ found
    fi
fi
#
#############################################
# QC
#############################################
#
# Run fastq_screen
run_fastq_screen --threads $threads $FASTQ
#
# Run FASTQC
if [ ! -d qc/${fastq_base}_fastqc ] || [ ! -f qc/${fastq_base}_fastqc.zip ] ; then
    fastqc_cmd="${FASTQC} --outdir qc --nogroup --extract --threads $threads"
    if [ ! -z "$FASTQC_CONTAMINANTS_FILE" ] ; then
	# Nb avoid -c even though this should be valid it seems to
	# confuse fastqc
	fastqc_cmd="$fastqc_cmd --contaminants $FASTQC_CONTAMINANTS_FILE"
    fi
    echo "Running FastQC command: $fastqc_cmd"
    echo ${FASTQC} version $(get_version $FASTQC)
    ${fastqc_cmd} $FASTQ
    if [ $? -ne 0 ] ; then
	echo FASTQC failed >&2
    fi
else
    echo "FastQC output already exists: qc/${fastq_base}_fastqc(.zip)"
fi
#
# Update permissions and group (if specified)
set_permissions_and_group "$SET_PERMISSIONS" "$SET_GROUP"
#
# Remove local temp
if [ -d $local_tmp ] ; then
    echo "Removing local tmp dir $local_tmp"
    /bin/rm -rf $local_tmp
fi
#
echo ILLUMINA QC pipeline completed: `date`
exit
##
#
