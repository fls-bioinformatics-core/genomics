NGS-general
===========

General NGS scripts that are used for both ChIP-seq and RNA-seq.

  * `boxplotps2png.sh`: make PNGs of PS plots from `qc_boxplotter.sh`
  * `explain_sam_flag.sh`: decodes bit-wise flag from SAM file
  * `qc_boxplotter.sh`: generate QC boxplot from SOLiD qual file
  * `SamStats`: counts uniquely map reads per chromosome/contig
  * `splitBarcodes.pl`: separate multiple barcodes in SOLiD data
  * `remove_mispairs.pl`: remove "singleton" reads from paired end fastq
  * `remove_mispairs.py`: remove "singleton" reads from paired end fastq
  * `separate_paired_fastq.pl`: separate F3 and F5 reads from fastq
  * `trim_fastq.pl`: trim down sequences in fastq file from 5' end


boxplotps2png.sh
----------------
Utility to generate PNGs from PS boxplots produced from `qc_boxplotter.sh`.

Usage:

    boxplotps2png.sh BOXPLOT1.ps [ BOXPLOT2.ps ... ]

Outputs:

PNG versions of the input postscript files as BOXPLOT1.png, BOXPLOT2.png etc.


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

(To compile into a jar, do `jar cf SamStats.jar SamStats.class`)

Output is a text file "SamStats_maponly_<sam_file>.stats"


splitBarcodes.pl
----------------
Split csfasta and qual files containing multiple barcodes into separate sets.

Usage:

    ./splitBarcodes.pl <barcode.csfasta> <read.csfasta> <read.qual>

Expects BC.csfasta, F3.csfasta and F3.qual files containing multiple barcodes.
Currently set up for 'BC Kit Module 1-16'.

Note that this utility also requires `BioPerl`.


remove_mispairs.pl
------------------
Look through fastq file from solid2fastq that has interleaved paired end reads
and remove singletons (missing partner)

Usage:

    remove_mispairs.pl <interleaved FASTQ>

Outputs:

    <FASTQ>.paired: copy of input fastq with all singleton reads removed
    <FASTQ>.single.header: list of headers for all reads that were removed
       as singletons
    <FASTQ>.pair.header: list of headers for all reads there were kept as
       part of a pair


remove_mispairs.py
------------------
Python implementation of `remove_mispairs.pl` which can also remove singletons
for paired end fastq data file where the reads are not interleaved.


separate_paired_fastq.pl
------------------------
Takes a fastq file with paired F3 and F5 reads and separate into a file for
each.

Usage:

    separate_paired_fastq.pl <interleaved FASTQ>


trim_fastq.pl
-------------
Takes a fastq file and keeps the first (5') bases of the sequences specified
by the user.

Usage:

    trim_fastq.pl <single end FASTQ> <desired length>
