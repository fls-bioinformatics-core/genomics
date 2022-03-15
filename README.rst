genomics/bcftbx
===============

Overview
********

``genomics-bcftbx`` provides a Python library and a set of utilities
used for NGS and genomics-related bioinformatics tasks, developed to
support the Bioinformatics Core Facility (BCF) of the Faculty of
Biology, Medicine and Health (FBMH) at the University of Manchester
(UoM).

The ``bcftbx`` library provides submodules for various tasks, including:

* handling data from Illumina and SOLiD sequencing platforms;
* working with various file formats including Fastq, Fasta, MS
  Excel (.xls and .xlsx), HTML and tab-delimited (.tsv) files;
* running commands on local and cluster systems;
* general filesystem operations, text manipulation and checksumming.

The library includes a collection of utilities for tasks including:

* handling Illumina and SOLiD sequencing data;
* reporting outputs from bioinformatics software;
* analysing and reporting microarray data;
* performing basic manipulations on Fastq and Fasta files;
* working with MD5 checksumming of files.

Full documentation is available at http://genomics-bcftbx.readthedocs.org.

Installation
************

It is recommended to install the package into a Python ``virtualenv``,
for example:

::

    virtualenv venv.bcftbx
    . venv.bcftbx/bin/activate

To install a specific version, first download and unpack the source
code, e.g.:

::

    wget https://github.com/fls-bioinformatics-core/genomics/archive/2.0.0.tar.gz
    tar zxf 2.0.0.tar.gz

Then install the package using:

::

    pip install ./genomics-2.0.0

.. note::

   It is also possible to use the package without installing it, by
   first ownloading and unpacking the ``.tar.gz`` archive and then
   adding the ``genomics`` directory to your ``PYTHONPATH`` environment
   and the ``bin`` directory to your ``PATH``.

   In this case you will also need to ensure that the additional
   packages required by the submodules are also installed (e.g.
   ``xlwt``, ``xlrd`` and ``xlutils``).

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

The tests can be run using::

    python setup.py test

In addition the tests are run by GitHub Actions whenever the repository
is updated:

.. image:: https://github.com/fls-bioinformatics-core/genomics/workflows/Python%20CI/badge.svg
   :target: https://github.com/fls-bioinformatics-core/genomics/actions?query=workflow%3A%22Python+CI%22

Developmental version
*********************

The developmental branch of the code on github is ``devel``, this can be
installed using:

::

    pip install git+https://github.com/fls-bioinformatics-core/genomics.git@devel
