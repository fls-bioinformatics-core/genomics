#!/bin/bash -e
#
# Run test of md5checker.py
if [ ! -d output ] ; then
  mkdir output
fi
md5checker.py -h
md5checker.py --version
md5checker.py -d $(dirname $0)/data/file1.txt $(dirname $0)/data/file2.txt
md5checker.py -d $(dirname $0)/data/dir1 $(dirname $0)/data/dir2
md5checker.py -o output/checksums.dir1 $(dirname $0)/data/dir1
md5checker.py -o output/checksums.file1 $(dirname $0)/data/file1.txt
pushd $(dirname $0); md5checker.py -c data/checksum.txt; popd
##
#
