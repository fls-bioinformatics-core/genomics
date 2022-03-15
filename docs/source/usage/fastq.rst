Fastq manipulation
==================

*****************************************
Extract subsets of reads from Fastq files
*****************************************

The :ref:`reference_extract_reads` utility extracts subsets of
reads from each of the supplied Fastq files according to specified
criteria (either a random subset of a specified number reads, or
readings matching a specified pattern).

Multiple files are assumed to be pairs (e.g. R1/R2 Fastqs) or
groups (R1/I1/R2 Fastqs), with the same number of read records.
The same subset will be extracted from each file, so that
pairing/grouping is preserved.

.. note::

   Input files can be any mixture of Fastq (``.fastq``, ``.fq``),
   or CSFASTA (``.csfasta``) and QUAL (``.qual``) files.

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
