#!/bin/bash
#
name=$(basename ${0%.*})
test_dir=$(mktemp --directory --tmpdir=. --suffix=.$name)
echo Running tests in $test_dir
cd $test_dir
ln -s ../illumina_sample1_R1.fastq.gz
uncompress_fastqgz.sh illumina_sample1_R1.fastq.gz
retcode=$?
echo FINISHED: $retcode
exit $retcode
##
#
