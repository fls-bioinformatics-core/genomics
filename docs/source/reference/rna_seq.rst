RNA-seq specific utilities
==========================

Scripts and tools for RNA-seq specific tasks.

* :ref:`bowtie_mapping_stats`: summarise statistics from bowtie output in spreadsheet

.. _bowtie_mapping_stats:

bowtie_mapping_stats.py
***********************
Extract mapping statistics for each sample referenced in the input bowtie log
files and summarise the data in an XLS spreadsheet. Handles output from both
Bowtie and Bowtie2.

Usage::

    bowtie_mapping_stats.py [options] bowtie_log_file [ bowtie_log_file ... ]

By default the output file is called ``mapping_summary.xls``; use the ``-o`` option to
specify the spreadsheet name explicitly.

Options:

.. cmdoption:: -o xls_file

    specify name of the output XLS file (otherwise defaults to ``mapping_summary.xls``).


.. cmdoption:: -t

    write data to tab-delimited file in addition to the XLS file. The tab file will
    have the same name as the XLS file, with the extension replaced by ``.txt``

Input bowtie log file
---------------------

The program expects the input log file to consist of multiple blocks of text of the form::

    ...
    <SAMPLE_NAME>
    Time loading reference: 00:00:01
    Time loading forward index: 00:00:00
    Time loading mirror index: 00:00:02
    Seeded quality full-index search: 00:10:20
    # reads processed: 39808407
    # reads with at least one reported alignment: 2737588 (6.88%)
    # reads that failed to align: 33721722 (84.71%)
    # reads with alignments suppressed due to -m: 3349097 (8.41%)
    Reported 2737588 alignments to 1 output stream(s)
    Time searching: 00:10:27
    Overall time: 00:10:27
    ...

The sample name will be extracted along with the numbers of reads processed, with at least one
reported alignment, that failed to align, and with alignments suppressed and tabulated in the
output spreadsheet.
