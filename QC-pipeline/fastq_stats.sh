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
# Inputs
fastq_orig=$1
fastq_filt=$2
#
fastq_base=$(baserootname $1)
#
# Check original and filtered files exist
if [ ! -f "${fastq_orig}" ] ; then
    echo `basename $0`: ${fastq_orig}: not found
    exit 1
fi
if [ ! -f "${fastq_filt}" ] ; then
    echo `basename $0`: ${fastq_filt}: not found
    exit 1
fi
#
# Get numbers of reads (fastq line count divided by 4)
#n_reads_orig=$((`wc -l $fastq_orig | cut -f1 -d" "`/4))
n_reads_orig=$(count_reads $fastq_orig)
n_reads_filt=$(count_reads $fastq_filt)
#
# Get difference and percent diff
n_filtered=$(difference ${n_reads_orig} ${n_reads_filt})
percent_filtered=$(percent ${n_filtered} ${n_reads_orig})
#
echo "--------------------------------------------------------"
echo Comparing numbers of primary and filtered reads
echo "--------------------------------------------------------"
echo ${fastq_orig}$'\t'${n_reads_orig}
echo ${fastq_filt}$'\t'${n_reads_filt}
echo Number filtered$'\t'${n_filtered}
echo % filtered$'\t'${percent_filtered}
#
# Write to file
if [ ! -z "$stats_file" ] ; then
    wait_for_lock ${stats_file} 30
    if [ $? == 1 ] ; then
	echo Writing to ${stats_file}
	if [ ! -f ${stats_file} ] ; then
	    # Create new stats file and write header
	    echo "#File"$'\t'"Reads"$'\t'"Reads after filter"$'\t'"Difference"$'\t'"% Filtered" > ${stats_file}
	else
	    # Filter out existing entry if present
	    tmp_file=`mktemp`
	    grep -v "^${fastq_base}"$'\t' ${stats_file} > ${tmp_file}
	    /bin/mv -f ${tmp_file} ${stats_file}
	fi
	# Write to stats file
	echo ${fastq_base}$'\t'${n_reads_orig}$'\t'${n_reads_filt}$'\t'${n_filtered}$'\t'${percent_filtered} >> ${stats_file}
	# Sort into order
	sort -o ${stats_file} ${stats_file}
	# Release lock
	unlock_file ${stats_file}
    else
	echo Unable to get lock on ${stats_file}
    fi
fi
##
#