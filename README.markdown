genomics: repository for FLS in-house genomics-related software
===============================================================

Scripts are organised into the following directories:

* [build-indexes](build-indexes): contains scripts for building genome
  indexes for various programs
* [ChIP-seq](ChIP-seq): contains ChIP-seq-specific scripts
* [RNA-seq](RNA-seq): contains RNA-seq-specific scripts
* [microarray](microarray): contains microarray-specific scripts
* [NGS-general](NGS-general): contains general NGS scripts not specific to a
  particular type of experiment
* [QC-pipeline](QC-pipeline): contains scripts for running QC pipelines on
  SOLiD data sets
* [solid2cluster](solid2cluster): utilities for copying data from SOLiD
  instrument to cluster
* [illumina2cluster](illumina2cluster): utilities for transferring and
  preparing Illumina data on the compute cluster
* [utils](utils): non-NGS utility scripts
* [share](share): common libraries and modules shared between applications

Dependencies
------------

* R
* perl Statistics::Descriptive module
* BioPerl
* java
* python (2.4+)
* python xlwt, xlrd, xlutils libraries
