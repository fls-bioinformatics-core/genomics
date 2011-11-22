#!/bin/sh
#
# Unpack rRNA sequences and build bowtie indexes
#
# Usage: build_rRNA_bowtie_indexes.sh <rRNA_archive>
#
# Steps:
# 1. Unpack the rRNA.tar.gz file
# 2. Iterate over the sequence files and create the
#    bowtie indexes
# 3. Make the fastq_screen file
#
# Import functions
. `dirname $0`/../share/functions.sh
#
SCRIPT_DIR=$(abs_path `dirname $0`)
#
# Check command line
echo $#
if [ $# -lt 1 ] ; then
    echo Usage: `basename $0` rRNA_archive
    exit
fi
#
# Destination
GENOME_INDEXES=`pwd`
if [ ! -d ${GENOME_INDEXES}/rRNAs ] ; then
    mkdir -p ${GENOME_INDEXES}/rRNAs/fasta
fi
#
RRNAS_TGZ=$(abs_path $1)
echo "Using archive $RRNAS_TGZ"
#
# Unpack
tmp=$(make_temp -d)
echo $tmp
pushd $tmp
cp ${RRNAS_TGZ} .
RRNAS_TGZ=`basename $RRNAS_TGZ`
tar xvzf ${RRNAS_TGZ}
if [ $? -ne 0 ] ; then
    echo Failed to unpack ${RRNAS_TGZ}
    exit 1
fi
#
# Check that there's an "rRNAs/fasta" subdir
if [ ! -d rRNAs/fasta ] ; then
    echo No rRNAs/fasta subdirectory
    exit 1
fi
#
# Copy the fasta files
for i in `ls rRNAs/fasta` ; do
    if [ ! -e ${GENOME_INDEXES}/rRNAs/fasta/$i ] ; then
	echo Copying $i
	cp rRNAs/fasta/$i ${GENOME_INDEXES}/rRNAs/fasta
    fi
done
popd
rm -rf ${tmp}
#
# Make indexes
mkdir -p ${GENOME_INDEXES}/rRNAs/bowtie
cd ${GENOME_INDEXES}/rRNAs/bowtie
for i in `ls ../fasta` ; do
    echo $i
    ${SCRIPT_DIR}/bowtie_build_indexes.sh ../fasta/$i
    if [ $? -ne 0 ] ; then
	echo Failure building bowtie index for $i
	exit 1
    fi
done
#
# Make fastq_conf file
FASTQ_SCREEN_CONF=${GENOME_INDEXES}/fastq_screen/fastq_screen_rRNA.conf
cd ../..
cat <<EOF > ${FASTQ_SCREEN_CONF}
## fastq_screen_rRNA ##
# Description: rRNA
#
# `date`
#

############
## Threads #
############

THREADS		8

EOF
for i in `ls rRNAs/fasta` ; do
    name=$(baserootname $i)
    display_name=`echo $name | cut -d"_" -f1`
    bowtie_cs_index=$(abs_path rRNAs/bowtie)/${name}_c
    echo "DATABASE"$'\t'${display_name}$'\t'${bowtie_cs_index} >> ${FASTQ_SCREEN_CONF}
done
##
#