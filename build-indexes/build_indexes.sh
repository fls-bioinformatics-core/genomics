#!/bin/sh
#
# build_indexes.sh
#
# Build indexes for all programs from input fasta file
#
# Runs scripts to generate bowtie, bfast and srma indexes
# and place them in "bowtie" and "bfast" subdirectories
# of the current directory
#
# Usage: build_indexes.sh <genome>.fa
#
# Base dir for scripts
SCRIPT_DIR=`pwd`/`dirname $0`
if [ ! -d "$SCRIPT_DIR" ] ; then
    # Assume absolute path
    SCRIPT_DIR=`dirname $0`
fi
#
# Full path for fasta file
FASTA=`pwd`/${1}
if [ ! -f "$FASTA" ] ; then
    # Assume absolute path
    FASTA=${1}
    if [ ! -f "$FASTA" ] ; then
	echo "$1 not found"
	exit 1
    fi
fi
echo "Input fasta: $FASTA"
#
# Bowtie indexes
#
# Make bowtie directory
BOWTIE_DIR=`pwd`/bowtie
if [ ! -d ${BOWTIE_DIR} ] ; then
    echo "Making ${BOWTIE_DIR}"
    mkdir -p $BOWTIE_DIR
fi
#
# Descend into bowtie dir and run the build script
# Index files will be created here
cd bowtie
echo ${SCRIPT_DIR}/bowtie_build_indexes.sh ${FASTA}
${SCRIPT_DIR}/bowtie_build_indexes.sh ${FASTA}
cd ..
#
# Bfast indexes
#
# Make bfast directory
BFAST_DIR=`pwd`/bfast
if [ ! -d ${BFAST_DIR} ] ; then
    echo "Making ${BFAST_DIR}"
    mkdir -p $BFAST_DIR
fi
#
# Descend into bfast dir and run the build script
# Index files will be created here
cd bfast
echo ${SCRIPT_DIR}/bfast_build_indexes.sh -d 1 -w 14 ${FASTA}
${SCRIPT_DIR}/bfast_build_indexes.sh -d 1 -w 14 ${FASTA}
cd ..
#
# SRMA indexes
#
# Run from pwd; the indexes will be created in the same location
# as the fasta file
echo ${SCRIPT_DIR}/srma_build_indexes.sh ${FASTA}
${SCRIPT_DIR}/srma_build_indexes.sh ${FASTA}
#
# Finished
exit
##
#