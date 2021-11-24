ChIP-seq (legacy)
=================

Deprecated scripts and tools for ChIP-seq specific tasks.

calc_coverage_stats.pl
----------------------
Get stats for coverage using a coverage file from genomeCoverageBed -d

Format of the input is: `chr position count`

Outputs mean and median for all positions including 0 count positions

NB requires perl `Statistics::Descriptive` module

convertFastq2Fasta.pl
---------------------
Convert fastq formatted consensus from `samtools pileup` to fasta

*Note that this will be redundant as mpileup (the successor to pileup) has its own way of
doing this. However it may be required for legacy projects.*

Usage:

`perl ~/ChIP_seq/convertFastq2Fasta.pl in.pileup.fq > out.fa`

CreateChIPalignFileFromBed.pl
-----------------------------
Convert csfasta->BED format file to ChIPalign format for GLITR peak caller.

Usage:

`CreateChIPalignFileFromBed.pl in.bed out.align`

getRandomTags_index.pl/getRandomTags_index_fastq.pl
---------------------------------------------------
Extract random subset of records from fasta and fastq sequence files.

### getRandomTags_index.pl ###

Extract N random records from ChIP align fasta files (2-line records):

Usage: `getRandomTags_index.pl in.fasta N out.fast`

### getRandomTags_index_fastq.pl ###

Extract N random records from fastq file (4-line records):

Usage: `getRandomTags_index_fastq.pl in.fastq N out.fastq`

mean_coverage.pl
----------------
Mean depth of read coverage: calculates the average coverage of all the captured bases in a
bam file and presents as a single number.

Originally posted by Michael James Clark on Biostar:
[http://biostar.stackexchange.com/questions/5181/tools-to-calculate-average-coverage-for-a-bam-file]()

Usage:

`/path/to/samtools pileup in.bam | awk '{print $4}' | perl mean_coverage.pl`

It can also be used for genomic regions:

`/path/to/samtools view -b in.bam <genomic region> | /path/to/samtools pileup - | awk '{print $4}' | perl mean_coverage.pl`

Note that this assumes every base is covered at least once (because samtools pileup doesn't
report bases with zero coverage).

run_DESeq.R
-----------
Usage:

`runDESeq.R [input file] [generic figure label] [output file]`

Run DESeq in R using a tab delimited file [input file] that has a column of
chr_start_end called 'regions' and four columns of read counts for:

`timeA_rep1 timeA_rep2 timeB_rep1 timeB_rep2`

('conds' order hard-wired).

A [generic figure label] adds specificity to the output diagrams (hard-wired).
The final [output file] is created.