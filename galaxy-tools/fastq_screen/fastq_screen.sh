#!/bin/sh
#
# Wrapper script to run FastQScreen program as a Galaxy tool
#
# The wrapper is needed for two reasons:
#
# 1. To trap for fastq_screen writing to stderr (which otherwise makes
#    Galaxy think that the tool run has failed; and
# 2. To rename the auto-generated output file names to file names
#    chosen by Galaxy.
#
# usage: sh fastq_screen.sh <fastq_in> <screen_txt_out> <screen_png_out>
#
# Note that this wrapper assumes:
#
# 1. The version of fastq_screen supports --color and --multilib
#    options; and
# 2. The conf file specifies colorspace bowtie indexes.
#
echo FastQ Screen: check for contaminants
#
# Run fastq screen
# NB append stderr to stdout otherwise Galaxy job will fail
# (Could be mitigated by using --quiet option?)
# Direct output to a temporary file
log=`mktemp`
fastq_screen --color --multilib $1 > $log 2>&1
#
# Check exit code
if [ "$?" -ne "0" ] ; then
    echo FastQ Screen exited with non-zero status
    echo Output:
    echo cat $log
    # Clean up and exit
    /bin/rm -f $log
    exit $?
fi
#
# Outputs are <fastq_in>_screen.txt and <fastq_in>_screen.png
# check these exist and rename to supplied arguments
if [ -f "${1}_screen.txt" ] ; then
    /bin/mv ${1}_screen.txt $2
fi
if [ -f "${1}_screen.png" ] && [ "$3" != "" ] ; then
    /bin/mv ${1}_screen.png $3
fi
#
# Clean up
/bin/rm -f $log
#
# Done