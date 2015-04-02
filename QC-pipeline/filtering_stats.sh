#!/bin/sh
#
# filtering_stats.sh: calculate stats for preprocess filtering
#
# Usage: filtering_stats.sh <original_csfasta> <processed_csfasta> <stats_file>
#
# Counts number of reads in original csfasta and processed csfasta files,
# and reports numbers plus the difference (= number filtered) and percentage
# filtered.
#
# Appends a tab-delimited line with this information to the
# specified <stats_file>
#
# Import function libraries
export PATH=$PATH:$(dirname $0)/../share
function import_functions() {
    if [ -z "$1" ] ; then
	echo ERROR no filename supplied to import_functions >2
    else
	echo Sourcing $1
	. $1
	if [ $? -ne 0 ] ; then
	    echo ERROR failed to import $1 >2
	fi
    fi
}
import_functions bcftbx.functions.sh
import_functions bcftbx.lock.sh
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
# Main script
#
# Set umask to allow group read-write on all new files etc
umask 0002
#
# Inputs
csfasta=$1
filtered_csfasta=$2
stats_file=$3
#
base_csfasta=$(baserootname $1)
#
# Check original and filtered files exist
if [ ! -f "${csfasta}" ] ; then
    echo `basename $0`: ${csfasta}: not found
    exit 1
fi
if [ ! -f "${filtered_csfasta}" ] ; then
    echo `basename $0`: ${filtered_csfasta}: not found
    exit 1
fi
#
# Get numbers of reads
n_reads_primary=`grep -c "^>" ${csfasta}`
n_reads_filter=`grep -c "^>" ${filtered_csfasta}`
#
# Get stats
n_filtered=$(difference ${n_reads_primary} ${n_reads_filter})
percent_filtered=$(percent ${n_filtered} ${n_reads_primary})
#
echo "--------------------------------------------------------"
echo Comparing numbers of primary and filtered reads
echo "--------------------------------------------------------"
echo ${csfasta}$'\t'${n_reads_primary}
echo ${filtered_csfasta}$'\t'${n_reads_filter}
echo Number filtered$'\t'${n_filtered}
echo % filtered$'\t'${percent_filtered}
#
# Write to file
wait_for_lock ${stats_file} 30
if [ $? == 1 ] ; then
    echo Writing to ${stats_file}
    if [ ! -f ${stats_file} ] ; then
	# Create new stats file and write header
	echo "#File"$'\t'"Reads"$'\t'"Reads after filter"$'\t'"Difference"$'\t'"% Filtered" > ${stats_file}
    else
	# Filter out existing entry if present
	tmp_file=`mktemp`
	grep -v "^${base_csfasta}"$'\t' ${stats_file} > ${tmp_file}
	/bin/mv -f ${tmp_file} ${stats_file}
	# Explicitly set permissions (as the temp file has restricted
	# permissions)
	chmod ug+rw ${stats_file}
    fi
    # Write to stats file
    echo ${base_csfasta}$'\t'${n_reads_primary}$'\t'${n_reads_filter}$'\t'${n_filtered}$'\t'${percent_filtered} >> ${stats_file}
    # Sort into order
    sort -o ${stats_file} ${stats_file}
    # Release lock
    unlock_file ${stats_file}
else
    echo Unable to get lock on ${stats_file}
fi
##
#
