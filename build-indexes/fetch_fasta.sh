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
# rn4: rat
function setup_rn4() {
    NAME="Rattus norvegicus"
    BUILD="rn4 Nov. 2004 version 3.4"
    INFO="Base chr. (1 to 20, X, Un), 'random' and chrM"
    MIRROR="http://hgdownload.cse.ucsc.edu/goldenPath/rn4/chromosomes/"
    CHR_LIST="chr1 chr2 chr3 chr4 chr5 chr6 chr7 chr8 chr9 chr10 \
chr11 chr12 chr13 chr14 chr15 chr16 chr17 chr18 chr19 chr20 \
chrX chrUn chrM \
chr1_random chr2_random chr3_random chr4_random chr5_random \
chr6_random chr7_random chr8_random chr9_random chr10_random \
chr11_random chr12_random chr13_random chr14_random chr15_random \
chr16_random chr17_random chr18_random chr19_random chr20_random \
chrX_random chrUn_random"
    EXT="fa"
    FORMAT="gz"
}
#
# ws200: worm
function setup_c_elegans_ws200() {
    NAME="Caenorhabditis elegans"
    BUILD="WS200 February 24 2009"
    INFO="C.Elegans WS201"
    MIRROR=ftp://ftp.sanger.ac.uk/pub/wormbase/FROZEN_RELEASES/WS200/genomes/c_elegans/sequences/dna/
    CHR_LIST="c_elegans.WS200.dna"
    EXT="fa"
    FORMAT="gz"
}
#
# ws201: worm
function setup_c_elegans_ws201() {
    NAME="Caenorhabditis elegans"
    BUILD="WS201 March 25 2009"
    INFO="C.Elegans WS201"
    MIRROR=ftp://ftp.wormbase.org/pub/wormbase/genomes/c_elegans/sequences/dna/
    CHR_LIST="c_elegans.WS201.dna"
    EXT="fa"
    FORMAT="gz"
}
#
# E.coli
function setup_ecoli() {
    NAME="Escherichia coli"
    BUILD=
    INFO="E.Coli"
    MIRROR=ftp://ftp.ncbi.nlm.nih.gov/genomes/Bacteria/Escherichia_coli_536_uid58531/
    CHR_LIST="NC_008253"
    EXT="fna"
    FORMAT=
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
function fetch_chrs() {
    # Make temporary directory for download
    wd=`pwd`
    tmp=`mktemp -d`
    cd $tmp
    echo "Working in temporary directory $tmp"
    # Download and unpack the chromosome files
    for chr in $CHR_LIST ; do
	filen=${chr}.${EXT}
	if [ ! -z "${FORMAT}" ] ; then
	    filen=${filen}.${FORMAT}
	fi
	url=${MIRROR}/${filen}
	echo $url
	wget -nv $url
	if [ ! -f "$filen" ] ; then
	    echo ERROR failed to download $filen
	    exit 1
	fi
	unpack_archive $filen
    done
    # Concatenate into a single fasta file
    cat *.${EXT} > ${wd}/${FASTA}
    echo "Made ${FASTA}"
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
# Manipulations: $INFO
# Source: ${MIRROR}
# Chromosomes: $CHR_LIST
# Extension: $EXT
# Archive format: $FORMAT
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
fetch_chrs
write_info
