General NGS utilities
=====================

General NGS scripts that are used for both ChIP-seq and RNA-seq.

* :ref:`extract_reads`: write out subsets of reads from input data files
* :ref:`reorder_fasta`: reorder chromosomes in FASTA file in karyotypic order
* :ref:`sam2soap`: convert from SAM file to SOAP format
* :ref:`split_fasta`: extract individual chromosome sequences from fasta file
* :ref:`split_fastq` : split fastq file by lane

.. _extract_reads:

extract_reads.py
****************

Usage::

    extract_reads.py OPTIONS infile [infile ...]

Extract subsets of reads from each of the supplied files according to
specified criteria (e.g. random, matching a pattern etc). Input files
can be any mixture of FASTQ (``.fastq``, ``.fq``), CSFASTA
(``.csfasta``) and QUAL (``.qual``).

Output file names will be the input file names with ``.subset``
appended.

Options:

.. cmdoption:: -m PATTERN, --match=PATTERN

    Extract records that match Python regular expression
    ``PATTERN``

..cmdoption:: -n N

    Extract ``N`` random records from the input file(s)
    (default 500). If multiple input files are specified,
    the same subsets will be extracted for each.

.. _reorder_fasta:

reorder_fasta.py
****************

Reorder the chromosome records in a FASTA file into karyotypic order.

Usage::

    reorder_fasta.py INFILE.fa

Reorders the chromosome records from a FASTA file into 'kayrotypic'
order, e.g.::

    chr1
    chr2
    ...
    chr10
    chr11

The output FASTA file will be called ``INFILE.karyotypic.fa``.

.. _sam2soap:

sam2soap.py
***********

Convert a SAM file into SOAP format.

Usage::

    sam2soap.py OPTIONS [ SAMFILE ]

Convert SAM file to SOAP format - reads from stdin (or SAMFILE, if
specified), and writes output to stdout unless -o option is
specified.

Options:

.. cmdoption:: -o SOAPFILE

    Output SOAP file name

.. _split_fasta:

split_fasta.py
**************

Extract individual chromosome sequences from a fasta file.

Usage::

    split_fasta.py fasta_file

Split input FASTA file with multiple sequences into multiple
files each containing sequences for a single chromosome.

For each chromosome CHROM found in the input Fasta file (delimited
by a line ``>CHROM``), outputs a file called ``CHROM.fa`` in the
current directory containing just the sequence for that chromosome.

.. _split_fastq:

split_fastq
***********

Splits a Fastq file by lane.

Usage::

    split_fastq.py [-h] [-l LANES] FASTQ

Split input Fastq file into multiple output Fastqs where each output only
contains reads from a single lane. 

Options:

.. cmdoption:: -l LANES, --lanes LANES

    lanes to extract: can be a single integer, a comma-
    separated list (e.g. 1,3), a range (e.g. 5-7) or a
    combination (e.g. 1,3,5-7). Default is to extract all
    lanes in the Fastq
