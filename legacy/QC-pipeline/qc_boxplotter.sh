#!/bin/bash
#
# qc_boxplotter.sh: wrapper script for Ian Donaldson's colour_QC_script.sh boxplotter
#
# Usage: qc_boxplotter.sh <qual_file>
#
`dirname $0`/qc_boxplotter/colour_QC_script.sh $@