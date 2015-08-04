#!/bin/bash
#
# build_indexes.sh
#
# Build indexes for all programs from input fasta file
#
# Runs scripts to generate bowtie, bowtie2 and srma indexes
# and place them in "bowtie" and "bowtie2" subdirectories
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
# Bowtie2 indexes
#
# Make bowtie2 directory
BOWTIE2_DIR=`pwd`/bowtie2
if [ ! -d ${BOWTIE2_DIR} ] ; then
    echo "Making ${BOWTIE2_DIR}"
    mkdir -p $BOWTIE2_DIR
fi
#
# Descend into bowtie2 dir and run the build script
# Index files will be created here
cd bowtie2
echo ${SCRIPT_DIR}/bowtie2_build_indexes.sh ${FASTA}
${SCRIPT_DIR}/bowtie2_build_indexes.sh ${FASTA}
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
