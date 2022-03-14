NGS utilities
=============

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

****************************************
Reorder FASTA file into karyotypic order
****************************************

The :ref:`reference_reorder_fasta` utility will reorder the
chromosome records in a FASTA file into 'karyotypic' order,
for example:

::

    chr1
    chr2
    ...
    chr10
    chr11

in contrast to standard alphanumeric sorting (e.g. ``chr1``,
``chr10``, ``chr11``, ``chr2`` etc).

*******************************
Convert SAM file to SOAP format
*******************************

The :ref:`reference_sam2soap` utility converts a SAM file to SOAP
format

********************************************
Extract chromosome sequences from FASTA file
********************************************

The :ref:`reference_split_fasta` utility extracts the sequences
associated with individual chromosomes from one or more FASTA
files.

Specifically, for each chromosome ``CHROM`` found in the input
FASTA file, outputs a file called ``CHROM.fa`` containing just
the sequence for that chromosome.

Sequences are identified as belonging to a specific chromosome
by a line ``>CHROM``.

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
