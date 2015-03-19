#!/bin/sh
#
name=$(basename $0)
test_dir=$(mktemp --directory --tmpdir=. --suffix=.$name)
echo Running tests in $test_dir
cd $test_dir
for f in ../*sample3*.csfasta ../*sample3*.qual ; do
  ln -s $f
done
run_qc_pipeline.py --runner=simple solid_qc.sh --input=solid_paired_end .
qcreporter.py --platform=solid --verify .
retcode=$?
echo FINISHED: $retcode
exit $retcode
##
#
