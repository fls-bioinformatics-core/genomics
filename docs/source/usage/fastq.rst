Fastq manipulation
==================

******************************************************
Extract subsets of reads from Fastq/CSFASTA/QUAL files
******************************************************

The :ref:`reference_extract_reads` utility extracts subsets of
reads from each of the supplied files according to specified
criteria (either a random subset of a specified number reads, or
readings matching a specified pattern).

Input files can be any mixture of Fastq (``.fastq``, ``.fq``), or
CSFASTA (``.csfasta``) and QUAL (``.qual``) files; output file
names will be the input file names with ``.subset`` appended.

********************************************
Split multi-lane Fastq into individual lanes
********************************************

Given a multi-lane Fastq file (that is, a Fastq file containing
reads for several different sequencer lanes), the
:ref:`reference_split_fastq` utility splits that data into
multiple output Fastqs where each file only contains reads from
a single lane.

**********************************
Verify that Fastq files are paired
**********************************

The :ref:`reference_verify_paired` utility verifies that two
Fastqs form an R1/R2 pair, by checking that read headers for
corresponding records from the input Fastq files are in agreement.
