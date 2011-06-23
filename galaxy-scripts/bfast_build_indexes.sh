#!/bin/sh
#
# bfast_build_indexes.sh
#
# Create reference genome and indexes for bfast (color space
# only i.e. -A 1 option of bfast) plus the .brg files (both
# color and base space).
#
# Options
#   -d <depth>      [default 1]
#   -w <hash_width> [default 14]
#   --dry-run       [print commands but don't execute them]
#
# Inputs
#   FASTA file containing the reference genome
#
# Outputs
#   In the current directory: creates *.cs.brg and *.nt.brg files
#   plus color space index files *.cs.x.y.bif
#   Also creates a symbolic link to the input FASTA file
#
script_name=`basename $0`
SCRIPT_NAME=`echo ${script_name%.*} | tr [:lower:] [:upper:]`
usage="$script_name [-d <depth>] [-w <hash_width>] [--dry-run] <genome_fasta_file>"
#
# Initialisations
BFAST=`which bfast 2>&1 | grep -v which`
if [ "$BFAST" == "" ] ; then
    echo Fatal: bfast program not found
    echo Check that bfast is on your PATH and rerun
    exit 1
fi
#
# Current environment
run_date=`date`
machine=`uname -n`
user=`whoami`
run_dir=`pwd`
#
# Bfast settings
FASTA_GENOME=
SPLITTING_DEPTH=1
HASH_WIDTH=14
#
# Dry run
# If set to anything other than an empty value then only print
# the commands, don't run them
DRY_RUN=
#
# Command line arguments
while [ "$1" != "" ] ; do
    case $1 in
	-d)
	    # -d <depth>
	    shift
	    SPLITTING_DEPTH=$1
	    ;;
	-w)
	    # -w <hash_width>
	    shift
	    HASH_WIDTH=$1
	    ;;
	--dry-run)
	    # Dry run mode
	    DRY_RUN=yes
	    ;;
	*)
	    # Assume unrecognised argument
	    # is the input FASTA file
	    FASTA_GENOME=$1
	    ;;
    esac
    # Next argument
    shift
done
# Input fasta file for reference genome
if [ "$FASTA_GENOME" == "" ] ; then
    echo Fatal: no input fasta file specified
    echo $usage
    exit 1
fi
#
# Bfast index options
BFAST_INDEX_OPTIONS="-w $HASH_WIDTH -d $SPLITTING_DEPTH"
#
# Check input file exists
if [ ! -f "$FASTA_GENOME" ] ; then
    echo Fatal: input fasta file not found
    echo $usage
    exit 1
fi
#
# Specify the scratch area for large temporary BFAST files
if [ "${SCRATCH}" != "" ] && [ -d "${SCRATCH}" ] ; then
    # Scratch area found so use this for temporary files
    # NB needs the trailing "/"
    BFAST_TEMP_DIR="-T ${SCRATCH}/"
else
    # No scratch area
    BFAST_TEMP_DIR=
fi
#
# Collect program version
BFAST_VERSION=`$BFAST 2>&1 | grep Version | cut -d" " -f2`
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
bfast exe       : $BFAST
bfast version   : $BFAST_VERSION
bfast index opts: $BFAST_INDEX_OPTIONS
bfast temp dir  : $BFAST_TEMP_DIR
qsub queue      : $USE_QUEUE
EOF
if [ ! -z $DRY_RUN ] ; then
    echo "************ Dry run mode ************"
fi
#
# Make a link to the fasta file from the current directory
LN_FASTA_GENOME=`basename $FASTA_GENOME`
if [ ! -f $LN_FASTA_GENOME ] ; then
    echo Making soft link to $LN_FASTA_GENOME
    if [ -z $DRY_RUN ] ; then
	ln -s $FASTA_GENOME $LN_FASTA_GENOME
    fi
else
    echo $LN_FASTA_GENOME: already exists
    if [ -h $LN_FASTA_GENOME ] ; then
	echo $LN_FASTA_GENOME is a link
    fi
fi
#
# Nucleotide space
#
# Outputs ${input}.nt.brg file
fasta2brg_nuc_cmd="$BFAST fasta2brg $BFAST_TEMP_DIR -f $LN_FASTA_GENOME"
##echo qsub $USE_QUEUE -cwd -V -b y -N bfast_fasta2brg_nt \'$fasta2brg_nuc_cmd\'
##qsub $USE_QUEUE -cwd -V -b y -N bfast_fasta2brg_nt $fasta2brg_nuc_cmd
echo $fasta2brg_nuc_cmd
if [ -z $DRY_RUN ] ; then
    $fasta2brg_nuc_cmd
fi
#
# Colour space
#
# Outputs ${input}.cs.brg file
fasta2brg_cs_cmd="$BFAST fasta2brg $BFAST_TEMP_DIR -f $LN_FASTA_GENOME -A 1"
##echo qsub $USE_QUEUE -cwd -V -b y -N bfast_fasta2brg_cs \'$fasta2brg_cs_cmd\'
##qsub $USE_QUEUE -cwd -V -b y -N bfast_fasta2brg_cs $fasta2brg_cs_cmd
echo $fasta2brg_cs_cmd
if [ -z $DRY_RUN ] ; then
    $fasta2brg_cs_cmd
fi
#
# Create indexes
#
# Masks for SOLiD data
# See http://helix.nih.gov/Applications/bfast-book.pdf (p57)
masks="1111111111111111111111 
111110100111110011111111111 
10111111011001100011111000111111 
1111111100101111000001100011111011 
111111110001111110011111111 
11111011010011000011000110011111111 
1111111111110011101111111 
111011000011111111001111011111 
1110110001011010011100101111101111 
111111001000110001011100110001100011111"
#
# Run index for each mask
#
# Note: these are dependent on the colorspace binary reference genome file
# (.brg) generated in the initial step - use qsub hold_jid to ensure that
# these jobs don't start before that job has finished
#
# Each mask is accompanied by an index (specified using the -i option) so
# output files are:
#
# ${input}.cs.${index}.1.bif
indx=1
for mask in $masks ; do
    bfast_index_cmd="$BFAST index -f $LN_FASTA_GENOME $BFAST_TEMP_DIR $BFAST_INDEX_OPTIONS -m $mask -i $indx -A 1"
    ##echo qsub $USE_QUEUE -hold_jid bfast_fasta2brg_cs -cwd -V -N bfast_index -b y \'$bfast_index_cmd\'
    ##qsub $USE_QUEUE -hold_jid bfast_fasta2brg_cs -cwd -V -N bfast_index -b y $bfast_index_cmd
    echo $bfast_index_cmd
    if [ -z $DRY_RUN ] ; then
	$bfast_index_cmd
    fi
    indx=$((indx+1))
done
#
echo ===================================================
echo $SCRIPT_NAME: FINISHED
echo ===================================================
exit