#!/bin/sh
#
name=$(basename ${0%.*})
test_dir=$(mktemp --directory --tmpdir=. --suffix=.$name)
data_dir=$(pushd $(dirname $0) >/dev/null; pwd; popd >/dev/null)
data_files=\
"solid_sample3_F3.csfasta \
solid_sample3_F3_QV.qual \
solid_sample3_F5.csfasta \
solid_sample3_F5_QV.qual"
echo Running tests in $test_dir
cd $test_dir
for f in $data_files ; do
  ln -s $data_dir/$f
done
mkdir qc
run_qc_pipeline.py --runner=simple solid_qc.sh --input=solid_paired_end .
qcreporter.py --platform=solid --format=solid_paired_end --verify .
retcode=$?
echo FINISHED: $retcode
exit $retcode
##
#
