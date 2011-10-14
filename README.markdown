genomics: repository for FLS in-house genomics-related software
===============================================================

Scripts are organised into the following directories:

* [ChIP-seq](ChIP-seq): contains ChIP-seq-specific scripts
* [RNA-seq](RNA-seq): contains RNA-seq-specific scripts
* [NGS-general](NGS-general): contains general NGS scripts not specific to a
  particular type of experiment
* [build-indexes](build-indexes): contains scripts for building genome
  indexes for various programs
* [QC-pipeline](QC-pipeline): contains scripts for running QC pipelines on
  SOLiD data sets
* [solid2cluster](solid2cluster): utilities for copying data from SOLiD
  instrument to cluster
* [utils](utils): non-NGS utility scripts
* [share](share): common libraries and modules shared between applications
* [shoebox](shoebox): a place for scrappy or one-off utility scripts which
  may or may not be useful in future.

Dependencies
------------

* R
* perl Statistics::Descriptive module
* BioPerl
* java
* python (2.4+)
* python xlwt, xlrd, xlutils libraries
