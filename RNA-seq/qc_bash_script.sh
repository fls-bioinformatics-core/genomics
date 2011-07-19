#!/bin/bash
#
# A generalised version of LZ's QC script for RNA-seq samples
#
# Runs bowtie, boxplotter and fastq_screen
#
# Usage: [qsub] qc_bash_script.sh <analysis_dir> <sample_name> <csfasta> <qual> <bowtie_genome_index>
#
# Arguments:
# <analysis_dir>: directory to write the outputs to
# <sample_name>: name of the sample
# <csfasta>: input csfasta file
# <qual>: input qual file
# <bowtie_genome_index>: full path to bowtie genome index
#
# Outputs:
# Creates a "qc" subdirectory in <analysis_dir> which contains the
# fastq_screen and boxplotter output files.
#
# qsub options:
#$ -j y
#$ -cwd
#$ -o ${HOME}/out

echo "QC_bash_script.sh"
echo "Run RNA-seq QC pipeline (bowtie, boxplots and fastq_screen)"

# Collect command line arguments
ANALYSIS_DIR=$1
SAMPLE_NAME=$2
CSFASTA=$3
QUAL=$4
BOWTIE_INDEX=$5

# Check analysis directoy already exists and has symbolic links to the
# csfasta and qual data files
if [ ! -d "$ANALYSIS_DIR" ] ; then
    echo "Analysis dir $ANALYSIS_DIR not found"
    exit 1
fi
if [ ! -f "$CSFASTA" ] ; then
    echo "csfasta file $CSFASTA not found"
    exit 1
fi
if [ ! -f "$QUAL" ] ; then
    echo "qual file $QUAL not found"
    exit 1
fi

# Make a qc directory (if necessary) and then move into it
# All outputs will be written to this directory
if [ ! -d "qc" ] ; then
    mkdir qc
fi
cd ${ANALYSIS_DIR}/qc

# Report inputs sample name
echo Sample name: $SAMPLE_NAME

# Generate fastq file from the SOLiD csfasta and qual file
solid2fastq -o ${SAMPLE_NAME} ${CSFASTA} ${QUAL}

# Run bowtie - short read aligner
# bowtie [options] <ebwt> <s> <hit>
bowtie -C -m 1 -S ${BOWTIE_INDEX} ${SAMPLE_NAME}.fastq  ${SAMPLE_NAME}.sam

# Generate boxplot
colour_QC_script.sh ${QUAL}

# Run fastq_screen
fastq_screen --subset 1000000 ${SAMPLE_NAME}.fastq

# Clean up
#
# Remove SAM file
rm  ${SAMPLE_NAME}.sam
# Remove postscript files from boxplotting
rm *.ps
#
# Done
