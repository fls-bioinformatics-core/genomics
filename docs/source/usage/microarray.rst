Microarray utilities
====================

Scripts and tools for microarray specific tasks.

* :ref:`annotate_probesets`: annotate probe set list based on probeset
  names
* :ref:`best_exons`: average data for 'best' exons for each gene symbol
  in a file
* :ref:`xrorthologs`: cross-reference data for two species using probeset
  lookup

.. _annotate_probesets:

annotate_probesets.py
*********************

Usage::

     annotate_probesets.py OPTIONS probe_set_file

Annotate a probeset list based on probe set names: reads in first column
of tab-delimited input file `probe_set_file` as a list of probeset names
and outputs these names to another tab-delimited file with a description
for each.

Output file name can be specified with the `-o` option, otherwise it will
be the input file name with `_annotated` appended.

Options:

.. cmdoption:: -o OUT_FILE

    specify output file name

Example input::

    ...
    1769726_at
    1769727_s_at
    ...

generates output::

    ...
    1769726_at	Rank 1: _at : anti-sense target (most probe sets on the array)
    1769727_s_at	Warning: _s_at : designates probe sets that share common probes among multiple transcripts from different genes
    ...

.. _best_exons:

best_exons.py
*************

Average data for 'best' exons for each gene symbol in a file.

Usage::

    best_exons.py [OPTIONS] EXONS_IN BEST_EXONS

Read exon and gene symbol data from ``EXONS_IN`` and picks the top three exons for
each gene symbol, then outputs averages of the associated values to ``BEST_EXONS``.

Options:

.. cmdoption:: --rank-by=CRITERION

    select the criterion for ranking the 'best' exons; possible options are:
    ``log2_fold_change`` (default), or ``p_value``.

.. cmdoption:: --probeset-col=PROBESET_COL

    specify column with probeset names (default=0, columns start counting from
    zero)

.. cmdoption:: --gene-symbol-col=GENE_SYMBOL_COL

    specify column with gene symbols (default=1, columns start counting from
    zero)

.. cmdoption:: --log2-fold-change-col=LOG2_FOLD_CHANGE_COL

    specify column with log2 fold change (default=12, columns start counting
    from zero)

.. cmdoption:: --p-value-col=P_VALUE_COL

    specify column with p-value (default=13; columns start counting from zero)

.. cmdoption:: --debug

    Turn on debug output

Description
-----------

Program to pick 'top' three exons for each gene symbol from a TSV file
with the exon data (file has one exon per line) and output a single
line for that gene symbol with values averaged over the top three.

'Top' or 'best' exons are determined by ranking on either the ``log2FoldChange``
(the default) or ``pValue`` (see the ``--rank-by`` option):

* For ``log2FoldChange``, the 'best' exon is the one with the biggest
  absolute ``log2FoldChange``; if this is positive or zero then takes
  the top three largest fold change value. Otherwise takes the bottom
  three.

* For ``pValue``, the 'best' exon is the one with the smallest value.

Outputs a TSV file with one line per gene symbol plus the average of
each data value for the 3 best exons according to the specified criterion.
The averages are just the mean of all the values.

Input file format
-----------------

Tab separated values (TSV) file, with first line optionally being a header
line.

By default the program assumes:

* Column 0:  probeset name (change using ``--probeset-col``)
* Column 1:  gene symbol (change using ``--gene-symbol-col``)
* Column 12: log2 fold change (change using ``--log2-fold-change-col``)
* Column 13: p-value (change using ``--p-value-col``)

Column numbering starts from zero.

Output file format
-------------------

TSV file with one gene symbol per line plus averaged data for the 'best'
exons, and an extra column which has a ``*`` to indicate which gene symbols
had 4 or fewer exons associated with them in the input file.

.. _xrorthologs:

xrorthologs.py
**************

Cross-reference data for two species using probe set lookup

Usage::

    xrorthologs.py [options] LOOKUPFILE SPECIES1 SPECIES2

Description
-----------

Cross-reference data from two species given a lookup file that maps probe set
IDs from one species onto those onto the other.

``LOOKUPFILE`` is a tab-delimited file with one probe set for species 1 per line in
first column and a comma-separated list of the equivalent probe sets for species 2
in the fourth column, e.g.

::

    ...
    121_at	7849	18510	1418208_at,1446561_at
    1255_g_at	2978	14913	1421061_a
    1316_at	7067	21833	1426997_at,1443952_at,1454675_at
    1320_at	11099	24000	1419054_a_at,1419055_a_at,1453298_at
    1405_i_at	6352	20304	1418126_at
    ...

Data for the two species are in tab-delimited files ``SPECIES1`` and ``SPECIES2``,
where the first column in each is a probe set ID (this is the only requirement).

The output consists of two files:

* ``SPECIES1_appended.txt``: a copy of ``SPECIES1`` with the cross-referenced data
  from ``SPECIES2`` appended to each line, and
* ``SPECIES2_appended.txt``: a copy of ``SPECIES2`` with the ``SPECIES1`` data
  appended.

Where there are multiple matching orthologs to a probe set ID, the data for each
match is appended onto a single line on the output.
