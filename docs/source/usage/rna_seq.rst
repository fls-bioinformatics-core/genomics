Reporting RNA-seq outputs
=========================

The :ref:`reference_bowtie_mapping_stats` utility can be used to summarise
the mapping statistics produced by ``bowtie2`` or ``bowtie``, and output to
an MS Excel spreadsheet file.

The utility reads the ``bowtie2`` log file and expects this to consist of
multiple blocks of text of the form:

::

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

The sample name will be extracted along with the numbers of reads processed,
with at least one reported alignment, that failed to align, and with
alignments suppressed and tabulated in the output spreadsheet.
