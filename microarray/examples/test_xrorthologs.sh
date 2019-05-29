#!/bin/bash -e
#
# Run test of xrorthologs.py
xrorthologs.py $(dirname $0)/data/lookup.txt $(dirname $0)/data/probe_set_1.txt $(dirname $0)/data/probe_set_2.txt
##
#
