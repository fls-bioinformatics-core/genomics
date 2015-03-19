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
# Provide names of csfasta and qual files (can include leading paths)
# If a second pair of csfasta/qual files is supplied then an "interleaved"
# fastq file will be generated.
#
# Creates fastq file in current directory
#
# Specify --remove-mispairs to perform removal of singleton reads if
# combining multiple csffasta/qual pairs into a single fastq file (i.e.
# paired end data)
#
# Specify --separate-pairs to split the combined F3 and F5 pairs back
# out to separate files for paired end data - in this case there will
# be an additional pair of output files ".F3" (F3 reads only) and
# ".F5" (F5 reads only)
#
# Usage: run_solid2fastq [ --remove-mispairs ] [ --separate-pairs ]
#        <csfasta> <qual> [ <csfasta_f5> <qual5> ]
#        [ <output_basename> ]
function run_solid2fastq() {
    #
    # solid2fastq executable
    : ${SOLID2FASTQ:=solid2fastq}
    # Check for options
    get_options=yes
    remove_mispairs=no
    separate_pairs=no
    while [ ! -z "$get_options" ] ; do
	case $1 in
	    --remove-mispairs)
		remove_mispairs=yes; shift
		;;
	    --separate-pairs)
		separate_pairs=yes; shift
		;;
	    *)
		get_options=
		;;
	esac
    done
    # Input files
    local csfasta=$(abs_path ${1})
    local qual=$(abs_path ${2})
    if [ $# -ge 4 ] ; then
	local csfasta="${csfasta} $(abs_path ${3})"
	local qual="${qual} $(abs_path ${4})"
    fi
    #
    local status=0
    #
    # Determine basename for fastq file: if not explicitly
    # specified then is same as csfasta (with leading directory
    # and extension stripped off)
    if [ $# -eq 3 ] ; then
	local fastq_base=$3
    elif [ $# -eq 5 ] ; then
	local fastq_base=$5
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
	# Remove mispairs
	if [ "$remove_mispairs" == yes ] ; then 
	    # Run the remove_mispairs script
	    fastq_in=`basename $fastq`
	    cmd="${REMOVE_MISPAIRS} $fastq_in"
	    echo $cmd
	    $cmd
	    # Overwrite the input file with the processed file
	    fastq_mispairs=`basename $fastq`.paired
	    if [ -f "${fastq_mispairs}" ] ; then
		/bin/cp ${fastq_mispairs} $fastq
		echo Created ${fastq_mispairs}
	    else
		echo WARNING no file ${fastq_mispairs}
	    fi
	fi
	# Separate pairs
	if [ "${separate_pairs}" == yes ] ; then
	    # Run the separate_paired_fastq script
	    cmd="${SEPARATE_PAIRED_FASTQ} $fastq"
	    echo $cmd
	    $cmd
	    # Check for outputs
	    fastq_f3=$(rootname $fastq).F3.fastq
	    if [ -f "${fastq}.F3" ] ; then
		/bin/mv ${fastq}.F3 $fastq_f3
	    else
		echo WARNING no file ${fastq}.F3
	    fi
	    fastq_f5=$(rootname $fastq).F5.fastq
	    if [ -f "${fastq}.F5" ] ; then
		/bin/mv ${fastq}.F5 $fastq_f5
	    else
		echo WARNING no file ${fastq}.F5
	    fi
	fi
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
	if [ "${separate_pairs}" == yes ] ; then
	    if [ -f "${tmp}/${fastq_f3}" ] && [ -f "${tmp}/${fastq_f5}" ] ; then
		/bin/cp ${tmp}/${fastq_f3} .
		echo Created ${fastq_f3}
		/bin/cp ${tmp}/${fastq_f5} .
		echo Created ${fastq_f5}
	    else
		echo WARNING missing one or both files ${fastq_f3}/${fastq_f5}
	    fi
	fi
	# Remove temporary dir
	/bin/rm -rf ${tmp}
    fi
    return $status
}
#
#====================================================================
#
# remove_mispairs: remove singleton reads from interleaved fastq file
#
# Usage: remove_mispairs <fastq>
function remove_mispairs() {
    fastq=$1
    echo "--------------------------------------------------------"
    echo Executing remove_mispairs
    echo "--------------------------------------------------------"
    # Make a temporary directory to run in
    local wd=`pwd`
    local tmp=$(make_temp -d --tmpdir=$wd --suffix=.solid2fastq)
    cd $tmp
    # Make link to input fastq file
    ln -s $(abs_path $fastq)
    fastq_in=`basename $1`
    # Run remove mispairs
    local cmd="${REMOVE_MISPAIRS} $fastq_in"
    echo $cmd
    $cmd
    # Termination status
    status=$?
    # Move back to working dir and deal with output
    cd $wd
    fastq_mispairs=`basename $1`.paired
    if [ -f "${tmp}/${fastq_mispairs}" ] ; then
	/bin/cp ${tmp}/${fastq_mispairs} .
	echo Created ${fastq_mispairs}
    else
	echo WARNING no file ${fastq_mispairs}
    fi
    # Remove temporary dir
    /bin/rm -rf ${tmp}
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
# Usage: solid_preprocess_filter [ options ] <csfasta> <qual>
function solid_preprocess_filter() {
    # Check for options to pass to the solid_preprocess_filter script
    local options=
    while [ $# -gt 2 ] ; do
	options="$options $1"
	shift
    done
    # Input file names
    local csfasta=$1
    local qual=$2
    # Run separate solid_preprocess_filter.sh script
    SOLID_PREPROCESS=`dirname $0`/solid_preprocess_filter.sh
    if [ -f "${SOLID_PREPROCESS}" ] ; then
	cmd="${SOLID_PREPROCESS} ${options} ${csfasta} ${qual}"
	$cmd
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
#====================================================================
#
# run_fastq_screen
#
# Run set of contaminant screens using the fastq_screen.sh script
#
# Supply full path of input qual file; specify --color if using
# colorspace data
#
# Usage: run_fastq_screen [ --color ] <fastq_file>
function run_fastq_screen() {
    FASTQ_SCREEN_QC=`dirname $0`/fastq_screen.sh
    if [ -f "${FASTQ_SCREEN_QC}" ] ; then
	${FASTQ_SCREEN_QC} $@
    else
	echo ERROR ${FASTQ_SCREEN_QC} not found, fastq_screen step skipped
    fi
}
