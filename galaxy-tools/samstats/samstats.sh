#!/bin/sh
#
# usage: sh samstats.sh [-j <jar_file>] <sam_in> <report_txt_out>
#
echo SamStats: count uniquely mapped reads in SAM file
#
# Process command line arguments
# There's only one (-j) to specify the Jar file
JAR_FILE=SamStats.jar
if [ "$1" == "-j" ] ; then
    shift
    JAR_FILE=$1
    shift
fi
#
# Run SamStats
java -cp ${JAR_FILE} SamStats $1
#
# Output is a text file: SamStats_maponly_<sam_in>.stats
# Check it exists and rename to supplied argument
sam_in=`basename $1`
if [ -f "SamStats_maponly_${sam_in}.stats" ] ; then
    echo Move SamStats_maponly_${sam_in}.stats to $2
    /bin/mv SamStats_maponly_${sam_in}.stats $2
else
    echo Can\'t find SamStats_maponly_${sam_in}.stats
    exit 1
fi
#
# Done
