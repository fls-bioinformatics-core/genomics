#!/bin/sh
#
# fastq_stats.sh: calculate stats for preprocess filtering etc for FASTQ files
#
# Usage: fastq_stats.sh [ -f <stats_file> ] <fastq.all> <fastq.filtered>
#
# Counts number of reads in original csfasta and processed csfasta files,
# and reports numbers plus the difference (= number filtered) and percentage
# filtered.
#
# Appends a tab-delimited line with this information to the
# specified <stats_file>
#
# Import function libraries
if [ -f functions.sh ] ; then
    # Import local copies
    . functions.sh
    . lock.sh
else
    # Import versions in share
    . `dirname $0`/../share/functions.sh
    . `dirname $0`/../share/lock.sh
fi
#
# Local functions
#
# difference(): difference between two numbers
function difference() {
    echo "scale=10; $1 - $2" | bc -l
}
#
# percent(): express one number as percentage of another
function percent() {
    echo "scale=10; ${1}/${2}*100" | bc -l | cut -c1-5
}
#
# count_reads(): get number of reads from fastq file
function count_reads() {
    echo $((`wc -l $1 | cut -f1 -d" "`/4))
}
#
# get_stats(): generate stats line for a pair of files
function get_stats_line() {
    # Get numbers of reads (fastq line count divided by 4)
    n_reads_filt=$(count_reads $1)
    n_filtered=$(difference ${n_reads_orig} ${n_reads_filt})
    percent_filtered=$(percent ${n_filtered} ${n_reads_orig})
    echo "${n_reads_filt} ${n_filtered} ${percent_filtered}"
}
#
# Main script
#
# Set umask to allow group read-write on all new files etc
umask 0002
#
# Stats file
if [ "$1" == "-f" ] ; then
    stats_file=$2
    shift; shift
fi
#
# Reference file
ref_fastq=$1
if [ ! -f "${ref_fastq}" ] ; then
    echo `basename $0`: reference fastq ${ref_fastq} not found
    exit 1
fi
# Base name
fastq_base=$(baserootname $ref_fastq)
# Get numbers of reads for reference
n_reads_orig=$(count_reads $1)
header="#File Reads"
line="${fastq_base} ${n_reads_orig}"
#
# Loop over remaining arguments and generate stats against
# reference
while [ ! -z "$2" ] ; do
    fastq=$2
    if [ ! -f "${fastq}" ] ; then
	echo `basename $0`: ${fastq}: not found
    else
	header="${header} Reads_(filtered) Diff %_Filtered"
	line="${line} $(get_stats_line $fastq)"
    fi
    shift
done
#
# Output
if [ -z "$stats_file" ] ; then
    # Send to stdout
    echo $line
else
    # Write to stats file
    if [ ! -z "$stats_file" ] ; then
	wait_for_lock ${stats_file} 30
	if [ $? == 1 ] ; then
	    echo Writing to ${stats_file}
	    if [ ! -f ${stats_file} ] ; then
		# Create new stats file and write header
		echo $header | sed 's/ /\t/g' | sed 's/_/ /g' >>  ${stats_file}
	    else
		# Filter out existing entry if present
		tmp_file=`mktemp`
		grep -v "^${fastq_base}"$'\t' ${stats_file} > ${tmp_file}
		/bin/mv -f ${tmp_file} ${stats_file}
	    fi
	    # Write stats line
	    echo $line | sed 's/ /\t/g' >> ${stats_file}
	    # Sort into order
	    sort -o ${stats_file} ${stats_file}
	    # Release lock
	    unlock_file ${stats_file}
	else
	    echo Unable to get lock on ${stats_file}
	fi
    fi
fi
##
#