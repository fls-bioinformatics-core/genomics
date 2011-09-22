#!/bin/sh
#
# srma_build_indexes.sh
#
function usage() {
    # Print usage information
    cat <<EOF

Create indexes for SRMA.

Usage
   $script_name <genome_fasta_file>

Inputs
   <genome_fasta_file> FASTA file containing the reference genome

Outputs
    .fai and .dict files in the same directory as the input FASTA file
   (as required by SRMA)
EOF
}
# Import functions
. `dirname $0`/../share/functions.sh
#
# Initialisations
script_name=`basename $0`
SCRIPT_NAME=$(rootname $script_name)
#
# Initialisations
SAMTOOLS=$(find_program samtools)
if [ "$SAMTOOLS" == "" ] ; then
    echo Fatal: samtools program not found
    echo Check that samtools is on your PATH and rerun
    exit 1
fi
#
# Acquire location of Picard tools jar files
: ${PICARD_TOOLS_DIR:=/usr/share/java/picard-tools}
#
# Generate index
CREATE_SEQ_DICT_JAR=${PICARD_TOOLS_DIR}/CreateSequenceDictionary.jar
if [ ! -f ${CREATE_SEQ_DICT_JAR} ] ; then
    echo Fatal: CreateSequenceDictionary.jar not found in $PICARD_TOOLS_DIR
    echo Set the PICARD_TOOLS_DIR variable in your environment to point to the correct location
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
    usage
    exit 1
fi
FASTA_GENOME=$1
#
# Check input file exists
if [ ! -f "$FASTA_GENOME" ] ; then
    echo Fatal: input fasta file not found
    usage
    exit 1
fi
#
# Collect program versions
SAMTOOLS_VERSION=$(get_version $SAMTOOLS)
#
echo ===================================================
echo $(to_upper $SCRIPT_NAME): START
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
picard tools dir: $PICARD_TOOLS_DIR
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
echo $(to_upper $SCRIPT_NAME): FINISHED
echo ===================================================
exit
