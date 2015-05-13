#!/bin/sh
#
# Run set of test scripts and report success or failure
#
# Setup
script_dir=$(pushd $(dirname $0) >/dev/null; pwd; popd >/dev/null)
echo Running test scripts from $script_dir
test_dir=$(mktemp --directory --tmpdir=. --suffix=.$(basename $0))
cd $test_dir
# Run scripts
echo Running tests in $(pwd)
tested=0
failed=0
for script in \
	test_solid_qc.sh \
	test_solid_qc.paired.sh \
	test_illumina_qc.sh ; do
  echo -n $script...
  tested=$((tested + 1))
  log=${script%.*}.log
  $script_dir/$script >$log 2>&1
  status=$?
  if [ $status -ne 0 ] ; then
    # Report failure and capture tail of log file
    echo FAIL
    cat >>error_report.log <<EOF
=======================================================
FAIL: $script
-------------------------------------------------------
Tail from captured output:
EOF
    tail $log >>error_report.log
    cat >>error_report.log <<EOF
-------------------------------------------------------
EOF
    failed=$((failed + 1))
  else
    echo ok
  fi
done
# Finished running scripts
if [ $failed -gt 0 ] ; then
  echo $failed failures:
  cat error_report.log
  status=1
else
  status=0
fi
echo Ran $tested tests
echo 
if [ $status -eq 0 ] ; then
  echo OK
else
  echo "FAILED (failures=$failed)"
fi
# Clean up
rm -rf tmp.* *.log
cd ..
rmdir $test_dir
# Finish
exit $status
##
#	
