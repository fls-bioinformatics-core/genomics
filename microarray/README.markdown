microarray
==========

Scripts and tools for microarray specific tasks.

  * `best_exons.py`: average data for 'best' exons for each gene symbol in a file
  * `xrothologs.py`: cross-reference data for two species using probe set lookup

best_exons.py
-------------

Average data for 'best' exons for each gene symbol in a file.

### Usage: ###

    best_exons.py [OPTIONS] EXONS_IN BEST_EXONS

Read exon and gene symbol data from EXONS_IN and picks the top three exons for
each gene symbol, then outputs averages of the associated values to BEST_EXONS.

Options:

    --version             show program's version number and exit
    -h, --help            show this help message and exit
    --rank-by=CRITERION   select the criterion for ranking the 'best' exons;
                          possible options are: 'log2_fold_change' (default), or
                          'p_value'.
    --probeset-col=PROBESET_COL
                          specify column with probeset names (default=0, columns
                          start counting from zero)
    --gene-symbol-col=GENE_SYMBOL_COL
                          specify column with gene symbols (default=1, columns
                          start counting from zero)
    --log2-fold-change-col=LOG2_FOLD_CHANGE_COL
                          specify column with log2 fold change (default=12,
                          columns start counting from zero)
     --p-value-col=P_VALUE_COL
                          specify column with p-value (default=13; columns start
                          counting from zero)
    --test                Run unit tests
    --debug               Turn on debug output

### Description ###

Program to pick 'top' three exons for each gene symbol from a TSV file
with the exon data (file has one exon per line) and output a single
line for that gene symbol with values averaged over the top three.

'Top' or 'best' exons are determined by ranking on either the `log2FoldChange`
(the default) or `pValue` (see the `--rank-by` option):

 * For `log2FoldChange`, the 'best' exon is the one with the biggest
   absolute `log2FoldChange`; if this is positive or zero then takes
   the top three largest fold change value. Otherwise takes the bottom
   three.

 * For `pValue`, the 'best' exon is the one with the smallest value.

Outputs a TSV file with one line per gene symbol plus the average of
each data value for the 3 best exons according to the specified criterion.
The averages are just the mean of all the values.

### Input file format ###

Tab separated values (TSV) file, with first line optionally being a header
line.

By default the program assumes:

 * Column 1:  probeset name (change using `--probeset-col`)
 * Column 2:  gene symbol (change using `--gene-symbol-col`)
 * Column 13: log2 fold change (change using `--log2-fold-change-col`)
 * Column 14: p-value (change using `--p-value-col`)

Column numbering starts from 1.

### Output file format ###

TSV file with one gene symbol per line plus averaged data for the 'best'
exons, and an extra column which has a `*` to indicate which gene symbols
had 4 or fewer exons associated with them in the input file.


xrothologs.py
-------------

Cross-reference data for two species using probe set lookup

### Usage: ###

    xrorthologs.py [options] LOOKUPFILE SPECIES1 SPECIES2

### Description ###

Cross-reference data from two species given a lookup file that maps probe set
IDs from one species onto those onto the other.

`LOOKUPFILE` is a tab-delimited file with one probe set for species 1 per line in
first column and a comma-separated list of the equivalent probe sets for species 2
in the fourth column, e.g.

    ...
    121_at	7849	18510	1418208_at,1446561_at
    1255_g_at	2978	14913	1421061_a
    1316_at	7067	21833	1426997_at,1443952_at,1454675_at
    1320_at	11099	24000	1419054_a_at,1419055_a_at,1453298_at
    1405_i_at	6352	20304	1418126_at
    ...

Data for the two species are in tab-delimited files SPECIES1 and SPECIES2, where
the first column in each is a probe set ID (this is the only requirement).

The output consists of two files:

  * `SPECIES1_appended.txt`: a copy of `SPECIES1` with the cross-referenced data
    from `SPECIES2` appended to each line, and
  * `SPECIES2_appended.txt`: a copy of `SPECIES2` with the `SPECIES1` data appended.

Where there are multiple matching orthologs to a probe set ID, the data for each
match is appended onto a single line on the output.

Options:

    -h, --help  show this help message and exit
    --debug     Turn on debugging output
    --test      Run unit tests
