#!/bin/sh -e
#
# Run test of best_exons.py
if [ ! -d output ] ; then
  mkdir output
fi
best_exons.py data/exons3genes.txt output/log2foldchange.out
best_exons.py --rank-by=p_value data/exons3genes.txt output/pvalue.out
##
#
