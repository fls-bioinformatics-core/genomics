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
#====================================================================
#
# solid_preprocess_filter
#
# Run solid_preprocess_filter.sh script to perform quality filtering
# of original SOLiD data using polyclonal and error tests from the
# SOLiD_precess_filter_v2.pl program
#
# Usage: solid_preprocess_filter <csfasta> <qual>
function solid_preprocess_filter() {
    # Input file names
    csfasta=$1
    qual=$2
    # Run separate solid_preprocess_filter.sh script
    SOLID_PREPROCESS=`dirname $0`/solid_preprocess_filter.sh
    if [ -f "${SOLID_PREPROCESS}" ] ; then
	${SOLID_PREPROCESS} ${csfasta} ${qual}
    else
	echo ERROR ${SOLID_PREPROCESS} not found, preprocess/filter step skipped
    fi
}
#
#====================================================================
#
# qc_boxplotter
#
# Run FLS in-house boxplotter on SOLiD data
#
# Supply full path of input qual file
#
# Usage: qc_boxplotter <qual_file>
function qc_boxplotter() {
    # Input qual file
    qual=$(abs_path ${1})
    # Qual base name
    qual_base=`basename $qual`
    # Check if boxplot files already exist
    if [ -f "${qual_base}_seq-order_boxplot.pdf" ] ; then
	echo Boxplot pdf already exists for ${qual_base}, skipping boxplotter
    else
	echo "--------------------------------------------------------"
	echo Executing QC_boxplotter: ${qual_base}
	echo "--------------------------------------------------------"
	# Make a temporary directory to run in
	# This stops intermediate files cluttering the working directory
	# if the boxplotter stops (or is stopped) prematurely
	wd=`pwd`
	tmp=$(make_temp -d --tmpdir=$wd --suffix=.boxplotter)
	cd $tmp
	# Make a link to the input qual file
	if [ ! -f "${qual_base}" ] ; then
	    echo Making symbolic link to qual file
	    /bin/ln -s ${qual} ${qual_base}
	fi
	# Run boxplotter
	cmd="${QC_BOXPLOTTER} $qual_base"
	$cmd
	# Move back to working dir and copy output files
	cd $wd
	if [ -f "${tmp}/${qual_base}_seq-order_boxplot.ps" ] ; then
	    /bin/cp ${tmp}/${qual_base}_seq-order_boxplot.ps .
	    echo Created ${qual_base}_seq-order_boxplot.ps
	else
	    echo WARNING no file ${qual_base}_seq-order_boxplot.ps
	fi
	if [ -f "${tmp}/${qual_base}_seq-order_boxplot.pdf" ] ; then
	    /bin/cp ${tmp}/${qual_base}_seq-order_boxplot.pdf .
	    echo Created ${qual_base}_seq-order_boxplot.pdf
	else
	    echo WARNING no file ${qual_base}_seq-order_boxplot.pdf
	fi
	if [ -f "${tmp}/${qual_base}_seq-order_boxplot.png" ] ; then
	    /bin/cp ${tmp}/${qual_base}_seq-order_boxplot.png .
	    echo Created ${qual_base}_seq-order_boxplot.png
	else
	    echo WARNING no file ${qual_base}_seq-order_boxplot.png
	fi
	# Remove temporary dir
	/bin/rm -rf ${tmp}
    fi
}
#
