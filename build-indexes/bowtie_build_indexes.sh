#!/bin/sh
#
# bowtie_build_indexes.sh
#
function usage() {
    # Print usage information
    cat <<EOF

Build color- and/or nucleotide-space indexes for BOWTIE.

Usage
   $script_name OPTIONS <genome_fasta_file>

Options
By default both color- and nucleotide space indexes are built; to
only build one or the other use one of:

   --nt: build nucleotide-space indexes
   --cs: build colorspace indexes

Inputs
   <genome_fasta_file> FASTA file containing the reference genome

Outputs
   In the current directory: creates <genome_name>.*.ebwt (nucleotide-space) and
   and <genome_name>_c.*.ebwt (color-space) files
EOF
}
# Import functions
. `dirname $0`/../share/functions.sh
. `dirname $0`/../share/versions.sh
#
# Initialisations
script_name=`basename $0`
SCRIPT_NAME=$(rootname $script_name)
#
BOWTIE_BUILD=$(find_program bowtie-build)
if [ "$BOWTIE_BUILD" == "" ] ; then
    echo Fatal: bowtie-build program not found
    echo Check that bowtie-build is on your PATH and rerun
    exit 1
fi
#
run_date=`date`
machine=`uname -n`
user=`whoami`
run_dir=`pwd`
#
# Command line arguments
build_color=
build_letter=
while [ $# -gt 1 ] ; do
    case $1 in
	--cs)
	    build_color=yes
	    ;;
	--nt)
	    build_letter=yes
	    ;;
	*)
	    echo "Unrecognised option: $1"
	    exit 1
	    ;;
    esac
    shift
done
if [ -z "$build_color" ] && [ -z "$build_letter" ] ; then
    # Neither set explicitly so set both
    build_color=yes
    build_letter=yes	    
fi
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
BOWTIE_VERSION=$(get_version $BOWTIE_BUILD)
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
bowtie-build exe: $BOWTIE_BUILD
bowtie version  : $BOWTIE_VERSION
Genome name     : $genome
Colorspace      : $build_color
Letterspace     : $build_letter
EOF
#
# ebwt outfile base names
nt_ebwt_outfile_base=${genome}
cs_ebwt_outfile_base=${genome}_c
#
# Check for fasta data directory
if [ ! -d $fasta_dir ] ; then
    echo "No fasta file directory for genome $genome"
    exit 1
fi
#
# Run bowtie-build in current directory
#
# Nucleotide space
if [ "$build_letter" == yes ] ; then
    nt_bowtie_build="$BOWTIE_BUILD -f $FASTA_GENOME $nt_ebwt_outfile_base"
    echo $nt_bowtie_build
    $nt_bowtie_build
fi
# Colorspace
if [ "$build_color" == yes ] ; then
    cs_bowtie_build="$BOWTIE_BUILD -C -f $FASTA_GENOME $cs_ebwt_outfile_base"
    echo $cs_bowtie_build
    $cs_bowtie_build
fi
echo ===================================================
echo $(to_upper $SCRIPT_NAME): FINISHED
echo ===================================================
exit
