genomics/bcftbx
===============

Utilities for NGS and genomics-related bioinformatics developed within the
Bioinformatics Core Facility (BCF) within the Faculty of Life Sciences (FLS)
at the University of Manchester (UoM).

Overview
********

The utilities are divided into broad categories:

- Handling data from SOLiD and Illumina sequencers (`solid2cluster`,
  `illumina2cluster`)
- Performing QC and manipulation of NGS data (`QC-pipeline`)
- Setting up reference data (`build-indexes`)
- Supporting analysis of ChIP-seq, RNA-seq and microarray data (`ChIP-seq`,
  `RNA-seq`, `microarray`, `NGS-general`)
- General non-bioinformatics utilities (`utils`)

There is also a Python package called `bcftbx` which is used by many of the
programs.

Installation
************

It is recommended to use::

    pip install .

from within the top-level source directory to install the package.

To use the package without installing it first you will need to add the
directory to your `PYTHONPATH` environment.

To install directly from github using `pip`::

    pip install git+https://github.com/fls-bioinformatics-core/genomics.git@devel

Documentation
*************

Documentation based on `sphinx` is available under the `docs` directory.

To build::

    cd docs
    make html

which creates the documentation in the `docs/build` subdirectory.

Running Tests
*************

The tests can be run using::

    python setup.py test

Note that this requires the `nose` package.

Dependencies
************

The package consists predominantly of code written in Python, which has been
used extensively with Python 2.6 and 2.7.

In addition there are scripts requiring:

- bash
- Perl
- R

The following packages are required for subsets of the code:

- perl: `Statistics::Descriptive` and `BioPerl`
- python: `xlwt`, `xlrd` and `xlutils`

Some of the scripts also use third party software, including:

- bowtie
- bowtie2
- bfast
- fastq_screen
- fastqc
- `convert` (from ImageMagick)
