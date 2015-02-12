#!/bin/sh
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
    echo "Options:"
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
while [ $# -gt 1 ] ; do
    case "$1" in
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
#
# fastq_screen options
FASTQ_SCREEN_OPTIONS="$options --subset 1000000 --threads $threads"
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
echo Location of conf files: $FASTQ_SCREEN_CONF_DIR
echo Colorspace: $color
echo Threads   : $threads
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
	    fastq_screen_txt=${fastq%.fastq}_screen.txt
	    fastq_screen_png=${fastq%.fastq}_screen.png
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
