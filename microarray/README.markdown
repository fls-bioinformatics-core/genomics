microarray
==========

Scripts and tools for microarray specific tasks.

  * `xrothologs.py`: cross-reference data for two species using probe set lookup


xrothologs.py
-------------

Usage:

    xrorthologs.py [options] LOOKUPFILE SPECIES1 SPECIES2

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
