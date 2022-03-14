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

***************************************
Manage contaminant sequences for FastQC
***************************************

The :ref:`reference_manage_seqs` utility can to help create and
update files with lists of so-called "contaminant" sequences, for
input into the FastQC program (specifically, via FastQC's
``--contaminants`` option).

For example, to create a new contaminants file using sequences from a
FASTA file:

::

    manage_seqs.py -o custom_contaminants.txt sequences.fa

To append sequences to an existing contaminants file:

::

    manage_seqs.py -a custom_contaminants.txt additional_seqs.fa

The inputs can be a mixture of FastQC "contaminants" format and/or
Fasta format files). The utility also check for redundancy (i.e.
sequences with multiple associated names) and contradictions (i.e.
names with multiple associated sequences).

*******************************
Convert SAM file to SOAP format
*******************************

The :ref:`reference_sam2soap` utility converts a SAM file to SOAP
format.
