#!/bin/sh
#
# bowtie2_build_indexes.sh
#
function usage() {
    # Print usage information
    cat <<EOF

Build indexes for BOWTIE2.

Usage
   $script_name <genome_fasta_file>

Inputs
   <genome_fasta_file> FASTA file containing the reference genome

Outputs
   In the current directory: creates <genome_name>.*.bt2 files
EOF
}
# Import functions
. `dirname $0`/../share/functions.sh
#
# Initialisations
script_name=`basename $0`
SCRIPT_NAME=$(rootname $script_name)
#
BOWTIE2_BUILD=$(find_program bowtie2-build)
if [ "$BOWTIE2_BUILD" == "" ] ; then
    echo Fatal: bowtie2-build program not found
    echo Check that bowtie2-build is on your PATH and rerun
    exit 1
fi
#
run_date=`date`
machine=`uname -n`
user=`whoami`
run_dir=`pwd`
#
# Input fasta file for reference genome
if [ "$1" == "" ] ; then
    echo Fatal: no input fasta file specified
    usage
    exit 1
fi
FASTA_GENOME=$1
#
# Genome base name
genome=$(baserootname $FASTA_GENOME)
#
# Check input file exists
if [ ! -f "$FASTA_GENOME" ] ; then
    echo Fatal: input fasta file $FASTA_GENOME not found
    usage
    exit 1
fi
#
# Collect program version
BOWTIE2_VERSION=$(get_version $BOWTIE2_BUILD)
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
bowtie-build exe: $BOWTIE2_BUILD
bowtie version  : $BOWTIE2_VERSION
Genome name     : $genome
Colorspace      : $build_color
Letterspace     : $build_letter
EOF
#
# bt2 outfile base names
bt2_outfile_base=${genome}
#
# Check for fasta data directory
if [ ! -d $fasta_dir ] ; then
    echo "No fasta file directory for genome $genome"
    exit 1
fi
#
# Run bowtie-build in current directory
bowtie2_build_cmd="$BOWTIE2_BUILD -f $FASTA_GENOME $bt2_outfile_base"
echo $bowtie2_build_cmd
$bowtie2_build_cmd
echo ===================================================
echo $(to_upper $SCRIPT_NAME): FINISHED
echo ===================================================
exit
