utils
=====

Place to put general utility scripts/tools.

cd_set_umask.sh
---------------
Script to set and revert a user's umask appropriately when moving in and out of a
particular directory (or one of its subdirectories).

do.sh
-----
Execute a command multiple times, substituting a range of integer index
values for each execution. For example:

    do.sh 1 43 ln -s /blah/blah#/myfile#.ext ./myfile#.ext

will execute:

ln -s /blah/blah1/myfile1.ext ./myfile1.ext
ln -s /blah/blah2/myfile2.ext ./myfile2.ext
...
ln -s /blah/blah43/myfile43.ext ./myfile43.ext


makeBinsFromBed.pl
------------------
Utility to to systematically and easily create feature 'bin' files, to be used in
binning applications.

Example use cases include defining a region 500bp in front of the tss, and making a
set of equally spaced intervals between the start and end of a gene or feature.

Usage:

    makeBinsFromBed.pl [options] BED_FILE OUTPUT_FILE

Options:

 *  `--marker [ midpoint | start | end | tss | tts ]`

    On which component of feature to position the bin(s) (default midpoint).
    `tss`: transcription start site (using strand)
    `tts`: transcription termination site (using strand)

 * `--binType [ centred | upstream | downstream ]`

    How to position the bin relative to the feature (default centred).
    If `marker` is `start`/`end`, position is relative to chromosome.
    If `marker` is `tss`/`tts`, position is relative to strand of feature

 *  `--offset n`

    All bins are shifted by this many bases (default 0).
    If `marker` is `start`/`end`, `n` is relative to chromosome.
    If `marker` is `tss`/`tts`, `n` is relative to strand of feature

 *  `--binSize n`

    The size of the bins (default 200)

 *  `--makeIntervalBins n`

    n bins are made of equal size within the feature.
    The bins begin, and are numbered from, the marker.
    If > 0, ignores binSize, offset and binType.
    Incompatible with `--marker midpoint`

*Tips:*

 *  To create single bp of the tss, use:

        --marker tss  --binSize 1 --binType downstream

 *  To get a bin of 1000bp ending 500bp upstream of the tss, use:

        --marker tss  --binSize 1000 --binType upstream --offset -500


makeRegularBinsFromGenomeTable.R
--------------------------------
Make a bed file with bins of size [binSize] filling every chrom specified in [Genome Table File]

Usage:

    makeRegularBinsFromGenomeTable.R [Genome Table File] [binSize]

Arguments:

 *  Genome Table File: name of a two-column tab-delimited file with chromosome name-start position
    information for each chromosome (i.e. the first two columns of the chromInfo table from UCSC).

 *  binSize: integer size of each bin (in bp) in the output file

Outputs:

 *  Bed file: same name as the genome table file with the extension `<binSize>.bp.bin.bed`,
    with each chromosome divided into bins of the requested size.
