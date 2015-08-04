#!/bin/bash
#
# do.sh
#
# Utility to run a command multiple times with an incrementing index
# and "templated input"
#
usage="do.sh <start> <end> <templated_command...>"
#
# <start> and <end> specify integer start and end indices; the
# script executes <templated_command> for each index from <start> to
# <end>, replacing any hash symbols in <templated_command> with the
# current index value.
#
# Example:
#
# do.sh 1 43 ln -s /blah/blah#/myfile#.ext ./myfile#.ext
#
# will execute:
#
# ln -s /blah/blah1/myfile1.ext ./myfile1.ext
# ln -s /blah/blah2/myfile2.ext ./myfile2.ext
# ...
# ln -s /blah/blah43/myfile43.ext ./myfile43.ext
#
# Initialisations
#
# Start and end indices
start=$1
shift
end=$1
shift
#
# Loop over remaining argments to extract command
cmd=""
while [ "$1" != "" ] ; do
    if [ "$cmd" == "" ] ; then
	cmd=$1
    else
	cmd="$cmd $1"
    fi
    shift
done
#
if [ "$start" == "" ] || [ "$end" == "" ] ; then
    echo Missing start and/or end values
    echo Usage: $usage
    exit 1
fi
#
if [ "$cmd" == "" ] ; then
    echo No command supplied, nothing to do
    echo Usage: $usage
    exit 1
fi
echo Iterating command: \"$cmd\"
echo Substituting hashes with indices from $start to $end
#
# Loop from start to end and echo command with template substitutions
for i in `seq $start $end` ; do
    cmd_i=${cmd//#/$i}
    echo Running \"$cmd_i\"
    $cmd_i
done
