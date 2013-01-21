utils
=====

Place to put general utility scripts/tools.

 *  `annotate_probesets.py`: annotate probe set list based on probe set names
 *  `cd_set_umask.sh`: setup script to automagically set umask for specific directory
 *  `do.sh`: execute shell command iteratively with range of integer index values
 *  `extract_reads.py`: write out subsets of reads from input data files
 *  `fastq_edit.py`: edit FASTQ files and data
 *  `makeBinsFromBed.pl`: create bin files for binning applications
 *  `makeRegularBinsFromGenomeTable.R`: make bin file from set of chromosomes
 *  `make_mock_solid_dir.py`: create mock SOLiD directory structure for testing
 *  `md5checker.py`: check files and directories using MD5 sums
 *  `sam2soap.py`: convert from SAM file to SOAP format
 *  `split_fasta.py`: extract individual chromosome sequences from fasta file
 *  `symlink_checker.py`: check and update symbolic links

See below for more detailed usage documentation.

annotate_probeset.py
--------------------

Usage: `annotate_probesets.py OPTIONS probe_set_file`

Annotate a probeset list based on probe set names: reads in first column of
tab-delimited input file 'probe_set_file' as a list of probeset names and outputs
these names to another tab-delimited file with a description for each. Output file name
can be specified with the -o option, otherwise it will be the input file name with
'_annotated' appended.

Options:

    --version    show program's version number and exit
    -h, --help   show this help message and exit
    -o OUT_FILE  specify output file name

Example input:

    ...
    1769726_at
    1769727_s_at
    ...

generates output:

    ...
    1769726_at	Rank 1: _at : anti-sense target (most probe sets on the array)
    1769727_s_at	Warning: _s_at : designates probe sets that share common probes among multiple transcripts from different genes
    ...

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


extract_reads.py
----------------

Usage: `extract_reads.py OPTIONS infile [infile ...]`

Extract subsets of reads from each of the supplied files according to
specified criteria (e.g. random, matching a pattern etc). Input files can be
any mixture of FASTQ (.fastq, .fq), CSFASTA (.csfasta) and QUAL (.qual).
Output file names will be the input file names with '.subset' appended.

Options:

    --version             show program's version number and exit
    -h, --help            show this help message and exit
    -m PATTERN, --match=PATTERN
                          Extract records that match Python regular expression
                          PATTERN
    -n N                  Extract N random records from the input file(s)
                          (default 500). If multiple input files are specified,
                          the same subsets will be extracted for each.


fastq_edit.py
-------------

Usage: `fastq_edit.py [options] <fastq_file>`

Perform various operations on FASTQ file.
Options:

    --version             show program's version number and exit
    -h, --help            show this help message and exit
    --stats               Generate basic stats for input FASTQ
    --instrument-name=INSTRUMENT_NAME
                          Update the 'instrument name' in the sequence
                          identifier part of each read record and write updated
                          FASTQ file to stdout

makeBinsFromBed.pl
------------------
Utility to systematically and easily create feature 'bin' files, to be used in
binning applications.

Example use cases include defining a region 500bp in front of the tss, and making a
set of equally spaced intervals between the start and end of a gene or feature.

Usage:

    makeBinsFromBed.pl [options] BED_FILE OUTPUT_FILE

Options:

    --marker [ midpoint | start | end | tss | tts ]
        On which component of feature to position the bin(s) (default midpoint).
	    tss: transcription start site (using strand)
	    tts: transcription termination site (using strand)	

    --binType [ centred | upstream | downstream ]
	    How to position the bin relative to the feature (default centred).
	    If marker is start/end, position is relative to chromosome. 
	    If marker is tss/tts, position is relative to strand of feature	
        
    --offset n
	    All bins are shifted by this many bases (default 0).
	    If marker is start/end, n is relative to chromosome. 
	    If marker is tss/tts, n is relative to strand of feature

    --binSize n
	   The size of the bins (default 200)
	
    --makeIntervalBins n
	   n bins are made of equal size within the feature. 
	   The bins begin, and are numbered from, the marker.
	   If > 0, ignores binSize, offset and binType.
	   Incompatible with --marker midpoint 

*Tips:*

    To create single bp of the tss, use:  
		--marker tss  --binSize 1 --binType downstream
        
	To get a bin of 1000bp ending 500bp upstream of the tss, use: 
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


make_mock_solid_dir.py
----------------------
Make a temporary mock SOLiD directory structure that can be used for testing.

Usage:

    make_mock_solid_dir.py [OPTIONS]

Arguments:

    --paired-end          Create directory structure for paired-end run


md5checker.py
-------------
Utility for checking files and directories using MD5 checksums.

Usage:

To generate MD5 sums for a directory:

    md5checker.py [ -o CHKSUM_FILE ] DIR

To generate the MD5 sum for a file:

    md5checker.py [ -o CHKSUM_FILE ] FILE

To check a set of files against MD5 sums stored in a file:

    md5checker.py -c CHKSUM_FILE

To compare the contents of source directory recursively against the contents of a destination
directory, checking that files in the source are present in the target and have the same MD5
sums:

    md5checker.py --diff SOURCE_DIR DEST_DIR

To compare two files by their MD5 sums:

    md5checker.py --diff FILE1 FILE2


sam2soap.py
-----------
Convert a SAM file into SOAP format.

Usage:

    sam2soap.py OPTIONS [ SAMFILE ]

Convert SAM file to SOAP format - reads from stdin (or SAMFILE, if specified),
and writes output to stdout unless -o option is specified.

Options:

    -o SOAPFILE  Output SOAP file name
    --debug      Turn on debugging output
    --test       Run unit tests


split_fasta.py
--------------
Extract individual chromosome sequences from a fasta file.

Usage:

    split_fasta.py OPTIONS fasta_file

Split input FASTA file with multiple sequences into multiple files each
containing sequences for a single chromosome.

Options:

    --version   show program's version number and exit
    -h, --help  show this help message and exit
    --tests     Run unit tests

For each chromosome CHROM found in the input Fasta file (delimited by a line
`>CHROM`), outputs a file called `CHROM.fa` in the current directory
containing just the sequence for that chromosome.


symlink_checker.py
------------------
Check and update symbolic links.

Usage:

    symlink_checker.py OPTIONS DIR

Recursively check and optionally update symlinks found under directory DIR

Options:

    --version             show program's version number and exit
    -h, --help            show this help message and exit
    --broken              report broken symlinks
    --find=REGEX_PATTERN  report links where the destination matches the
                          supplied REGEX_PATTERN
    --replace=NEW_STRING  update links found by --find options, by substituting
                          REGEX_PATTERN with NEW_STRING
