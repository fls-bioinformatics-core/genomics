#!/bin/sh
#
# Script to run fastq_screen QC steps on SOLiD data
#
# Usage: fastq_screen.sh <fastq>
#
# Set umask to allow group read-write on all new files etc
umask 0002
#
# Get the input file
fastq=`basename $1`
#
# Strip extension
fastq_base=${fastq%.*}
#
# Get the data directory i.e. location of the input files
datadir=`dirname $1`
if [ "$datadir" == "." ] ; then
    datadir=`pwd`
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
# Check that fastq file exists
if [ ! -f "${datadir}/${fastq}" ] ; then
    echo ERROR fastq file not found: ${datadir}/${fastq}, stopping
    exit 1
fi
#
# Set the programs
# Override these defaults by setting them in qc.setup
: ${FASTQ_SCREEN:=fastq_screen}
: ${FASTQ_SCREEN_CONF_DIR:=}
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
	fastq_screen_conf=${FASTQ_SCREEN_CONF_DIR}/fastq_screen_${screen}.conf
	if [ ! -f $fastq_screen_conf ] ; then
	    # Conf file not found
	    echo WARNING conf file $fastq_screen_conf not found, skipped
	else
	    # Run the screen
	    cmd="${FASTQ_SCREEN} --color --subset 1000000 --outdir . --conf ${fastq_screen_conf} ${datadir}/${fastq}"
	    echo $cmd
	    $cmd
	    # Move the screen files
	    if [ -f "${fastq_base}_screen.txt" ] ; then
		/bin/mv ${fastq_base}_screen.txt ${screen_base}.txt
		echo Output .txt: ${screen_base}.txt
	    else
		echo WARNING failed to generate ${screen_base}.txt
	    fi
	    if [ -f "${fastq_base}_screen.png" ] ; then
		/bin/mv ${fastq_base}_screen.png ${screen_base}.png
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
