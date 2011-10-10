#!/bin/sh
#
# function.sh: library of useful shell functions
# Peter Briggs, University of Manchester 2011
#
# Set of useful shell functions to do simple operations such as
# strip/return file extensions, convert strings to upper/lowercase
# locate a program on the path, and fetch the version numbers for
# specific programs.
#
# To include in a shell script, do:
#
# . `dirname $0`/functions.sh
#
# if this file is in the same directory as the script, or
#
# . `dirname $0`/relative/path/to/functions.sh
#
# if it's elsewhere.
#
# getextension(): return file extension
#
# e.g. ext=$(getextension <filename>)
function getextension() {
    echo ${1##*.}
}
#
# rootname(): return file rootname i.e. no extension
#
# name=$(rootname <filename>)
function rootname() {
    echo ${1%.*}
}
#
# baserootname(): return file with no extension or
# leading directory
#
# e.g. name=$(baserootname <filename>)
function baserootname() {
    rootname `basename $1`
}
#
# to_upper(): convert string to uppercase
#
# e.g. upper=$(to_upper <string>)
function to_upper() {
    echo $1 | tr [:lower:] [:upper:]
}
#
# to_lower(): convert string to lowercase
#
# e.g. lower=$(to_lower <string>)
function to_lower() {
    echo $1 | tr [:upper:] [:lower:]
}
#
# find_program(): return path to program
#
# e.g. prog=$(find_program <name>) 
function find_program() {
    echo `which $1 2>&1 | grep -v which`
}
#
# timestamp(): get timestamp on file as seconds from epoch
#
# Usage: timestamp <file>
function timestamp() {
    echo `stat -c %X $1`
}
#
# abs_path(): get the absolute path
#
# Usage: abs_path <file>
function abs_path() {
    if [ "$1" == "." ] ; then
	echo `pwd`
    elif [ -e "$1" ] ; then
	try_path=`pwd`/$1
	if [ -e "$try_path" ] ; then
	    echo $try_path
	else
	    echo $1
	fi
    else
	echo $1
    fi
}
#
# get_version(): extract and return version number
#
# e.g. version=$(get_version <name>)
function get_version() {
    get_version_exe=$(find_program $1)
    if [ ! -z "$get_version_exe" ] ; then
	get_version_name=$(baserootname $get_version_exe)
	case "$get_version_name" in
	    bowtie*)
		echo `$get_version_exe --version 2>&1 | grep "bowtie" | grep "version" | cut -d" " -f3`
		;;
	    bfast)
		echo `$get_version_exe 2>&1 | grep Version | cut -d" " -f2`
		;;
	    samtools)
		echo `$get_version_exe 2>&1 | grep Version | cut -d" " -f2`
		;;
	    *)
		echo
		;;
	esac
    fi
}
#
# Tests: import into shell and do "run_tests"
function run_tests() {
    getextension file.txt
    rootname /path/to/file.txt
    baserootname /path/to/file.txt
    to_upper "testing_testing 123"
    find_program bowtie
    get_version bowtie-build
    get_version bfast
    get_version samtools
}
##
#
