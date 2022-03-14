Fasta manipulation
==================

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
