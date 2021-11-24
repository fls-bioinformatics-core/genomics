Illumina data handling utilities
================================

Utilities for preparing data on the cluster from the Illumina instrument:

* :ref:`prep_sample_sheet`: edit SampleSheet.csv before generating FASTQ
* :ref:`verify_paired`: utility to check FASTQs form R1/R2 pair

.. _prep_sample_sheet:

prep_sample_sheet.py
********************

Prepare sample sheet files for Illumina sequencers for input into CASAVA.

Usage::

    prep_sample_sheet.py [OPTIONS] SampleSheet.csv

Utility to prepare SampleSheet files from Illumina sequencers. Can be used to
view, validate and update or fix information such as sample IDs and project
names before running BCL to FASTQ conversion.

Options:

.. cmdoption:: -o SAMPLESHEET_OUT

    output new sample sheet to ``SAMPLESHEET_OUT``

.. cmdoption::  -f FMT, --format=FMT

    specify the format of the output sample sheet written by the ``-o`` option;
    can be either ``CASAVA`` or ``IEM`` (defaults to the format of the original
    file)

.. cmdoption:: -v, --view

    view contents of sample sheet

.. cmdoption:: --fix-spaces

    replace spaces in sample ID and project fields with underscores

.. cmdoption:: --fix-duplicates

    append unique indices to Sample IDs where original ID and project name
    combination are duplicated

.. cmdoption:: --fix-empty-projects

    create sample project names where these are blank in the original sample sheet

.. cmdoption:: --set-id=SAMPLE_ID

    update/set the values in the Sample ID field;
    SAMPLE_ID should be of the form ``<lanes>:<name>``,
    where ``<lanes>`` is a single integer (e.g. 1), a set of
    integers (e.g. 1,3,...), a range (e.g. 1-3), or a
    combination (e.g. 1,3-5,7)

.. cmdoption:: --set-project=SAMPLE_PROJECT

    update/set values in the sample project field;
    ``SAMPLE_PROJECT`` should be of the form ``[<lanes>:]<name>``,
    where the optional ``<lanes>`` part can be a single integer (e.g. 1), a set of
    integers (e.g. 1,3,...), a range (e.g. 1-3), or a
    combination (e.g. 1,3-5,7). If no lanes are specified then all
    samples will have their project set to ``<name>``

.. cmdoption:: --ignore-warnings

    ignore warnings about spaces and duplicated sampleID/sampleProject
    combinations when writing new samplesheet.csv file

.. cmdoption:: --include-lanes=LANES

    specify a subset of lanes to include in the output sample sheet;
    ``LANES`` should be single integer (e.g. 1), a list of integers (e.g.
    1,3,...), a range (e.g. 1-3) or a combination (e.g. 1,3-5,7).
    Default is to include all lanes

Deprecated options:

.. cmdoption:: --truncate-barcodes=BARCODE_LEN

    trim barcode sequences in sample sheet to number of bases specified
    by ``BARCODE_LEN``. Default is to leave barcode sequences unmodified
    (deprecated; only works for CASAVA-style sample sheets)

.. cmdoption:: --miseq

    convert MiSEQ input sample sheet to CASAVA-compatible format (deprecated;
    conversion is performed specify -f/--format CASAVA to convert IEM sample
    sheet to older format)


Examples:

1. Read in the sample sheet file ``SampleSheet.csv``, update the ``SampleProject``
   and ``SampleID`` for lanes 1 and 8, and write the updated sample sheet to the
   file ``SampleSheet2.csv``::

     prep_sample_sheet.py -o SampleSheet2.csv --set-project=1,8:Control \
          --set-id=1:PhiX_10pM --set-id=8:PhiX_12pM SampleSheet.csv

2. Automatically fix spaces and duplicated ``sampleID``/``sampleProject``
   combinations and write out to ``SampleSheet3.csv``::

     prep_sample_sheet.py --fix-spaces --fix-duplicates \
          -o SampleSheet3.csv SampleSheet.csv

.. _verify_paired:

verify_paired.py
****************

Utility to verify that two fastq files form an R1/R2 pair.

Usage::

    verify_paired.py OPTIONS R1.fastq R2.fastq

Check that read headers for R1 and R2 fastq files are in agreement, and that
the files form an R1/2 pair.
