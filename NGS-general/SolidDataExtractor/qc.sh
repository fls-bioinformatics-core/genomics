#!/bin/sh
#
# Script to run QC steps on SOLiD data
#
# solid2fastq: create fastq file
echo Executing solid2fastq
echo $cwd
echo $1
echo $2
fastq=${1%.*}
cmd="solid2fastq -o $fastq $1 $2"
echo $cmd
$cmd
#
# fastq_screen
#
# QC_boxplotter
