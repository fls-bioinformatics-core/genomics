========================
Illumina sequencing data
========================

********
Overview
********

This section outlines the general structure of the data from Illumina
based sequencers (GA2x, HiSEQ, MiSEQ, NextSeq, MiniSeq, iSeq etc) and
the procedures for converting these data into FASTQ format.

A sequencing run performed on one of these sequencer instruments includes
image analysis and base calling, and produces data files in either ``.bcl``
(binary base call) format, or (more commonly), a compressed version
``.bcl.gz`` (the *primary sequencing data*).

Additional processing is required to convert these BCL data files to
Fastq format for subsequent analysis; this processing is referred to as
*BCL-to-fastq conversion*.

In the case of multiplexed runs (i.e. runs where multiple samples are
sequenced in a single lane or run, now typically the standard way that
samples are sequenced) it is also necessary to perform *demultiplexing*
of the data, which assigns data from individual samples into distinct
Fastq files; this requires an additional control file called a
*sample sheet* which specifies which index sequences belong to which
sample.

*********************************************************
Primary sequencing data: structure and naming conventions
*********************************************************

The directories produced by the runs use a standard naming format of
the form:

::

    <date_stamp>_<instrument_name>_<run_id>_<flow_cell>

for example ``120518_ILLUMINA-13AD3FA_00002_FC``.
    
The components are interpreted as follows:

* ``<date_stamp>``: a 6-digit or 8-digit date stamp in year-month-day
  format (e.g. ``120518`` is 18th May 2012)
* ``<instrument_name>``: name of the Illumina instrument (e.g.
  ``ILLUMINA-13AD3FA``)
* ``<run_id>``: id number corresponding to the run (e.g. ``00002``)
* ``<flow_cell>``: identifier for the flow cell used for the run
  (e.g. ``FC``)

A partial directory structure is shown below::

 <YYMMDD>_<INSTRUMENT>_<XXXXX>_<FLOWCELL>/
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

********************************
BCL-to-Fastq conversion software
********************************

Over time Illumina have provided a number of different software packages
to perform the BCL-to-Fastq process:

* **CASAVA**: included a Perl script ``configureBclToFastq.pl`` used
  to generate a ``Makefile`` which performed BCL-to-Fastq conversion
  (``.bcl`` only). CASAVA is no longer supported;
* **bclToFastq**: just the BCL-to-Fastq conversion components of
  CASAVA, with support for both ``.bcl`` and ``.bcl.gz`` formats).
  bclToFastq is no longer supported;
* **bcl2fastq**: (version 1.8.*) provided a single ``bcl2fastq`` program
  to perform the BCL-to-Fastq conversion; used the same sample sheet
  file format as CASAVA and bclToFastq; bcl2fastq is no longer
  supported;
* **bcl2fastq2**: (version 2 and above) updated the ``bcl2fastq``
  program with new options including combining data for the same
  samples sequenced across multiple lanes into a single Fastq, and
  introduced a newer sample sheet format (SampleSheet v1), and modified
  output directory structure and Fastq naming convention. bcl2fastq2
  is still commonly used for BCL-to-Fastq conversion;
* **bcl-convert**: replacement for bcl2fastq2, with a new sample sheet
  format (SampleSheet v2).

**********************************
Demultiplexing: sample sheet files
**********************************

Multiplexed sequencing allows multiple samples to be run per lane, with
the samples being identified by distinct index sequences (barcodes) that
are attached to the template during sample preparation.

In order to demultiplex the data associated with each sample after
sequencing, the index sequences associated with the sample name has to
be supplied to the BCL-to-Fastq conversion software via a *sample sheet
file*.

There have been three different sample sheet formats:

* **CASAVA format**: comma-separated (CSV) file with one sample
  description per line. This format is no longer supported;
* **SampleSheet v1**: (also referred to as "Illumina Experimental
  Manager" or IEM format) introduced with bcl2fastq2 and also
  supported by bcl-convert. Divided into different sections
  containing specific data in CSV format;
* **SampleSheet v2**: introduced with bcl-convert and not supported
  by earlier BCL-to-Fastq conversion software. Similar structure
  to SampleSheet v1 but with different sections and parameters.

.. note::

   The :ref:`reference_prep_sample_sheet` utility can convert between
   CASAVA and SampleSheet v1/IEM formats; it doesn't currently
   support SampleSheet v2 format.

*******************************************************
Output directory structure and Fastq naming conventions
*******************************************************

Since bcl2fastq2, BCL-to-Fastq conversion has resulted in output
directory structures of the form:

::

   <OUT_DIR>/
       |
       +-- Project_A/
       |       |
       |       +-- *.fastq.gz file(s)
       |
       +-- Project_B/
       |       |
       |       +-- *.fastq.gz files(s)
       :
       |
       +-- Reports/
       |
       +-- Stats/
       |
       +-- Undetermined*.fastq.gz file(s)

.. note::

   It is also possible to have additional "sample" subdirectories
   within each project, grouping together Fastq files belonging
   to the same sample, if the sample name and sample ID fields in
   the sample sheet differ.

Within each project, Fastq files are gzipped and use the following
naming scheme:

::

    <sample_name>_S<sample_index>_L<lane>_<read_id>_001.fastq.gz

e.g. ``NA10931_S12_L002_R1_001.fastq.gz``

The sample name is the name supplied in the input sample sheet;
the sample index is an integer which indicates the order of the
sample within the sample sheet (so it is to some extent arbitrary).

Read IDs are ``R1``, ``R2`` etc for data reads, and ``I1``, ``I2``
etc for index reads.

The lane may be omitted if data for the sample has been combined
across all lanes into a single Fastq. For example:

::

   NA10931_S12_R1_001.fastq.gz

The quality scores in the output fastq files are Phred+33 (see
http://en.wikipedia.org/wiki/FASTQ_format#Quality under the "Encoding"
section).

When demultiplexing it is likely that the software will be unable to
assign some of the reads to a specific sample. In this case these
reads will be classed as "undetermined" and will be assigned to
files directly under the top-level output directory with the name

::

   Undetermined_S0_Llane>_<read_id>_001.fastq.gz

.. note::

   The undetermined Fastqs always have sample index zero.

**************
Legacy outputs
**************
       
For pre-bcl2fastq BCL-to-Fastq conversion the output directory
structure would look like:

::

   Unaligned/
       |
       +-- Project_A/
       |         |
       |         +- Sample_1/
       |         |     |
       |         |     +-- *.fastq.gz file(s)
       |         |
       |         +- Sample_2/
       |               |
       |               +-- *.fastq.gz file(s)
       |
       +-- Project_B/
       |         |
       |         +- Sample_3/
       |               |
       |               +-- *.fastq.gz file(s)
       :
       +-- Undetermined_indexes

The general naming scheme for fastq output files is:

::

    <sample_name>_<barcode_sequence>_L<lane>_R<read_number>_<set_number>.fastq.gz

e.g. ``NA10931_ATCACG_L002_R1_001.fastq.gz``


For non-multiplex runs (or in the absence of a sample sheet), one
sample is assumed per lane and all samples belong to he same project
with the sample name being the lane (e.g. ``lane1`` etc) and the index
barcode sequence set to ``NoIndex``, for example:

::

   lane1_NoIndex_L001_R1_001.fastq.gz

When demultiplexing, the "undetermined" reads are assigned to Fastqs
in the ``Undetermined_indexes`` "project".

   
