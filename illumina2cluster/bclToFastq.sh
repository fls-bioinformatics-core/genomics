#!/bin/sh
#
# Bcl to Fastq conversion wrapper script
#
# Usage: bclToFastq.sh <illumina_run_dir> <output_dir>
#
# Runs configureBclToFastq.pl from CASAVA to set up conversion scripts,
# then runs make to perform the actual conversion
#
# Check arguments
if [ $# -lt 2 ] ; then
    echo "Usage: `basename $0` <illumina_run_dir> <output_dir>"
    exit 1
fi
#
# Input parameters
illumina_run_dir=$1
fastq_output_dir=$2
#
basecalls_dir=${illumina_run_dir}/Data/Intensities/BaseCalls
n_mismatches=0
force=
#
echo Illumina run directory: $illumina_run_dir
echo BaseCalls directory   : $basecalls_dir
echo Fastq output directory: $fastq_output_dir
echo Number of mismatches  : $n_mismatches
#
# Check input directory
if [ ! -d "$illumina_run_dir" ] ; then
    echo ERROR no directory $illumina_run_dir
    exit 1
elif [ ! -d "$basecalls_dir" ] ; then
    echo ERROR no BaseCalls directory $basecalls_dir
    exit 1
fi
#
# Check output directory
if [ -d "$fastq_output_dir" ] ; then
    echo WARNING output dir $fastq_output_dir exists
    echo Using --force option of configureBclToFastq.pl
    force=--force
fi
#
# Locate configureBclToFastq.pl script
configureBclToFastq=`which configureBclToFastq.pl 2>&1`
got_bcl_converter=`echo $configureBclToFastq | grep "no configureBclToFastq.pl"`
if [ ! -z "$got_bcl_converter" ] ; then
    echo ERROR configureBclToFastq.pl not found
    exit 1
fi
#
# Run configureBclToFastq
echo Running configureBclToFastq
configureBclToFastq.pl \
    --input-dir $basecalls_dir \
    --output-dir $fastq_output_dir \
    --mismatches $n_mismatches \
    --fastq-cluster-count -1 \
    $force
#
# Check output
if [ ! -d "$fastq_output_dir" ] ; then
    echo ERROR no output directory $fastq_output_dir found
    exit 1
fi
cd $fastq_output_dir
if [ ! -f Makefile ] ; then
    echo ERROR no Makefile from configurebclToFastq.pl
    exit 1
fi
echo Running make
make
echo $0: finished
exit
##
#
