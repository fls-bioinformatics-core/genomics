#!/bin/sh
#
name=$(basename ${0%.*})
test_dir=$(mktemp --directory --tmpdir=. --suffix=.$name)
data_dir=$(pushd $(dirname $0) >/dev/null; pwd; popd >/dev/null)
data_files=\
"illumina_sample1_R1.fastq.gz \
illumina_sample1_R2.fastq.gz"
echo Running tests in $test_dir
cd $test_dir
for f in $data_files ; do
  ln -s $data_dir/$f
done
mkdir qc
run_qc_pipeline.py --input=fastqgz --runner=simple illumina_qc.sh .
qcreporter.py --format=fastqgz --platform=illumina --verify .
retcode=$?
echo FINISHED: $retcode
exit $retcode
##
#
