#!/bin/bash
#
# Script to run fastq_screen QC steps on NGS data
#
# Usage: fastq_screen.sh [options] <fastq>
#
function usage() {
    echo "Usage: fastq_screen.sh [options] <fastq_file>"
    echo ""
    echo "Run fastq_screen against model organisms, other organisms and rRNA"
    echo "Note that a gzipped <fastq_file> is also valid as input"
    echo ""
    echo "Output is written to the subdirectory 'qc' of the current directory"
    echo "(will be created if not found)"
    echo ""
    echo "Options:"
    echo "  --subset N: use subset of N reads (default 1000000, 0=use all reads)"
    echo "  --color: use colorspace bowtie indexes (SOLiD data)"
    echo "  --threads N: use N threads to run fastq_screen (default is 1)"
}
# Check command line
if [ $# -eq 0 ] || [ "$1" == "-h" ] || [ "$1" == "--help" ] ; then
    usage
    exit
fi
# Collect options
options=
color=
threads=1
subset=1000000
while [ $# -gt 1 ] ; do
    case "$1" in
	--subset)
	    shift
	    subset=$1
	    ;;
	--color)
	    color=yes
	    options="$options --color"
	    ;;
	--threads)
	    shift
	    threads=$1
	    ;;
	*)
	    echo Unrecognised option: $1 >&2
	    exit 1
	    ;;
    esac
    shift
done
#
# Set umask to allow group read-write on all new files etc
umask 0002
#
# Get the input file
fastq=`basename $1`
#
# Strip "fastq(.gz)" extension
fastq_base=${fastq%.gz}
fastq_base=${fastq_base%.fastq}
#
# Get the data directory i.e. location of the input file
datadir=`dirname $1`
if [ "$datadir" == "." ] ; then
    datadir=`pwd`
fi
#
# Set up environment
export PATH=$(dirname $0)/../share:${PATH}
. bcftbx.functions.sh
. bcftbx.ngs_utils.sh
. bcftbx.versions.sh
import_qc_settings
#
# Set the programs
# Override these defaults by setting them in qc.setup
: ${FASTQ_SCREEN:=fastq_screen}
: ${FASTQ_SCREEN_CONF_DIR:=}
#
# fastq_screen options
FASTQ_SCREEN_OPTIONS="$options --threads $threads"
#
# Subset options
FASTQ_SCREEN_VERSION=$(get_version fastq_screen)
MAJOR_VERSION=$(get_version fastq_screen | cut -d. -f1)
MINOR_VERSION=$(get_version fastq_screen | cut -d. -f2)
PATCH_VERSION=$(get_version fastq_screen | cut -d. -f3)
if [ -z "$subset" ] || [ "$subset" == "0" ] ; then
    # Handle no subset i.e. use all data
    if [ $MAJOR_VERSION == "v0" ] ; then
	case "$MINOR_VERSION" in
	    [0-4])
		subset_option=
		;;
	    [5-7])
		case "$PATCH_VERSION" in
		    [0-2])
			echo "ERROR --subset 0 broken for fastq_screen $FASTQ_SCREEN_VERSION; switch to 0.6.3 or later" >&2
			exit 1
			;;
		esac
		subset_option="--subset 0"
		;;
	    *)
		echo "ERROR don't know how to set subset for fastq_screen $MAJOR_VERSION.$MINOR_VERSION.*" >&2
		exit 1
		;;
	esac
    fi
else
    # Subset explicitly specified
    subset_option="--subset $subset"
fi
FASTQ_SCREEN_OPTIONS="$FASTQ_SCREEN_OPTIONS $subset_option"
#
# Extension for conf file based on index type
if [ -z "$color" ] ; then
    # Letterspace indexes
    conf_ext=${FASTQ_SCREEN_CONF_NT_EXT}
else
    # Colorspace indexes
    conf_ext=${FASTQ_SCREEN_CONF_CS_EXT}
fi
#
# Report
echo ========================================================
echo fastq_screen pipeline
echo ========================================================
echo Started   : `date`
echo Running in: `pwd`
echo data dir  : $datadir
echo fastq     : $fastq
echo fastq_screen: $FASTQ_SCREEN
echo Version   : $FASTQ_SCREEN_VERSION
echo Location of conf files: $FASTQ_SCREEN_CONF_DIR
echo Colorspace: $color
echo Threads   : $threads
echo Subset    : $subset
#
# Check that fastq file exists
if [ ! -f "${datadir}/${fastq}" ] ; then
    echo ERROR fastq file not found: ${datadir}/${fastq}, stopping
    exit 1
fi
#
# Create 'qc' subdirectory
if [ ! -d "qc" ] ; then
    mkdir qc
fi
cd qc
#
# fastq_screen
#
# Run multiple screens:
# - Model organisms
# - Other organisms
# - rRNA
#
SCREENS="model_organisms other_organisms rRNA"
#
for screen in $SCREENS ; do
    # Check if screen files already exist
    screen_base=${fastq_base}_${screen}_screen
    if [ -f "${screen_base}.txt" ] && [ -f "${screen_base}.png" ] ; then
	echo Screen files already exist for ${screen}, skipping fastq_screen
    else
	echo "--------------------------------------------------------"
	echo Executing fastq_screen for ${screen}
	echo "--------------------------------------------------------"
	fastq_screen_conf=${FASTQ_SCREEN_CONF_DIR}/fastq_screen_${screen}${conf_ext}.conf
	if [ ! -f $fastq_screen_conf ] ; then
	    # Conf file not found
	    echo WARNING conf file $fastq_screen_conf not found, skipped
	else
	    # Names for output files
	    case "$MAJOR_VERSION.$MINOR_VERSION" in
		v0.4)
		    fastq_screen_txt=${fastq%.fastq}_screen.txt
		    fastq_screen_png=${fastq%.fastq}_screen.png
		    ;;
		v0.[5-6])
		    fastq_screen_txt=${fastq_base}_screen.txt
		    fastq_screen_png=${fastq_base}_screen.png
		    ;;
		*)
		    echo WARNING cannot handle output from fastq_screen $FASTQ_SCREEN_VERSION
		    exit 1
		    ;;
	    esac
	    # Check for and remove exisiting outputs
	    if [ -f "${fastq_screen_txt}" ] ; then
		echo "Removing old ${fastq_screen_txt}"
		/bin/rm ${fastq_screen_txt}
	    fi
	    if [ -f "${fastq_screen_png}" ] ; then
		echo "Removing old ${fastq_screen_png}"
		/bin/rm ${fastq_screen_png}
	    fi
	    if [ -f "${screen_base}.txt" ] ; then
		echo "Removing old ${screen_base}.txt"
		/bin/rm ${screen_base}.txt
	    fi
	    if [ -f "${screen_base}.png" ] ; then
		echo "Removing old ${screen_base}.png"
		/bin/rm ${screen_base}.png
	    fi
	    # Run the screen
	    cmd="${FASTQ_SCREEN} ${FASTQ_SCREEN_OPTIONS} --outdir . --conf ${fastq_screen_conf} ${datadir}/${fastq}"
	    echo $cmd
	    $cmd
	    # Move the screen files
	    if [ -f "${fastq_screen_txt}" ] ; then
		/bin/mv ${fastq_screen_txt} ${screen_base}.txt
		echo Output .txt: ${screen_base}.txt
	    else
		echo WARNING failed to generate ${screen_base}.txt
	    fi
	    if [ -f "${fastq_screen_png}" ] ; then
		/bin/mv ${fastq_screen_png} ${screen_base}.png
		echo Output .png: ${screen_base}.png
	    else
		echo WARNING failed to generate ${screen_base}.png
	    fi
	fi
	# End of screen
    fi
done
#
echo fastq_screen pipeline completed: `date`
exit
#
