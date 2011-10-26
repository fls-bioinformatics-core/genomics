#!/bin/sh
#
# fetch_fasta.sh: reproducibly download and create fasta files for
# various organisms
#
# Usage: fetch_fasta.sh <name>
#
# Data is only defined for certain names. To add a new genome
# or genome build, make a new function in this file called e.g.
# "setup_<name>" and set the variables NAME, BUILD, INFO, MIRROR,
# ARCHIVE (or CHR_LIST and FORMAT), EXT and FORMAT as appropriate.
#
# The new name will automatically be available the next time that
# the script is run.
#
# ===============================================================
# Setup functions for different sequences
# ===============================================================
#
# E.coli
function setup_ecoli_NC_008253() {
    set_name    "Escherichia coli"
    set_build   "NC_008253"
    set_info    "E.Coli"
    set_mirror  ftp://ftp.ncbi.nlm.nih.gov/genomes/Bacteria/Escherichia_coli_536_uid58531
    set_archive NC_008253.fna
    set_ext     fna
}
#
# dm3: fly
function setup_dm3() {
    set_name    "Drosophila melanogaster"
    set_build   "DM3, BDGP Release 5 April 2006"
    set_info    "Base chr. (2L, 2R, 3L, 3R, 4, X), heterochromatin, chrM and chrU - unmasked"
    set_mirror  http://hgdownload.cse.ucsc.edu/goldenPath/dm3/bigZips
    set_archive chromFa.tar.gz
    set_ext     fa
    # Remove chrUextra
    add_processing_step "Exclude chrUextra" "rm chrUextra.fa"
}
#
# WS200: worm
function setup_c_elegans_WS200() {
    set_name    "Caenorhabditis elegans"
    set_build   "WS200 February 24 2009"
    set_info    "C.Elegans WS200"
    set_mirror  ftp://ftp.sanger.ac.uk/pub/wormbase/FROZEN_RELEASES/WS200/genomes/c_elegans/sequences/dna
    set_archive c_elegans.WS200.dna.fa.gz
    set_ext     fa
    set_format  gz
}
#
# WS201: worm
function setup_c_elegans_WS201() {
    set_name    "Caenorhabditis elegans"
    set_build   "WS201 March 25 2009"
    set_info    "C.Elegans WS201"
    set_mirror  ftp://ftp.wormbase.org/pub/wormbase/genomes/c_elegans/sequences/dna
    set_archive c_elegans.WS201.dna.fa.gz
    set_ext     fa
    set_format  gz
}
#
# hg18: human
function setup_hg18() {
    set_name    "Homo sapiens"
    set_build   "HG18/NCBI36.1 March 2006"
    set_info    "Base chr. (1 to 22, X, Y), 'random' and chrM - unmasked"
    set_mirror  http://hgdownload.cse.ucsc.edu/goldenPath/hg18/bigZips
    set_archive chromFa.zip
    set_ext     fa
    set_format  zip
    # Delete haplotypes
    add_processing_step "Delete haplotypes" "rm -f *hap*"
}
#
# rn4: rat
function setup_rn4() {
    set_name    "Rattus norvegicus"
    set_build   "rn4 Nov. 2004 version 3.4"
    set_info    "Base chr. (1 to 20, X, Un), 'random' and chrM"
    set_mirror  http://hgdownload.cse.ucsc.edu/goldenPath/rn4/bigZips
    set_archive chromFa.tar.gz
    set_ext     fa
    set_format  tar.gz
    # Unpacks into subdirectories so need to move the fa files
    # to the current directory
    add_processing_step "Put chromosome files in cwd" "mv */*.fa ."
}
#
# ===============================================================
# Functions for setup, downloading and unpacking etc
# ===============================================================
#
function set_name() {
    NAME=$1
}
#
function set_build() {
    BUILD=$1
}
#
function set_info() {
    INFO=$1
}
#
function set_mirror() {
    MIRROR=$1
}
#
function set_archive() {
    ARCHIVE=$1
}
#
function set_ext() {
    EXT=$1
}
#
function set_format() {
    FORMAT=$1
}
#
function add_processing_step() {
    if [ -z "$POST_PROCESS_SCRIPT" ] ; then
	# Make the initial post process script
	POST_PROCESS_SCRIPT=`mktemp --suffix .sh`
	echo "Adding processing steps to script: $POST_PROCESS_SCRIPT"
    fi
    # Append to the script
    cat <<EOF >> $POST_PROCESS_SCRIPT

# $1
$2
EOF
}
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
		unzip -qq $filen
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
    TMP_DIR=`mktemp -d`
    cd $TMP_DIR
    echo "Working in temporary directory $TMP_DIR"
    if [ -f "${wd}/${ARCHIVE}" ] ; then
	# Archive file already downloaded to pwd
	echo "Archive file found in ${wd}"
	/bin/cp ${wd}/${ARCHIVE} .
	unpack_archive $ARCHIVE
    elif [ ! -z "$ARCHIVE" ] ; then
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
    # Add concatenation command into processing script
    # Do it this way so that the concat is added to the info file
    add_processing_step "concatenate" "cat *.${EXT} > ${FASTA}"
    # Apply post-processing commands
    if [ ! -z "$POST_PROCESS_SCRIPT" ] ; then
	echo "Doing post-processing:"
	cat $POST_PROCESS_SCRIPT
	/bin/sh $POST_PROCESS_SCRIPT
    fi
    # Check that something got written
    fsize=`du --apparent-size -s ${FASTA} | cut -f1`
    if [ "$fsize" == 0 ] ; then
	echo "ERROR failed to create fasta file"
	echo "See files in $TMP_DIR"
	exit 1
    fi
    /bin/cp ${FASTA} ${wd}
    echo "Made ${FASTA}"
    # Return to working directory
    cd ${wd}
}
#
function write_info() {
    now=`date`
    cat <<EOF > ${ORGANISM}.info
# Organism: $NAME
# Genome build: $BUILD
# Manipulations: $INFO
# Source: $MIRROR
EOF
    # Archives
    if [ ! -z "$ARCHIVE" ] ; then
	echo "# Archive: $ARCHIVE" >> ${ORGANISM}.info
    else
	echo "# Chromosomes: $CHR_LIST" >> ${ORGANISM}.info
    fi
    # Remaining information
    cat <<EOF >> ${ORGANISM}.info
# Fasta: $FASTA
# Date: $now
EOF
    # Append the post-processing scripts
    # Post-processing steps
    if [ ! -z "$POST_PROCESS_SCRIPT" ] ; then
	echo "" >> ${ORGANISM}.info
	echo "### Scripts ###" >> ${ORGANISM}.info
	cat $POST_PROCESS_SCRIPT >> ${ORGANISM}.info
    fi
}
#
function clean_up() {
    # Remove processing script
    if [ -f "$POST_PROCESS_SCRIPT" ] ; then
	echo "Removing processing script"
	/bin/rm $POST_PROCESS_SCRIPT
    fi
    # Remove temp dir
    if [ -d "$TMP_DIR" ] ; then
	echo "Removing temporary directory"
	/bin/rm -rf $TMP_DIR
    fi
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
    echo $FASTA already exists, nothing to do
else
    fetch_sequence
    write_info
fi
clean_up
##
#
