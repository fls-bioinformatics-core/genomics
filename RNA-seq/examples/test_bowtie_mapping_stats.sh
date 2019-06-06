#!/bin/bash -e
#
# Run test of bowtie_mapping_stats.py
if [ ! -d output ] ; then
  mkdir output
fi
bowtie_mapping_stats.py -h
bowtie_mapping_stats.py --version
bowtie_mapping_stats.py -o output/mapping_summary.xls -t $(dirname $0)/data/bowtie.out
bowtie_mapping_stats.py -o output/mapping_summary_multi_sample.xls -t $(dirname $0)/data/bowtie_multi_sample.out
bowtie_mapping_stats.py -o output/mapping_summary_multi_file.xls -t $(dirname $0)/data/bowtie_log1.out $(dirname $0)/data/bowtie_log2.out
bowtie_mapping_stats.py -o output/mapping_summary_bowtie2.xls -t $(dirname $0)/data/bowtie2.out
bowtie_mapping_stats.py -o output/mapping_summary_bowtie2_PE.xls -t $(dirname $0)/data/bowtie2_PE.out
##
#
