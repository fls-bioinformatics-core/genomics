#!/bin/sh
#
# fetch_fasta.sh: reproducibly download and create fasta files for
# various organisms
#
# Usage: fetch_fasta.sh [ <name> ]
#
# If <name> is supplied then download the sequence and create the
# fasta file for that organism.
#
# (If invoked without arguments then prints a list of the organism
# names that are available.)
#
# Adding new organisms
# --------------------
# The information for downloading and creating the fasta file for
# an organism called <name> is in a function "setup_<name>".
#
# Within the "setup_..." function, various "set_<attribute>"
# functions are available to define the name, source archive
# and any additional processing functions that are required. A
# minimal set is:
#
# set_name "Organism name"
# set_build "Genome build"
# set_info "Info on e.g. which chromosomes are included"
# set_mirror http://where/the/archive/is/kept
# set_archive organism.zip
# set_ext fa
#
# To specify additional processing steps use the
# "add_processing_step" function, e.g.
#
# add_processing_step "Remove haplotypes" "rm *hap*"
#
# To specify comments to be added to the .info file use the
# "add_comment" function, e.g.
#
# add_comment "Haplotypes removed"
#
# See the existing setup_... functions for examples.
#
# ===============================================================
# Setup functions for different organisms
# ===============================================================
#
# E.coli
function setup_ecoli() {
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
    # Comments
    add_comment "These datafiles contain the finished genomic sequences of the long chromosome arms*, as well as nonredundant scaffolds from the heterochromatin."
    add_comment "Scaffolds that could not be unambiguously mapped to a chromosome arm have been concatenated into chrU."
    add_comment "Removed chrUextra: chrUextra contains 34,630 small scaffolds produced by the Celera shotgun assembler that could not be consistently joined with larger scaffolds. Because some of the chrUextra data are of low quality, researchers are encouraged to contact either BDGP or DHGP for further details on this resource."
}
#
# WS200: worm
function setup_ws200() {
    set_name    "Caenorhabditis elegans"
    set_build   "WS200 February 24 2009"
    set_info    "C.Elegans WS200"
    set_mirror  ftp://ftp.sanger.ac.uk/pub/wormbase/FROZEN_RELEASES/WS200/genomes/c_elegans/sequences/dna
    set_archive c_elegans.WS200.dna.fa.gz
    set_ext     fa
}
#
# WS201: worm
function setup_ws201() {
    set_name    "Caenorhabditis elegans"
    set_build   "WS201 March 25 2009"
    set_info    "C.Elegans WS201"
    set_mirror  ftp://ftp.wormbase.org/pub/wormbase/genomes/c_elegans/sequences/dna
    set_archive c_elegans.WS201.dna.fa.gz
    set_ext     fa
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
    # Delete haplotypes
    add_processing_step "Delete haplotypes" "rm -f *hap*"
}
#
# hg19: human
function setup_hg19() {
    set_name    "Homo sapiens"
    set_build   "hg19 GRCh37 - Feb. 2009 assembly of the human genome (hg19, GRCh37 Genome Reference Consortium Human Reference 37 (GCA_000001405.1))"
    set_info    "Base chr. (1 to 22, X, Y), 'random' and chrM - unmasked"
    set_mirror  http://hgdownload.cse.ucsc.edu/goldenPath/hg19/bigZips
    set_archive chromFa.tar.gz
    set_ext     fa
    # Delete haplotypes
    add_processing_step "Delete haplotypes" "rm -f *hap*"
}
#
# mm9: mouse
function setup_mm9() {
    set_name    "Mus musculus"
    set_build   "MM9/NCBI37 July 2007"
    set_info    "Base chr. (1 to 19, X, Y), chrN_random, chrM and chrUn_random - unmasked"
    set_mirror  http://hgdownload.cse.ucsc.edu/goldenPath/mm9/bigZips
    set_archive chromFa.tar.gz
    set_ext     fa
}
#
# PhiX
function setup_PhiX() {
    set_name    "Enterobacteria phage phiX174"
    set_build   "NCBI accession code NC_001422.1"
    set_info    "Complete genome"
    set_mirror  ftp://ftp.ncbi.nih.gov/genomes/Viruses/Enterobacteria_phage_phiX174_sensu_lato_uid14015
    set_archive NC_001422.fna
    set_ext     fna
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
    # Unpacks into subdirectories so need to move the fa files
    # to the current directory
    add_comment "Archive unpacks .fa files into subdirectories 1,2,3..etc"
    add_processing_step "Put chromosome files in cwd" "mv */*.fa ."
}
#
# sacCer2: yeast
function setup_sacCer2() {
    set_name    "Saccharomyces cerevisiae"
    set_build   "sacCer2 June 2008"
    set_info    ""
    set_mirror  http://hgdownload.cse.ucsc.edu/goldenPath/sacCer2/bigZips
    set_archive chromFa.tar.gz
    set_ext     fa
}
#
# SpR6
function setup_SpR6() {
    set_name    "Streptococcus pneumoniae R6"
    set_build   "NCBI accession code NC_003098"
    set_info    "Complete genome"
    set_mirror  ftp://ftp.ncbi.nih.gov/genomes/Bacteria/Streptococcus_pneumoniae_R6_uid57859
    set_archive NC_003098.fna
    set_ext     fna
}
#
# UniVec
function setup_UniVec() {
    set_name    "UniVec"
    set_build   "UniVec build #6.0 (Nov. 8, 2010)"
    set_info    "See http://www.ncbi.nlm.nih.gov/VecScreen/UniVec.html"
    set_mirror  ftp://ftp.ncbi.nih.gov/pub/UniVec
    set_archive UniVec
    set_ext     fa
    # Rename the downloaded file
    add_processing_step "Rename download to give it fa extension" "mv UniVec UniVec_fasta.fa"
}
#
# ===============================================================
# Functions for setup, downloading and unpacking etc
# ===============================================================
#
# set_name <organism>
# Written to the "Organism" field of the info file
function set_name() {
    NAME=$1
}
#
# set_build <build_description>
# Written to the "Genome build" field of the info file
function set_build() {
    BUILD=$1
}
#
# set_info <information>
# Written to the "Manipulations" field of the info file
function set_info() {
    INFO=$1
}
#
# set_mirror <url>
# Location to download the genome sequence archive from
# (not including the archive itself)
function set_mirror() {
    MIRROR=$1
}
#
# set_archive <archive_name>
# The archive file to be downloaded from the URL given
# with set_mirror()
function set_archive() {
    ARCHIVE=$1
}
#
# set_ext <fasta_extension>
# Set the file extension for the fasta files extracted
# from the archive (e.g. "fa", "fasta")
function set_ext() {
    EXT=$1
}
#
# add_processing_step <description> <command>
#
# Add a command to be executed once the archive has been
# downloaded and unpacked. The command is also recorded in the
# ### Scripts ### section of the .info file.
#
# Multiple processing commands can be specified by calling
# this function once for each command.
#
# Typically this can be used to move or rename files, or to
# remove files before concatenation.
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
# add_comment <comment>
#
# Add a comment string to be added to the ### Comments ### section
# of the .info file.
#
# Multiple comments can be added by calling this function once
# for each comment.
function add_comment() {
    if [ -z "$COMMENTS" ] ; then
	# Make the initial comments file
	COMMENTS=`mktemp --suffix .txt`
	echo "Storing comments in: $COMMENTS"
    fi
    # Append comment
    echo "# $1" >> $COMMENTS
}
#
# reset_settings
#
# Reset the internal state after calling any of the "setup_..."
# functions
function reset_settings() {
    clean_up > /dev/null
    NAME=
    BUILD=
    INFO=
    MIRROR=
    ARCHIVE=
    EXT=
    FASTA=
    POST_PROCESS_SCRIPT=
    COMMENTS=
}
#
# unpack_archive <archive_file>
#
# Extracts contents of <archive_file> to the current directory
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
# fetch_url <url>
#
# Download <url> to the current directory
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
# fetch_sequence
#
# Download, unpack, process and concat the sequence data
# from the archive specified in the setup_<organism>
# function
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
    else
	# No archive
	echo "ERROR no archive defined"
	return 1
    fi
    # Add rename or concatenation command into processing script
    # Do it this way so that the command is added to the info file
    n_fasta=`ls *.${EXT} 2>/dev/null | wc -l`
    if [ "$n_fasta" == "1" ] ; then
	add_processing_step "rename" "mv *.${EXT} ${FASTA}"
    else
	add_processing_step "concatenate" "cat *.${EXT} > ${FASTA}"
    fi
    # Apply post-processing commands
    if [ ! -z "$POST_PROCESS_SCRIPT" ] ; then
	echo "Processing unpacked files"
	/bin/sh $POST_PROCESS_SCRIPT
    fi
    # Check that something got written
    fsize=`du --apparent-size -s ${FASTA} | cut -f1`
    if [ "$fsize" == 0 ] ; then
	echo "ERROR failed to create fasta file"
	echo "See files in $TMP_DIR"
	exit 1
    fi
    # Copy fasta file to target directory
    if [ ! -d "${wd}/fasta" ] ; then
	mkdir ${wd}/fasta
    fi
    /bin/cp ${FASTA} ${wd}/fasta
    echo "Made ${FASTA}"
    # Return to working directory
    cd ${wd}
    return 0
}
#
# list_chromosomes
#
# Extract a list of chromosome names from the fasta file
# and write to <organism>.chr.list
function list_chromosomes() {
    echo "Writing chromosome list"
    grep "^>" fasta/${FASTA} | cut -c2- > ${ORGANISM}.chr.list
}
#
# write_info
#
# Create a .info file for the sequence file, with the data
# supplied by the setup_<organism> function
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
# Person: $(user_real_name $USER)
# Date: $now
EOF
    # Append comments
    if [ ! -z "$COMMENTS" ] ; then
	echo "" >> ${ORGANISM}.info
	echo "### Comments ###" >> ${ORGANISM}.info
	cat $COMMENTS >> ${ORGANISM}.info
    fi
    # Append the post-processing scripts
    if [ ! -z "$POST_PROCESS_SCRIPT" ] ; then
	echo "" >> ${ORGANISM}.info
	echo "### Scripts ###" >> ${ORGANISM}.info
	cat $POST_PROCESS_SCRIPT >> ${ORGANISM}.info
    fi
}
#
# clean_up
#
# Remove temporary files and directories
function clean_up() {
    # Remove processing script
    if [ -f "$POST_PROCESS_SCRIPT" ] ; then
	echo "Removing processing script"
	/bin/rm $POST_PROCESS_SCRIPT
    fi
    # Remove comments file
    if [ -f "$COMMENTS" ] ; then
	echo "Removing temporary comments file"
	/bin/rm $COMMENTS
    fi
    # Remove temp dir
    if [ -d "$TMP_DIR" ] ; then
	echo "Removing temporary directory"
	/bin/rm -rf $TMP_DIR
    fi
}
#
# user_real_name <username>
#
# Get a user's real name (from finger) based on their user name
function user_real_name() {
    finger $1 | grep -o "Name: .*$" | cut -d" " -f2-
}
#
# usage
#
# Print usage information
function usage() {
    echo "Usage: `basename $0` [ <organism> ]"
    echo ""
    echo "Download sequence data for <organism> and create fasta file"
    echo "alongside chromosome list and descriptive 'info' file."
    echo ""
    echo "Run without arguments to see this help and list the available"
    echo "organisms."
    echo ""
    echo "Available organisms:"
    names=$(available_names)
    for name in $names ; do
	setup_${name} >> /dev/null
	echo "  ${name}"$'\t'$'\t'"${NAME} (${BUILD})"
	reset_settings
    done
}
#
# available_names
#
# Echo a list of available organism names i.e. all
# names for which a setup_<organism> function exists
function available_names() {
    grep "^function setup_" $0 | cut -c16- | cut -f1 -d"(" | sort
}
#
# check_organism <name>
#
# Check if <name> is one of the available organism names.
#
# Return 0 if yes, 1 if no
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
# Check command line
if [ -z "$1" ] ; then
    usage
    exit
fi
# Get organism name and check it's available
ORGANISM=$1
if ! check_organism $ORGANISM ; then
    echo "$ORGANISM not available"
    exit 1
fi
# Set up
setup_${ORGANISM}
FASTA=${ORGANISM}.${EXT}
if [ -f "fasta/${FASTA}" ] ; then
    # Fasta file already exists
    echo $FASTA already exists, nothing to do
else
    # Create the sequence file
    if fetch_sequence ; then
	list_chromosomes
	write_info
    fi
fi
clean_up
##
#
