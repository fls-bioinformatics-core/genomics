#!/bin/sh
#
# Bcl to Fastq conversion wrapper script
#
# Usage: bclToFastq.sh OPTIONS <illumina_run_dir>  <output_dir> [ <sample_sheet> ]
#
# Runs configureBclToFastq.pl from CASAVA to set up conversion scripts, then runs
# make to perform the actual conversion
#
# Requires that CASAVA is available on the system.
#
# Help information
usage="Usage: `basename $0` OPTIONS <illumina_run_dir> <output_dir> [ <sample_sheet> ]"
if [ "$1" == "-h" ] || [ "$1" == "--help" ] ; then
    echo $usage
    cat <<EOF

Automate the CASAVA BCL to FASTQ conversion process

Runs configureBclToFastq.pl followed by make step. Supplied OPTIONS are
passed to configureBclToFastq.pl; <illumina_run_dir> is the top-level
directory of the Illumina run to be processed; output will be written to
the specified <output_dir>.

Optionally a non-default <sample_sheet> file can also be specified,
otherwise the SampleSheet.csv file in the BaseCalls directory will be
used, if present.

Options:

  -h, --help        display usage text
  --nmismatches N   set number of mismatches to allow; recommended values are 0 for
                    samples without multiplexing, 1 for multiplexed samples with tags
                    of length 6 or longer (see the CASAVA user guide for details of
                    the --nmismatches option)
  --use-bases-mask BASES_MASK
                    specify a bases-mask string tell CASAVA how to use each cycle.
                    The supplied value is passed directly to configureBcltoFastq.pl
                    (see the CASAVA user guide for details of how --use-bases-mask
                    works)
  --nprocessors N   set the number of processors to use (defaults to 1).
                    This is passed to the -j option of the 'make' step after running
                    configureBcltoFastq.pl (see the CASAVA user guide for details of
                    how -j works)
EOF
    exit
fi
#
# Check arguments
if [ $# -lt 2 ] ; then
    echo $usage
    exit 1
fi
#
# Echo command line
echo "=================================================================="
echo `basename $0`
echo "=================================================================="
echo "Arguments: $@"
echo 
#
# Defaults
n_mismatches=0
n_processors=1
#
# Collect command line options to pass directly to CASAVA
casava_options=
while [ ! -z `echo $1 | grep "^-"` ] ; do
    case $1 in
	--use-bases-mask)
	    shift
	    casava_options="$casava_options --use-bases-mask $1"
	    ;;
	--nmismatches)
	    shift
	    n_mismatches=$1
	    ;;
	--nprocessors)
	    shift
	    n_processors=$1
	    ;;
	*)
	    echo "Ignored option $1"
	    ;;
    esac
    shift
done
#
# Input parameters
illumina_run_dir=$1
fastq_output_dir=$2
sample_sheet_file=$3
#
basecalls_dir=${illumina_run_dir}/Data/Intensities/BaseCalls
#
if [ -z "$sample_sheet_file" ] ; then
    # Collect the default sample sheet
    sample_sheet_file=${basecalls_dir}/SampleSheet.csv
fi
force=
#
echo Illumina run directory: $illumina_run_dir
echo BaseCalls directory   : $basecalls_dir
echo SampleSheet.csv file  : $sample_sheet_file
echo Fastq output directory: $fastq_output_dir
echo Number of mismatches  : $n_mismatches
echo Number of processors  : $n_processors
echo Additional options    : $casava_options
#
# Check input directory
if [ ! -d "$illumina_run_dir" ] ; then
    echo ERROR no directory $illumina_run_dir
    exit 1
elif [ ! -d "$basecalls_dir" ] ; then
    echo ERROR no BaseCalls directory $basecalls_dir
    exit 1
fi
#
# Check output directory
if [ -d "$fastq_output_dir" ] ; then
    echo WARNING output dir $fastq_output_dir exists
    echo Using --force option of configureBclToFastq.pl
    force=--force
fi
#
# Check sample sheet
if [ -f $sample_sheet_file ] ; then
    sample_sheet="--sample-sheet $sample_sheet_file"
else
    echo WARNING sample sheet $sample_sheet not found
    sample_sheet=
fi
#
# Locate configureBclToFastq.pl script
configureBclToFastq=`which configureBclToFastq.pl 2>&1`
got_bcl_converter=`echo $configureBclToFastq | grep "no configureBclToFastq.pl"`
if [ ! -z "$got_bcl_converter" ] ; then
    echo ERROR configureBclToFastq.pl not found
    exit 1
fi
#
# Run configureBclToFastq
echo Running configureBclToFastq
cmd="configureBclToFastq.pl \
    --input-dir $basecalls_dir \
    --output-dir $fastq_output_dir \
    --mismatches $n_mismatches \
    --fastq-cluster-count -1 \
    $casava_options \
    $sample_sheet \
    $force"
echo $cmd
$cmd
status=$?
echo configureBclToFastq: finished exit code $status
#
# Check output
if [ ! -d "$fastq_output_dir" ] ; then
    echo ERROR no output directory $fastq_output_dir found
    exit 1
fi
cd $fastq_output_dir
if [ ! -f Makefile ] ; then
    echo ERROR no Makefile from configurebclToFastq.pl
    exit 1
fi
#
# Run the 'make' step
echo Running make
make -j $n_processors
status=$?
echo make: finished exit code $status
#
# Change permissions on "Unaligned" directory
cd ..
chmod -R g+rwX `basename $fastq_output_dir`
#
# Finished
echo $0: finished
exit
##
#
