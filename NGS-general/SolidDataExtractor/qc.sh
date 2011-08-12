#!/bin/sh
#
# Script to run QC steps on SOLiD data
#
# Usage: qc.sh <csfasta> <qual>
#
# Get the input files
#
# NB need to take care: we assume that the files are in the
# current directory
# This is important as fastq_screen and boxplotter write their
# output to the same directory as the input file (regardless of
# current working directory)
csfasta=$1
qual=$2
#
# Report
echo QC pipeline
echo Running in: `pwd`
echo csfasta   : $csfasta
echo qual      : $qual
#
# solid2fastq: create fastq file
#
# Determine basename for fastq file: same as csfasta, with
# leading directory and extension stripped off
fastq_base=`basename $csfasta` 
fastq_base=${fastq_base%.*}
#
# Check if fastq file already exists
fastq=${fastq_base}.fastq
if [ -f "${fastq}" ] ; then
    echo Fastq file already exists, skipping solid2fastq
else
    echo Executing solid2fastq
    cmd="solid2fastq -o $fastq_base $csfasta $qual"
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
# Check if screen files already exist
if [ -f "${fastq_base}_screen.txt" ] && [ -f "${fastq_base}_screen.png" ] ; then
    echo Screen files already exist, skipping fastq_screen
else
    # Make a link to the input fastq file
    if [ ! -f "${fastq}" ] ; then
	echo Making symbolic link to fastq file
	/bin/ln -s ../${fastq} ${fastq}
    fi
    echo Executing fastq_screen
    fastq_screen --color --subset 1000000 ${fastq}
    # Clean up
    if [ -L "${fastq}" ] ; then
	echo Removing symbolic link to fastq file
	/bin/rm -f ${fastq}
    fi
fi
#
# QC_boxplotter
#
# Check if boxplot files already exist
if [ -f "${qual}_primer-order_boxplot.pdf" ] && [ -f "${qual}_seq-order_boxplot.pdf" ] ; then
    echo Boxplot pdfs already exist, skipping boxplotter
else
    # Make a link to the input qual file
    if [ ! -f "${qual}" ] ; then
	echo Making symbolic link to qual file
	/bin/ln -s ../${qual} ${qual}
    fi
    echo Executing QC_boxplotter
    colour_QC_script.sh $qual
    # Clean up
    if [ -L "${qual}" ] ; then
	echo Removing symbolic link to qual file
	/bin/rm -f ${qual}
    fi
fi
#
