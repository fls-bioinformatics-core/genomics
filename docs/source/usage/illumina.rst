Illumina data handling utilities
================================

Utilities for preparing data on the cluster from the Illumina instrument:

* :ref:`prep_sample_sheet`: edit SampleSheet.csv before generating FASTQ
* :ref:`verify_paired`: utility to check FASTQs form R1/R2 pair

Background
**********

This section outlines the general structure of the data from Illumina
based sequencers (GA2x, HiSEQ and MiSEQ) and the procedures for
converting these data into FASTQ format.

Primary sequencing data
-----------------------

The software on the various sequencers  performs image analysis and base
calling, producing primary data files in either ``.bcl`` (binary base call)
format, or (for newer instruments), a compressed version ``.bcl.gz``.

Additional software is required to convert these data files to FASTQ format,
and in the case of multiplexed runs also perform demultiplexing of the data.

The directories produced by the runs have the format::

    <date_stamp>_<instrument_name>_<run_id>_FC

(For example ``120518_ILLUMINA-13AD3FA_00002_FC``)

The components are:

* ``<date-stamp>``: a 6-digit date stamp in year-month-day format e.g.
  ``120518`` is 18th May 2012
* ``<instrument_name>``: name of the Illumina instrument e.g.
  ``ILLUMINA-13AD3FA``
* ``<run_id>``: id number corresponding to the run e.g. ``00002``

A partial directory structure is shown below::

 <YYMMDD>_<machinename>_<XXXXX>_FC/
          |
          +-- Data/
          |     |
          |     +------ Intensities/
          |                  |
          +                  +-- .pos files
          |                  |
          |                  +-- config.xml
          +-- RunInfo.xml    |
                             +-- L001(2,3...)/  (lanes)
                             |
                             +-- BaseCalls/
                                    |
                                    +-- config.xml
                                    |
                                    +-- SampleSheet.csv
                                    |
                                    +--L001(2,3...)/  (lanes)
                                          |
                                          +-- C1.1/   (lane and cycle)
                                                |
                                                +-- .bcl(.gz) files
                                                |
                                                +-- .stats files

Key points:

* The ``.bcl`` or ``.bcl.gz`` files are located under the
  ``Data/Intensities/BaseCalls/`` directory
* The ``config.xml`` file under the ``BaseCalls`` directory is implicitly
  needed for demultiplexing and fastq conversion
* The ``SampleSheet`` file is only needed if the demultiplexing needs to
  be performed.

Fastq generation and demultiplexing
-----------------------------------

Multiplexed sequencing allows multiple samples to be run per lane. The
samples are identified by index sequences (barcodes) that are attached
to the template during sample preparation.

Originally bcl-to-fastq programs in Illumina's ``CASAVA`` software package
could be used to perform both these steps, but were unable to handle the
compressed bcf files produced by newer instruments. Illumina now provide
a ``bclToFastq`` software package which only includes the components of
``CASAVA`` required for FASTQ conversion and which can also deal with
compressed bcl files.

.. note::

    Both ``CASAVA`` and ``bclToFastq`` provide the same programs for the
    conversion, and use the same protocol and input files. Within
    this documentation *bcl-to-fastq* is therefor used interchangably to
    refer to these programs.

The ``configureBclToFastq.pl`` script from bcl-to-fastq can be used to set up
the bcl to fastq conversion, e.g.::

    configureBclToFastq.pl \
             --input-dir <path_to_BaseCalls_dir> \
             --output-dir <path_to_output_dir> \
             [ --sample-sheet <path_to>/SampleSheet.csv ]

This will create the named output directory containing a Makefile which
performs the actual conversion; to run, 'cd' to the output directory and
then run ``make``.

If the ``--output-dir`` option is omitted then it defaults to
``<run_dir>/Unaligned/``. The sample sheet is only required for
demultiplexing.

Other useful options:

* ``--fastq-cluster-count <n>``: sets the maximum "cluster size" for the
  output fastq; this can result in multiple fastq output files. Use -1 to
  force all reads to be put into a single fastq.
* ``--mismatches <n>``: number of mismatches allowed for each read; the
  default is zero (recommended for samples without multiplexing), 1
  mismatch is recommended for multiplexed samples with tags of length 6 bases.

According to the CASAVA 1.8.2 documentation: *"FASTQ files contain only
reads that passed filtering. If you want all reads in a FASTQ file, use
the --with-failed-reads option."*

.. note::

  Comprehensive notes on CASAVA options to use for bcl-to-fastq conversion
  for different demultiplexing scenarios can be found via
  https://gist.github.com/3125885

Sample sheets
-------------

.. warning::

    Sample sheet files are generated by the software on the instrument. For
    older instruments these could be fed directly into the bcl-to-fastq
    conversion software; for newer instruments they are in "experimental
    manager" format, which needs to be converted to the older format - use
    the :ref:`prep_sample_sheet` utility to do this.

The sample sheets accepted by the bcl-to-fastq software are comma-separated
files with the following fields on each line:

+---------------+-----------------------------------------------------+
| Field         | Description                                         |
+===============+=====================================================+
| FCID          | Flow cell ID                                        |
+---------------+-----------------------------------------------------+
| Lane          | Positive integer, indicating the lane number (1-8)  |
+---------------+-----------------------------------------------------+
| SampleID      | ID of the sample                                    |
+---------------+-----------------------------------------------------+
| SampleRef     | The reference used for alignment for the sample     |
+---------------+-----------------------------------------------------+
| Index         | Index sequences. Multiple index reads are separated |
|               | by a hyphen (for example, ACCAGTAA-GGACATGA).       |
+---------------+-----------------------------------------------------+
| Description   | Description of the sample                           |
+---------------+-----------------------------------------------------+
| Control       | Y indicates this lane is a control lane, N means    |
|               | sample                                              |
+---------------+-----------------------------------------------------+
| Recipe        | Recipe used during sequencing                       |
+---------------+-----------------------------------------------------+
| Operator      | Name or ID of the operator                          |
+---------------+-----------------------------------------------------+
| SampleProject | The project the sample belongs to                   |
+---------------+-----------------------------------------------------+

The ``SampleID`` field forms the base of the output fastq name (see below);
the ``SampleProject`` field indicates which project directory the fastq
file will be placed into.

It is advised to set both these fields to something descriptive e.g.
SampleProject = "Control" and SampleName = "PhiX".

To remove a lane from the analysis remove references to it from the sample
sheet file.

The bcl-to-fastq software will automatically use the samplesheet files in the
instrument output directories unless overriden by a user-supplied
samplesheet file.

The samplesheet can be edited using Excel or similar spreadsheet program,
and manipulated using the :ref:`prep_sample_sheet` utility. The modified
samplesheet file name can be supplied as an addition argument to the
``bclToFastq.sh`` script.

Output directory structure
--------------------------

Example output directory structure is::


 Unaligned/
    |
    +-- Project_A/
    |         |
    |         +- Sample_A/
    |         |     |
    |         |   fastq.gz file(s)
    |         |
    |         +- Sample_B/
    |               |
    |             fastq.gz file(s)
    |
    +-- Project_B/
              |
              +- Sample_C/
                    |
                  fastq.gz file(s)

In the absence of a sample sheet, one sample is assumed per lane and all
samples belong to he same project.

Output fastq files
------------------

The general naming scheme for fastq output files is::

    <sample_name>_<barcode_sequence>_L<lane>_R<read_number>_<set_number>.fastq.gz

e.g. ``NA10931_ATCACG_L002_R1_001.fastq.gz``

For non-multiplexed runs, the sample name is the lane (e.g. ``lane1`` etc)
and the barcode sequence is ``NoIndex``

e.g. ``lane1_NoIndex_L001_R1_001.fastq.gz``

The read number is either 1 or 2 (2's only appear for paired-end sequencing).

The quality scores in the output fastq files are Phred+33 (see
http://en.wikipedia.org/wiki/FASTQ_format#Quality under the "Encoding"
section).

Undetermined reads
------------------

When demultiplexing it is likely that the software will be unable to
assign some of the reads to a specific sample. In this case the read is
assigned to "undetermined" instead, and there will be an additional
``Undetermined_indexes`` "project" produced under the ``Unaligned``
directory.

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
