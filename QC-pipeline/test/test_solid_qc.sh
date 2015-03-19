#!/bin/sh
#
test_dir=$(mktemp --directory --tmpdir=. --suffix=.test_solid_qc)
echo Running tests in $test_dir
cd $test_dir
for f in ../*.csfasta ../*.qual ; do
  ln -s $f
done
run_qc_pipeline.py --runner=simple solid_qc.sh .
qcreporter.py --platform=solid --verify .
retcode=$?
echo FINISHED: $retcode
exit $retcode
##
#
