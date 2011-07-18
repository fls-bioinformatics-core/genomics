#!/bin/sh
#
# srma_build_indexes.sh
#
# Create indexes for SRMA (.fai and .dict files)
#
# Takes a FASTA file as input.
#
# The index files are created in the same directory as the
# input FASTA file.
#
script_name=`basename $0`
SCRIPT_NAME=`echo ${script_name%.*} | tr [:lower:] [:upper:]`
usage="$script_name <genome_fasta_file>"
#
# Initialisations
SAMTOOLS=`which samtools 2>&1 | grep -v which`
if [ "$SAMTOOLS" == "" ] ; then
    echo Fatal: samtools program not found
    echo Check that samtools is on your PATH and rerun
    exit 1
fi
#
# Acquire Picard tools
PICARD_TOOLS=${HOME}/galaxy/tools/picard-tools-1.47
#
# Generate index
CREATE_SEQ_DICT_JAR=${PICARD_TOOLS}/CreateSequenceDictionary.jar
if [ ! -f ${CREATE_SEQ_DICT_JAR} ] ; then
    echo Fatal: CreateSequenceDictionary.jar not found
    echo Ensure PICARD_TOOLS variable is set correctly
    exit 1
fi
#
run_date=`date`
machine=`uname -n`
user=`whoami`
run_dir=`pwd`
#
# Command line arguments
# Input fasta file for reference genome
if [ "$1" == "" ] ; then
    echo Fatal: no input fasta file specified
    echo $usage
    exit 1
fi
FASTA_GENOME=$1
#
# Check input file exists
if [ ! -f "$FASTA_GENOME" ] ; then
    echo Fatal: input fasta file not found
    echo $usage
    exit 1
fi
#
# Collect program versions
SAMTOOLS_VERSION=`$SAMTOOLS 2>&1 | grep Version | cut -d" " -f2`
#
echo ===================================================
echo $SCRIPT_NAME: START
echo ===================================================
#
# Print program information, versions etc
cat <<EOF
Run date        : $run_date
Machine         : $machine
User            : $user
Run directory   : $run_dir
Input fasta file: $FASTA_GENOME
samtools exe    : $SAMTOOLS
samtools version: $SAMTOOLS_VERSION
picard tools    : $PICARD_TOOLS
qsub queue      : $USE_QUEUE
EOF
#
# Name of output .dict file
DICT_GENOME=${FASTA_GENOME%.*}.dict
#
# Samtools .fai index
samtools_faidx_cmd="$SAMTOOLS faidx $FASTA_GENOME"
echo $samtools_faidx_cmd
$samtools_faidx_cmd
#
# Picard tools .dict index
picard_tools_cmd="java -jar $CREATE_SEQ_DICT_JAR R=${FASTA_GENOME} O=${DICT_GENOME}"
echo $picard_tools_cmd
$picard_tools_cmd
#
echo ===================================================
echo $SCRIPT_NAME: FINISHED
echo ===================================================
exit