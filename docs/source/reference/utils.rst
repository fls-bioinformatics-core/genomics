General non-bioinformatic utilities
===================================

General utility scripts/tools.

* :ref:`manage_seqs`: handling sets of named sequences (e.g. FastQC
  contaminants file)
* :ref:`md5checker`: check files and directories using MD5 sums

.. _manage_seqs:

manage_seqs.py
**************

Read sequences and names from one or more INFILEs (which can be a
mixture of FastQC 'contaminants' format and or Fasta format), check
for redundancy (i.e. sequences with multiple associated names) and
contradictions (i.e. names with multiple associated sequences).

Usage::

    manage_seqs.py OPTIONS FILE [FILE...]

Options:

.. cmdoption:: -o OUT_FILE

    write all sequences to ``OUT_FILE`` in FastQC 'contaminants'
    format

.. cmdoption:: -a APPEND_FILE

    append sequences to existing ``APPEND_FILE`` (not compatible
    with ``-o``)

.. cmdoption:: -d DESCRIPTION

    supply arbitrary text to write to the header of the output
    file

Intended to help create/update files with lists of "contaminant"
sequences to input into the ``FastQC`` program (using
``FastQC``'s ``--contaminants`` option).

To create a contaminants file using sequences from a FASTA file
do e.g.::

    manage_seqs.py -o custom_contaminants.txt sequences.fa

To append sequences to an existing contaminants file do e.g.::

    manage_seqs.py -a my_contaminantes.txt additional_seqs.fa

.. _md5checker:

md5checker.py
*************

Utility for checking files and directories using MD5 checksums.

Usage:

To generate MD5 sums for a directory::

    md5checker.py [ -o CHKSUM_FILE ] DIR

To generate the MD5 sum for a file::

    md5checker.py [ -o CHKSUM_FILE ] FILE

To check a set of files against MD5 sums stored in a file::

    md5checker.py -c CHKSUM_FILE

To compare the contents of source directory recursively against
the contents of a destination directory, checking that files in
the source are present in the target and have the same MD5
sums::

    md5checker.py --diff SOURCE_DIR DEST_DIR

To compare two files by their MD5 sums::

    md5checker.py --diff FILE1 FILE2
