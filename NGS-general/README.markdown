NGS-general
===========

General NGS scripts that are used for both ChIP-seq and RNA-seq.

  * `explain_sam_flag.sh`: decodes bit-wise flag from SAM file
  * `extract_reads.py`: write out subsets of reads from input data files
  * `fastq_edit.py`: edit FASTQ files and data
  * `fastq_sniffer.py`: "sniff" FASTQ file to determine quality encoding
  * `manage_seqs.py`: handling sets of named sequences (e.g. FastQC contaminants file)
  * `merge_regions.py`: discover overlapping regions (aka peaks) for time series data
  * `SamStats`: counts uniquely map reads per chromosome/contig
  * `splitBarcodes.pl`: separate multiple barcodes in SOLiD data
  * `remove_mispairs.pl`: remove "singleton" reads from paired end fastq
  * `remove_mispairs.py`: remove "singleton" reads from paired end fastq
  * `sam2soap.py`: convert from SAM file to SOAP format
  * `separate_paired_fastq.pl`: separate F3 and F5 reads from fastq
  * `split_fasta.py`: extract individual chromosome sequences from fasta file
  * `trim_fastq.pl`: trim down sequences in fastq file from 5' end
  * `uncompress_fastqgz.sh`: create ungzipped version of a compressed FASTQ file


explain_sam_flag.sh
-------------------
Convert a decimal bitwise SAM flag value to binary representation and
interpret each bit.


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


fastq_sniffer.py
----------------

Usage: `fastq_sniffer.py <fastq_file>`

"Sniff" FASTQ file to try and determine likely format and quality encoding.

Attempts to identify FASTQ format and quality encoding, and suggests likely datatype
for import into Galaxy.

Use the `--subset` option to only use a subset of reads from the file for the type
determination (using a smaller set speeds up the process at the risk of not being able
to accuracy determine the encoding convention).

See [http://en.wikipedia.org/wiki/FASTQ_format]() for information on the different
quality encoding standards used in different FASTQ formats.

Options:

    --version          show program's version number and exit
    -h, --help         show this help message and exit
    --subset=N_SUBSET  try to determine encoding from a subset of consisting of
                       the first N_SUBSET reads. (Quicker than using all reads
                       but may not be accurate if subset is not representative
                       of the file as a whole.)


manage_seqs.py
--------------

Read sequences and names from one or more INFILEs (which can be a mixture of
FastQC 'contaminants' format and or Fasta format), check for redundancy (i.e.
sequences with multiple associated names) and contradictions (i.e. names with
multiple associated sequences).

Usage:

    manage_seqs.py OPTIONS FILE [FILE...]

To append a 

Options:

    --version       show program's version number and exit
    -h, --help      show this help message and exit
    -o OUT_FILE     write all sequences to OUT_FILE in FastQC 'contaminants'
                    format
    -a APPEND_FILE  append sequences to existing APPEND_FILE (not compatible
                    with -o)
    -d DESCRIPTION  supply arbitrary text to write to the header of the output
                    file

Intended to help create/update files with lists of "contaminant" sequences to
input into the `FastQC` program (using `FastQC`'s `--contaminants` option).

To create a contaminants file using sequences from a FASTA file do e.g.:

    % manage_seqs.py -o custom_contaminants.txt sequences.fa

To append sequences to an existing contaminants file do e.g.

    % manage_seqs.py -a my_contaminantes.txt additional_seqs.fa

merge_regions.py
----------------
Program that discovers overlapping regions (aka peaks) for time series
data supplied in a tab delimited file, and reports the sets of overlapped
regions.

Depending on the mode it also reports either a "merged" region (i.e. a
region that is large enough to encompass all the overlapped peaks), or
a "best" region (i.e. the peak in the set which has the highest
normalized tag count).

Usage:

    merge_regions.py [--mode MODE] [OPTIONS] PEAKS_FILE THRESHOLD ATTR

where `MODE` can be one of `merge`, `merge_hybrid` or `best`.

`PEAKS_FILE in a tab delimited input file with one region per line,
with the following columns:

    CHR START END PEAK_ID STRAND TAG_COUNT ... TIME_POINT

where:

    CHR   = chromomsome
    START = start position
    END   = end position
    PEAK_ID = name for each peak
    STRAND = strand (+ or -)
    TAG_COUNT = normalized tag count

The last column should be the time point index.

 *  **merge mode**: overlapping regions are merged together into a
    single region which covers all regions in the overlap.
    Output in `merge` mode is:

        CHR START END N_OVERLAPS FLAG PEAK_LIST

 * **merge_hybrid mode**: this is the same as 'merge', but the
   highest score from the overlapping set is also output. Output in
   `merge_hybrid` mode is:

        CHR START END SCORE N_OVERLAPS FLAG PEAK_LIST

 * **best mode**: only the region with the highest score of all
   those in the overlapping set is kept. Output in `best` mode is:

        CHR START END N_OVERLAPS FLAG BEST_PEAK PEAK_LIST

`N_OVERLAPS` is the number of overlapping peaks (zero if there
were no overlaps).

`FLAG` is either `no_overlap` (the peak didn't overlap any others),
`normal` (overlaps with no more than one peak from each time point),
or `time_split_full` (overlaps with more than one peak for a single
time point).

`PEAK_LIST` is a comma-delimited list of region ids.

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


uncompress_fastqz.sh
--------------------
Create uncompressed copies of fastq.gz file (if input is fastq.gz).

Usage:

    uncompress_fastqgz.sh <fastq>

`<fastq>` can be either fastq or fastq.gz file.

The original file will not be removed or altered.
