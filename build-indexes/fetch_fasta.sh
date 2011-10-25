#!/bin/sh
#
# fetch_fasta.sh: download and create fasta file for given
# organism
#
# Usage: fetch_fasta.sh <name>
#
# Data is only defined for certain names. To add a new genome
# or genome build, make a new function in this file called e.g.
# "setup_<name>" and set the variables NAME, BUILD, INFO, MIRROR,
# CHR_LIST, EXT and FORMAT as appropriate.
#
# The new name will automatically be available the next time that
# the script is run.
#
# ===============================================================
# Setup functions for different sequences
# ===============================================================
#
# hg19: human
function setup_hg18() {
    NAME="Homo sapiens"
    BUILD="HG18/NCBI36.1 March 2006"
    INFO="Base chr. (1 to 22, X, Y), 'random' and chrM - unmasked"
    MIRROR=http://hgdownload.cse.ucsc.edu/goldenPath/hg18/bigZips
    ARCHIVE=chromFa.zip
    CHR_LIST=
    EXT=fa
    FORMAT=zip
    # Delete haplotypes
    POST_PROCESS="rm -f *hap*"
}
#
# rn4: rat
function setup_rn4() {
    NAME="Rattus norvegicus"
    BUILD="rn4 Nov. 2004 version 3.4"
    INFO="Base chr. (1 to 20, X, Un), 'random' and chrM"
    MIRROR=http://hgdownload.cse.ucsc.edu/goldenPath/rn4/bigZips
    ARCHIVE=chromFa.tar.gz
    CHR_LIST=
    EXT=fa
    FORMAT=zip
    # Unpacks into subdirectories so need to move the fa files
    # to the current directory
    POST_PROCESS="mv */*.fa ."
}
#
# ws200: worm
function setup_c_elegans_ws200() {
    NAME="Caenorhabditis elegans"
    BUILD="WS200 February 24 2009"
    INFO="C.Elegans WS200"
    MIRROR=ftp://ftp.sanger.ac.uk/pub/wormbase/FROZEN_RELEASES/WS200/genomes/c_elegans/sequences/dna
    ARCHIVE=c_elegans.WS200.dna.fa.gz
    CHR_LIST=
    EXT=fa
    FORMAT=gz
    POST_PROCESS=
}
#
# ws201: worm
function setup_c_elegans_ws201() {
    NAME="Caenorhabditis elegans"
    BUILD="WS201 March 25 2009"
    INFO="C.Elegans WS201"
    MIRROR=ftp://ftp.wormbase.org/pub/wormbase/genomes/c_elegans/sequences/dna
    ARCHIVE=c_elegans.WS201.dna.fa.gz
    CHR_LIST=
    EXT=fa
    FORMAT=gz
    POST_PROCESS=
}
#
# E.coli
function setup_ecoli() {
    NAME="Escherichia coli"
    BUILD=
    INFO="E.Coli"
    MIRROR=ftp://ftp.ncbi.nlm.nih.gov/genomes/Bacteria/Escherichia_coli_536_uid58531
    ARCHIVE=NC_008253.fna
    CHR_LIST=
    EXT=fna
    FORMAT=
    POST_PROCESS=
}
#
# ===============================================================
# Functions for downloading and unpacking etc
# ===============================================================
#
function unpack_archive() {
    filen=$1
    ext=${filen##*.}
    echo -n "Unpacking "
    while [ ! -z "$ext" ] ; do
	echo -n "$filen => "
	case "$ext" in
	    gz)
		# gunzip
		gunzip $filen
		;;
	    zip)
		# unzip
		unzip $filen
		;;
	    tar)
		# untar
		tar xf $filen
		;;
	    *)
		# Unrecognised extension
		# Assume we're done
		echo "done"
		return
	esac
	# Set filename and extension for
	# next iteration
	filen=${filen%.*}
	ext=${filen##*.}
    done
}
#
function fetch_url() {
    echo $url
    wget -nv $url
    filen=`basename $url`
    if [ ! -f "$filen" ] ; then
	echo ERROR failed to download $filen
	exit 1
    fi
}
#
function fetch_sequence() {
    # Make temporary directory for download
    wd=`pwd`
    tmp=`mktemp -d`
    cd $tmp
    echo "Working in temporary directory $tmp"
    if [ ! -z "$ARCHIVE" ] ; then
	# Download archive
	url=${MIRROR}/${ARCHIVE}
	fetch_url $url
	unpack_archive $ARCHIVE
    elif [ ! -z "$CHR_LIST" ] ; then
	# Download and unpack the chromosome files
	for chr in $CHR_LIST ; do
	    filen=${chr}
	    if [ ! -z "${EXT}" ] ; then
		filen=${filen}.${EXT}
	    fi
	    if [ ! -z "${FORMAT}" ] ; then
		filen=${filen}.${FORMAT}
	    fi
	    url=${MIRROR}/${filen}
	    fetch_url $url
	    unpack_archive $filen
	done
    fi
    # Apply post-processing commands, if any
    if [ ! -z "$POST_PROCESS" ] ; then
	echo "Doing post-processing:"
	echo "$POST_PROCESS"
	$POST_PROCESS
    fi
    # Concatenate into a single fasta file
    cat *.${EXT} > ${FASTA}
    # Check that something got written
    fsize=`du --apparent-size -s ${FASTA} | cut -f1`
    if [ "$fsize" == 0 ] ; then
	echo "ERROR failed to create fasta file"
	echo "See files in $tmp"
	exit 1
    fi
    echo "Made ${FASTA}"
    /bin/cp ${FASTA} ${wd}
    # Remove temporary directory
    cd ${wd}
    /bin/rm -rf $tmp
}
#
function write_info() {
    now=`date`
    cat <<EOF > ${ORGANISM}.info
# Organism: $NAME
# Genome build: $BUILD
# Source: ${MIRROR}
EOF
    # Archives
    if [ ! -z "$ARCHIVE" ] ; then
	echo "# Archive: $ARCHIVE" >> ${ORGANISM}.info
    else
	echo "# Chromosomes: $CHR_LIST" >> ${ORGANISM}.info
    fi
    # Post-processing steps
    if [ ! -z "$POST_PROCESS" ] ; then
	echo "# Post-processing: $POST_PROCESS" >> ${ORGANISM}.info
    fi
    # Remaining information
    cat <<EOF >> ${ORGANISM}.info
# Fasta: $FASTA
# Date: $now

###
EOF
}
#
function available_names() {
    grep "^function setup_" $0 | cut -c16- | cut -f1 -d"(" | sort
}
#
function check_organism() {
    available=$(available_names)
    for name in $available ; do
	if [ "$1" == "$name" ] ; then
	    return 0
	fi
    done
    return 1
}
#
# ===============================================================
# Main script
# ===============================================================
#
if [ -z "$1" ] ; then
    echo "Usage: $0 <organism>"
    echo ""
    echo "Given an organism name, downloads sequence data and creates"
    echo "fasta file alongside descriptive 'info' file."
    echo ""
    echo "Available organisms:"
    names=$(available_names)
    for name in $names ; do
	echo "  $name"
    done
    exit
fi
#
ORGANISM=$1
if ! check_organism $ORGANISM ; then
    echo "$ORGANISM not available"
    exit 1
fi
setup_${ORGANISM}
FASTA=${ORGANISM}.${EXT}
if [ -f "${FASTA}" ] ; then
    echo $FASTA already exists
    exit 1
fi
fetch_sequence
write_info
