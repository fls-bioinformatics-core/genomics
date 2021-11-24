#!/bin/bash
#
# index_indexes.sh
#
# Trawl genome indexes and report what's found
#
# Usage: index_indexes.sh <dir>
#
# Explores the hierarchy under the specified directory and reports
# fasta, info and index files that are found.
#
#
# report_files <indent_marker> [<file> [<file> ...]]
#
# If at least one file is specified then print each name per
# line preceeded by the <indent_marker>
function report_files() {
    if [ ! -z "$2" ] ; then
	indent=$1
	echo $indent
	while [ ! -z "$2" ] ; do
	    echo $indent $2
	    shift
	done
    fi
}
#
# trawl <dir> [ <indent_marker> ]
#
# Move into <dir> and look for genome indexes and related files
# Call this script recursively for any subdirectories of <dir>
# that are encountered.
function trawl() {
    # Initialise
    indent="${2}===="
    info=
    fasta=
    brg=
    bif=
    ebwt=
    bt2=
    fai=
    scripts=
    compressed=
    other=
    # Go into the directory
    cd $1
    this_dirn=`pwd`
    this_dirn=`basename $this_dirn`
    echo ${2}
    echo ${2} ${this_dirn}/
    # Analyse files
    files=`/bin/ls`
    if [ -z "$files" ] ; then
	echo ${indent} ...empty...
    fi
    for name in $files ; do
	if [ -d $name ] ; then
	    # Descend into directory for more analysis
	    $TRAWLER $name $indent
	elif [ -f $name ] ; then
	    # Process based on file extension
	    ext=$(getextension $name)
	    case "$ext" in
		info)
		    # info files
		    info="$info $name"
		    ;;
		fa|fasta)
		    # Fasta files
		    fasta="$fasta $name"
		    ;;
		brg)
		    # Bfast brg
		    brg="$brg $name"
		    ;;
		bif)
		    # Bfast bif
		    bif="$bif $name"
		    ;;
		fai)
		    # Samtools fai
		    fai="$fai $name"
		    ;;
		ebwt)
		    # Bowtie index
		    ebwt="$ebwt $name"
		    ;;
		bt2)
		    # Bowtie2 index
		    bt2="$bt2 $name"
		    ;;
		sh)
		    # Script
		    scripts="$scripts $name"
		    ;;
		gz|zip)
		    # Compressed file
		    compressed="$compressed $name"
		    ;;
		*)
		    # Anything that doesn't match
		    other="$other $name"
		    ;;
	    esac
	fi
    done
    # Report
    report_files "${indent}" $info
    report_files "${indent}" $fasta
    report_files "${indent}" $brg
    report_files "${indent}" $bif
    report_files "${indent}" $fai
    report_files "${indent}" $ebwt
    report_files "${indent}" $bt2
    ##report_files "${indent}" $scripts
    report_files "${indent}" $compressed
    ##report_files "${indent}" $other
}
#
# Main script
#
# Sort out script path so we can call it recursively from
# the "trawl" function
TRAWLER=`basename $0`
TRAWLER_DIR=`dirname $0`
if [ "$TRAWLER_DIR" == . ] ; then
    TRAWLER=`pwd`/${TRAWLER}
else
    TRAWLER=${TRAWLER_DIR}/${TRAWLER}
fi
#
# Import external function library
export PATH=$(dirname $0)/../share:${PATH}
. bcftbx.functions.sh
#
# Check a directory was supplied
if [ -z "$1" ] ; then
    echo "Usage: $TRAWLER DIR"
    exit
fi
#
# Begin the trawl
trawl $1 $2
##
#
