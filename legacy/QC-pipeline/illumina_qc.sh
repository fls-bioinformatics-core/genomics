#!/bin/bash -e
#
# QC pipeline script for Illumina data
#
# Usage: illumina_qc.sh <fastq>
#
VERSION=1.3.3
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
    echo "  --subset N    number of reads to use in"
    echo "                fastq_screen (default N=100000,"
    echo "                N=0 to use all reads)"
    echo "  --no-screens  don't run fastq_screen"
    echo "  --qc_dir DIR  output QC to DIR (default 'qc')"
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
echo $@
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
do_fastq_screen=yes
threads=1
subset=100000
qc_dir=qc
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
        --subset)
            shift
	    subset=$2
	    ;;
	--threads)
	    shift
	    threads=$2
	    ;;
        --qc_dir)
            shift
	    qc_dir=$2
	    ;;
	--no-screens)
	    do_fastq_screen=no
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
echo run screens: $do_fastq_screen
echo ungzip fastq: $do_ungzip
echo threads   : $threads
echo fastq_screen subset: $subset
echo output dir: $qc_dir
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
# Check for required programs
echo "Checking for required programs:"
required="$FASTQC"
if [ $do_fastq_screen != "no" ] ; then
    required="$FASTQ_SCREEN $required"
fi
missing=
for prog in $required ; do
    echo -n "* ${prog}..."
    if [ -z "$(which $prog 2>/dev/null)" ] ; then
	echo "not found"
	missing="$missing $prog"
    else
	echo "ok"
    fi
done
if [ ! -z "$missing" ] ; then
    echo "ERROR required programs not found" >&2
    exit 1
fi
#
#############################################
# SET UP QC DIRECTORY
#############################################
#
# Create output directory
if [ ! -d "$qc_dir" ] ; then
    echo Making QC directory $qc_dir
    mkdir "$qc_dir"
fi
#
#############################################
# Report program paths and versions
#############################################
#
program_info=${qc_dir}/${fastq_base%%.fq}.$qc.programs
echo "# Program versions and paths used for $fastq_base:" > $program_info
for prog in $required ; do
    report_program_info $prog >> $program_info
done
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
if [ $do_fastq_screen == "yes" ] ; then
    run_fastq_screen --threads $threads --subset $subset --qc_dir $qc_dir $FASTQ
fi
#
# Run FASTQC
fastqc_base=${fastq_base%%.fq}_fastqc
if [ ! -d ${qc_dir}/${fastqc_base} ] || [ ! -f ${qc_dir}/${fastqc_base}.zip ] ; then
    fastqc_cmd="${FASTQC} --outdir $qc_dir --nogroup --extract --threads $threads"
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
    # Deal with non-standard .fq extension
    fastqc_out=${fastq_base}_fastqc
    if [ "$fastqc_out" != "$fastqc_base" ] ; then
	echo "Moving $fastqc_out to $fastqc_base..."
	/bin/mv $qc_dir/$fastqc_out $qc_dir/$fastqc_base
	/bin/mv $qc_dir/$fastqc_out.html $qc_dir/$fastqc_base.html
	/bin/mv $qc_dir/$fastqc_out.zip $qc_dir/$fastqc_base.zip
    fi
else
    echo "FastQC output already exists: $qc_dir/${fastqc_base}(.zip)"
fi
#
# Remove local temp
if [ -d $local_tmp ] ; then
    echo "Removing local tmp dir $local_tmp"
    /bin/rm -rf $local_tmp
fi
#
# Update permissions and group (if specified)
set_permissions_and_group "$SET_PERMISSIONS" "$SET_GROUP" $qc_dir
set_permissions_and_group "$SET_PERMISSIONS" "$SET_GROUP" "$program_info"
set_permissions_and_group -R "$SET_PERMISSIONS" "$SET_GROUP" "$qc_dir/${fastqc_base}*"
if [ $do_fastq_screen == "yes" ] ; then
    set_permissions_and_group "$SET_PERMISSIONS" "$SET_GROUP" "$qc_dir/$(get_fastq_basename $FASTQ)_*_screen.*"
fi
#
echo ILLUMINA QC pipeline completed: `date`
exit
##
#
