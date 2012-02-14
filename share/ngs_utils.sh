#!/bin/sh
#
# ngs_utils.sh: library of shell functions for NGS
# Peter Briggs, University of Manchester 2011
#
# Set of shell functions to perform various NGS operations, e.g.
# generate fastq files from SOLiD data etc.
#
# To include in a shell script, do:
#
# . `dirname $0`/ngs_utils.sh
#
# if this file is in the same directory as the script, or
#
# . `dirname $0`/relative/path/to/ngs_utils.sh
#
# if it's elsewhere.
#
# NB This also requires the shell functions from functions.sh.
#
#====================================================================
#
# run_solid2fastq: create fastq file
#
# Provide names of csfasta and qual files (can include leading
# paths)
#
# Creates fastq file in current directory
#
# Usage: run_solid2fastq <csfasta> <qual> [ <output_basename> ]
function run_solid2fastq() {
    #
    # solid2fastq executable
    : ${SOLID2FASTQ:=solid2fastq}
    # Input files
    local csfasta=$(abs_path ${1})
    local qual=$(abs_path ${2})
    #
    local status=0
    #
    # Determine basename for fastq file: if not explicitly
    # specified then is same as csfasta (with leading directory
    # and extension stripped off)
    if [ ! -z $3 ] ; then
	local fastq_base=$3
    else
	local fastq_base=$(baserootname ${csfasta})
    fi
    #
    # Check if fastq file already exists
    local fastq=${fastq_base}.fastq
    if [ -f "${fastq}" ] ; then
	echo Fastq file already exists, skipping solid2fastq
    else
	echo "--------------------------------------------------------"
	echo Executing solid2fastq
	echo "--------------------------------------------------------"
	# Make a temporary directory to run in
	# This stops incomplete fastq files being written to the working
	# directory which might be left behind if solid2fastq stops (or
	# is stopped) prematurely
	local wd=`pwd`
	local tmp=$(make_temp -d --tmpdir=$wd --suffix=.solid2fastq)
	cd $tmp
	# Run solid2fastq
	local cmd="${SOLID2FASTQ} -o $fastq_base $csfasta $qual"
	echo $cmd
	$cmd
	# Termination status
	status=$?
	# Move back to working dir and copy preprocessed files
	cd $wd
	if [ -f "${tmp}/${fastq}" ] ; then
	    /bin/cp ${tmp}/${fastq} .
	    echo Created ${fastq}
	else
	    echo WARNING no file ${fastq}
	fi
	# Remove temporary dir
	/bin/rm -rf ${tmp}
    fi
    return $status
}
#
#====================================================================
#
# number_of_reads: count reads in csfasta file
#
# Usage: number_of_reads <csfasta>
function number_of_reads() {
    echo `grep -c "^>" $1`
}
#
#====================================================================
#
# solid_preprocess_files
#
# Returns csfasta and qual file pair, if found (otherwise returns
# empty string).
#
# Input is the basename of the input csfasta file (which can include
# a leading directory name).
#
# The function checks for a csfasta/qual file pair based on the input
# basename, using different variants of the naming convention used
# by the SOLiD_preprocess_filter_v2.pl script.
#
# Reports "<csfasta> <qual>", use 'cut -d" " -f...' to extract just
# the csfasta or qual name.
#
# Use 'if [ ! -z "$(solid_preprocess_files ...)" ] ; then' as a test
# on whether the files already exist.
#
# Usage: solid_preprocess_files <csfasta_basename>
function solid_preprocess_files() {
    # Old form of the output file names
    local csfasta=${1}_T_F3.csfasta
    local qual=${1}_QV_T_F3.qual
    if [ -f "$csfasta" ] && [ -f "$qual" ] ; then
	echo "$csfasta $qual"
	return
    fi
    # Newer form
    csfasta=${1}_T_F3.csfasta
    qual=${1}_T_F3_QV.qual
    if [ -f "$csfasta" ] && [ -f "$qual" ] ; then
	echo "$csfasta $qual"
	return
    fi
    # No matches
}
#
