Microarray data
===============

*******************
Probeset annotation
*******************

The :ref:`reference_annotate_probesets` utility can be used to annotate
a probeset list based on probe set names.

It requires a tab-delimited file as input, where the first column
comprises the probeset names (any other other columns are ignored), and
outputs each name to a new tab-delimited file alongside a description of
each.

For example input, the following input:

::

    ...
    1769726_at
    1769727_s_at
    ...

generates:

::

    ...
    1769726_at	Rank 1: _at : anti-sense target (most probe sets on the array)
    1769727_s_at	Warning: _s_at : designates probe sets that share common probes among multiple transcripts from different genes
    ...

*****************************
Average data for 'best' exons
*****************************

The :ref:`reference_best_exons` utility picks the 'top' three exons
for each gene symbol from a tab-delimited (TSV) input file containing
the exon data, and outputs a single line for that gene symbol with
values averaged over the top three.

'Top' or 'best' exons are determined by ranking on either the
``log2FoldChange`` (the default) or ``pValue`` (this is set using the
``--rank-by`` option):

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

TSV file with one gene symbol per line plus averaged data for the three
'best' exons (according to the specified criterion), and an extra column
which has a ``*`` to indicate which gene symbols had 4 or fewer exons
associated with them in the input file.

Note that the averages are just the mean of all the values.

************************************
Cross-reference data for two species
************************************

The :ref:`reference_xrorthologs` utility will cross-reference data from
two species, given a lookup file that maps probe set IDs from one species
onto those onto the other.

The lookup file is a tab-delimited file with one probe set for species #1
per line in the first column, and a comma-separated list of the equivalent
probe sets for species 2 in the fourth column (columns two and three
are ignored).

For example:

::

    ...
    121_at	7849	18510	1418208_at,1446561_at
    1255_g_at	2978	14913	1421061_a
    1316_at	7067	21833	1426997_at,1443952_at,1454675_at
    1320_at	11099	24000	1419054_a_at,1419055_a_at,1453298_at
    1405_i_at	6352	20304	1418126_at
    ...

Data for the two species are supplied via tab-delimited files ``SPECIES1``
and ``SPECIES2``, where the first column in each is a probe set ID (this
is the only requirement).

The output consists of two files:

* ``SPECIES1_appended.txt``: a copy of ``SPECIES1`` with the
  cross-referenced data from ``SPECIES2`` appended to each line, and

* ``SPECIES2_appended.txt``: a copy of ``SPECIES2`` with the ``SPECIES1``
  data appended.

Where there are multiple matching orthologs to a probe set ID, the data
for each match is appended onto a single line on the output.
