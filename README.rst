genomics/bcftbx
===============

Utilities for NGS and genomics-related bioinformatics developed within the
Bioinformatics Core Facility (BCF) within the Faculty of Life Sciences (FLS)
at the University of Manchester (UoM).

Full documentation is available at http://genomics-bcftbx.readthedocs.org.

Overview
********

The utilities are divided into broad categories:

- Handling data from SOLiD and Illumina sequencers (``solid2cluster``,
  ``illumina2cluster``)
- Performing QC and manipulation of NGS data (``QC-pipeline``)
- Setting up reference data (``build-indexes``)
- Supporting analysis of ChIP-seq, RNA-seq and microarray data (``ChIP-seq``,
  ``RNA-seq``, ``microarray``, ``NGS-general``)
- General non-bioinformatics utilities (``utils``)

There is also a Python package called ``bcftbx`` which is used by many of the
programs, and which provides a wide range of utility functions.

Installation
************

It is recommended to use::

    pip install .

from within the top-level source directory to install the package.

To use the package without installing it first you will need to add the
directory to your ``PYTHONPATH`` environment.

To install directly from github using ``pip``::

    pip install git+https://github.com/fls-bioinformatics-core/genomics.git

Setup
*****

Many of the scripts should run directly after installation without additional
setup. The exceptions are the QC scripts, which require a ``qc_setup.sh``
file to be created and edited to point to the locations of the ``fastq_screen``
configuration files.

Documentation
*************

Documentation based on ``sphinx`` is available under the ``docs`` directory.

To build do either::

    python setup.py sphinx_build

or::

    cd docs
    make html

both of which create the documentation in the ``docs/build`` subdirectory.

Running Tests
*************

The Python unit tests can be run using::

    python setup.py test

Note that this requires the ``nose`` package.

There are also some test scripts in the ``QC-pipeline/tests`` directory,
these can be run individually or via a 'runner' script::

    run_tests.sh

(Note that this requires that the QC scripts have already been setup after
installing the package.)

In addition the tests are run via TravisCI whenever this GitHub repository
is updated:

.. image:: https://travis-ci.org/fls-bioinformatics-core/genomics.png?branch=master
   :alt: Current status of TravisCI build for master branch
   :target: https://travis-ci.org/fls-bioinformatics-core/genomics/builds

Developmental version
*********************

The developmental branch of the code on github is ``devel``, this can be
installed using::

    pip install git+https://github.com/fls-bioinformatics-core/genomics.git@devel

Use the ``-e`` option to install an 'editable' version (see the section on
`"Editable" installs
<https://pip.pypa.io/en/latest/reference/pip_install.html#editable-installs>_`
in the pip documentation),

The tests are run on TravisCI whenever the developmental version is updated:

.. image:: https://travis-ci.org/fls-bioinformatics-core/genomics.png?branch=devel
   :alt: Current status of TravisCI build for devel branch
   :target: https://travis-ci.org/fls-bioinformatics-core/genomics/builds

Dependencies
************

The package consists predominantly of code written in Python, which has been
used extensively with Python 2.6 and 2.7.

In addition there are scripts requiring:

- bash
- Perl
- R

The following packages are required for subsets of the code:

- perl: ``Statistics::Descriptive`` and ``BioPerl``
- python: ``xlwt``, ``xlrd`` and ``xlutils``

Some of the scripts also use third party software, including:

- bowtie
- bowtie2
- bfast
- fastq_screen
- fastqc
- ``convert`` (from ImageMagick)

There are also a couple of Java-based programs.
