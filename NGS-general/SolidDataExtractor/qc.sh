#!/bin/sh
#
# Script to run QC steps on SOLiD data
#
# Usage: qc.sh <csfasta> <qual>
#
# Set umask to allow group read-write on all new files etc
umask 0002
#
# Get the input files
csfasta=`basename $1`
qual=`basename $2`
#
# Get the data directory i.e. location of the input files
csfastadir=`dirname $1`
if [ "$csfastadir" == "." ] ; then
    csfastadir=`pwd`
fi
qualdir=`dirname $2`
if [ "$qualdir" == "." ] ; then
    qualdir=`pwd`
fi
datadir=$csfastadir
#
# Report
echo ========================================================
echo QC pipeline
echo ========================================================
echo Started   : `date`
echo Running in: `pwd`
echo data dir  : $datadir
echo csfasta   : $csfasta
echo qual      : $qual
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
: ${SOLID2FASTQ:=solid2fastq}
: ${QC_BOXPLOTTER:=colour_QC_script.sh}
#
# Check: both files should be in the same directory
if [ "$qualdir" != "$csfastadir" ] ; then
    echo ERROR csfasta and qual are in different directories
    exit 1
fi
#
# solid2fastq: create fastq file
#
# Determine basename for fastq file: same as csfasta, with
# any leading directory and extension stripped off
fastq_base=${csfasta%.*}
#
# Check if fastq file already exists
fastq=${fastq_base}.fastq
if [ -f "${fastq}" ] ; then
    echo Fastq file already exists, skipping solid2fastq
else
    echo "--------------------------------------------------------"
    echo Executing solid2fastq
    echo "--------------------------------------------------------"
    cmd="${SOLID2FASTQ} -o $fastq_base ${datadir}/${csfasta} ${datadir}/${qual}"
    echo $cmd
    $cmd
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
# QC_boxplotter
#
# Check if boxplot files already exist
if [ -f "${qual}_primer-order_boxplot.pdf" ] && [ -f "${qual}_seq-order_boxplot.pdf" ] ; then
    echo Boxplot pdfs already exist, skipping boxplotter
else
    echo "--------------------------------------------------------"
    echo Executing QC_boxplotter
    echo "--------------------------------------------------------"
    # Make a link to the input qual file
    if [ ! -f "${qual}" ] ; then
	echo Making symbolic link to qual file
	/bin/ln -s ${datadir}/${qual} ${qual}
    fi
    cmd="${QC_BOXPLOTTER} $qual"
    $cmd
    # Clean up
    if [ -L "${qual}" ] ; then
	echo Removing symbolic link to qual file
	/bin/rm -f ${qual}
    fi
fi
#
echo QC pipeline completed: `date`
exit
#
