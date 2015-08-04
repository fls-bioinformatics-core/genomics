#!/bin/bash
#
# versions.sh: shell functions for acquiring program versions
# Peter Briggs, University of Manchester 2012
#
# NB This also requires the shell functions from functions.sh.
#
# get_version(): extract and return version number
#
# e.g. version=$(get_version <name>)
function get_version() {
    get_version_exe=$(find_program $1)
    if [ ! -z "$get_version_exe" ] ; then
	get_version_name=$(baserootname $get_version_exe)
	case "$get_version_name" in
	    bowtie2*)
		# bowtie2 --version
		# .../bowtie2-align version 2.1.0
		echo `$get_version_exe --version 2>&1 | grep "bowtie2" | grep "version" | cut -d" " -f3`
		;;
	    bowtie*)
		# bowtie --version
		# bowtie version 0.12.7
		echo `$get_version_exe --version 2>&1 | grep "bowtie" | grep "version" | cut -d" " -f3`
		;;
	    bfast)
		# bfast
		# Version: 0.7.0a git:Revision: undefined$
		echo `$get_version_exe 2>&1 | grep Version | cut -d" " -f2`
		;;
	    cufflinks)
		# cufflinks
		# cufflinks v2.0.2
		echo `$get_version_exe 2>&1 | grep "^cufflinks " | cut -d" " -f2`
		;;
	    fastq_screen)
		# fastq_screen --version
		# fastq_screen v0.3.1
		echo `$get_version_exe --version | cut -d" " -f2`
		;;
	    fastqc)
		# fastqc -v
		# FastQC v0.10.0
		echo `$get_version_exe -v 2>&1 | tail -1 | cut -d" " -f2`
		;;
	    samtools)
		# samtools: Version: 0.1.18 (r982:295)
		echo `$get_version_exe 2>&1 | grep Version | cut -d" " -f2`
		;;
	    SOLiD_preprocess_filter_*)
		# No option to get version
		# Return trailing part of name
		echo `echo $get_version_name | cut -d"_" -f4 | cut -d"." -f1`
		;;
	    solid2fastq)
		# solid2fastq
		# solid2fastq 0.7.0a
		echo `$get_version_exe 2>&1 | head -1 | cut -d" " -f2`
		;;
	    tophat)
		# tophat --version
		# TopHat v1.4.1
		echo `$get_version_exe --version 2>&1 | cut -d" " -f2`
		;;
	    *)
		echo
		;;
	esac
    fi
}
function report_program_info() {
    echo $(basename $1)$'\t'$(get_version $1)$'\t'$(find_program $1)
}
#
# Tests: import into shell and do "run_tests"
function run_tests() {
    get_version bowtie-build
    get_version cufflinks
    get_version bfast
    get_version samtools
    get_version fastq_screen
    get_version fastqc
    get_version solid2fastq
    get_version tophat
}
##
#
