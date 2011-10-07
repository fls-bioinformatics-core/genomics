NGS-general
===========

General NGS scripts that are used for both ChIP-seq and RNA-seq.

explain_sam_flag.sh
-------------------
Convert a decimal bitwise SAM flag value to binary representation and
interpret each bit.

qc_boxplotter
-------------
Generates a QC boxplot from a SOLiD .qual file.

Usage:

    qc_boxplotter.sh <solid.qual>

Outputs:

Two files (PostScript and PDF format) with the boxplot, called
`<solid.qual>_seq-order_boxplot.ps` and `<solid.qual>_seq-order_boxplot.pdf`

SamStats
--------
Counts how many reads are uniquely mapped onto each chromosome or
contig in a SAM file. To run:

java -classpath <dir_with_SamStats.class> SamStats <sam_file>

or (if using a Jar file):

java -cp /path/to/SamStats.jar SamStats <sam_file>

(To compile into a jar, do "jar cf SamStats.jar SamStats.class")

Output is a text file "SamStats_maponly_<sam_file>.stats"

splitBarcodes.pl
----------------
Split csfasta and qual files containing multiple barcodes into separate sets.

Usage:

    ./splitBarcodes.pl <barcode.csfasta> <read.csfasta> <read.qual>

Expects BC.csfasta, F3.csfasta and F3.qual files containing multiple barcodes.
Currently set up for 'BC Kit Module 1-16'.

Note that this utility also requires `BioPerl`.

SolidDataExtractor
------------------
Python modules for extracting data about a SOLiD run from the data in
the run directory.

- SolidDataExtractor.py: classes for data extraction, analysis and
  reporting of a SOLiD run.
  Can also be run as a stand-alone program:

  python SolidDataExtractor.py /path/to/solid/run/directory

- analyse_solid_run.py: use the SolidDataExtractor classes to analyse
  and report the layout, samples etc for a SOLiD run:

  python analyse_solid_run.py /path/to/solid/run/directory

- Spreadsheet.py: utility class to generate basic spreadsheet.
