#!/bin/sh
#
name=$(basename ${0%.*})
test_dir=$(mktemp --directory --tmpdir=. --suffix=.$name)
data_files=\
"solid_F3_sample1.csfasta \
solid_F3_QV_sample1.qual \
solid_F3_sample2.csfasta \
solid_F3_QV_sample2.qual"
echo Running tests in $test_dir
cd $test_dir
for f in $data_files ; do
  ln -s ../$f
done
run_qc_pipeline.py --runner=simple solid_qc.sh .
qcreporter.py --platform=solid --verify .
retcode=$?
echo FINISHED: $retcode
exit $retcode
##
#
