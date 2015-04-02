#!/bin/sh
#
name=$(basename ${0%.*})
test_dir=$(mktemp --directory --tmpdir=. --suffix=.$name)
data_files=\
"solid_sample3_F3.csfasta \
solid_sample3_F3_QV.qual \
solid_sample3_F5-BC.csfasta \
solid_sample3_F5-BC_QV.qual"
echo Running tests in $test_dir
cd $test_dir
for f in $data_files ; do
  ln -s ../$f
done
run_qc_pipeline.py --runner=simple solid_qc.sh --input=solid_paired_end .
qcreporter.py --platform=solid --format=solid_paired_end --verify .
retcode=$?
echo FINISHED: $retcode
exit $retcode
##
#
