#!/bin/sh -e
#
# Generate sequence alignment files for arbitrary fasta file
if [ $# -eq 0 ] ; then
  echo "Usage: $(basename $0) [--qsub=...] FASTA SEQ_DIR"
  echo ""
  echo "Generates sequence alignment (.nib) files for each"
  echo "chromosome in FASTA, and puts them into SEQ_DIR"
  echo ""
  echo "Options:"
  echo "  --qsub  Run operations via qsub (i.e. Grid Engine)"
  echo "          Use --qsub=\"...\" to specify additional"
  echo "          options for qsub"
  exit
fi
# Get command line options
use_qsub=no
qsub_args=
while [ $# -gt 2 ] ; do
  arg=$1
  case $arg in
     --qsub=*)
       use_qsub=yes
       qsub_args=$(echo $arg | cut -d= -f2-)
       ;;
     --qsub)
       use_qsub=yes
       ;;
     *)
       echo "ERROR unrecognised option: $arg" >&2
       exit 1
       ;;
  esac
  shift
done
# Get input file 
FASTA=$1
if [ ! -f "$FASTA" ] ; then
  echo File $FASTA not found >&2
  exit 1
fi
# Get destination
SEQ_DIR=$2
if [ ! -d "$SEQ_DIR" ] ; then
  echo Destination $SEQ_DIR not found >&2
  exit 1
fi
this_dir=$(pwd)
cd $SEQ_DIR
SEQ_DIR=$(pwd)
cd $this_dir
# Check for require utilities
got_splitter=$(which split_fasta.py 2>&1 | grep -v ": no ")
if [ -z "$got_splitter" ] ; then
  echo ERROR split_fasta.py not found >&2
  exit 1
fi
got_fa_to_nib=$(which faToNib 2>&1 | grep -v ": no ")
if [ -z "$got_fa_to_nib" ] ; then
  echo ERROR faToNib not found >&2
  exit 1
fi
# Report settings
echo Fasta: $FASTA
echo Destination: $SEQ_DIR
echo Using qsub: $use_qsub
echo qsub args: $qsub_args
# Make temp working dir
wd=$(mktemp -d --suffix=.make_nibs --tmpdir=.)
echo Working dir $wd
cd $wd
# Split the fasta
echo Splitting $FASTA into individual chromosome files
if [ $use_qsub == yes ] ; then
  qsub $qsub_args -cwd -sync y -V -b y split_fasta.py $FASTA
else
  split_fasta.py $FASTA
fi
if [ $? -ne 0 ] ; then
  echo ERROR split_fasta.py finished with non-zero status >&2
  exit 1
fi
# Generate nib files
echo Creating nib files
chroms=$(ls chr*.fa)
for chrom in $chroms ; do
  echo Processing $chrom
  nib=${chrom%.*}.nib
  if [ $use_qsub == yes ] ; then
    qsub $qsub_args -cwd -sync y -V -b y -N faToNib.$chrom faToNib $chrom $nib
  else
    faToNib $chrom $nib
  fi
  if [ $? -ne 0 ] ; then 
    echo ERROR faToNib finished with non-zero status >&2
    exit 1
  fi
done
# Copy to destination
echo Copying .nib files to $SEQ_DIR
cp *.nib $SEQ_DIR
# Remove working dir
cd ..
echo Removing working dir
rm -rf $wd
echo Done
exit
##
#
