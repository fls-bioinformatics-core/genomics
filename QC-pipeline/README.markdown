QC-pipeline
===========

Scripts and utilities for running QC pipelines on SOLiD data.

There is a core pipeline runner program:

*   `run_pipeline.py`: run a (QC) pipeline script via SGE's `qsub` command,
    to perform QC steps on each pairs of csfasta/qual data files in one or
    more analysis directories.

The core QC script is:

*   `qc.sh`: given a csfasta and qual file pair, runs the QC pipeline
    (solid2fastq, fastq_screen, solid_preprocess_filter and qc_boxplotter).

There are other scripts which perform QC substeps:

*   `run_solid2fastq.sh`: given a csfasta and qual file pair, generates a
    fastq file by running the `solid2fastq` program.

*   `fastq_screen.sh`: given a fastq file, runs `fastq_screen` against
    three sets of genome indexes, specified by the following `.conf` files:

     * `fastq_screen_model_organisms.conf`
     * `fastq_screen_other_organisms.conf`
     * `fastq_screen_rRNA.conf`

    The location of the `.conf` files is set by the `FASTQ_SCREEN_CONF_DIR`
    variable in `qc.setup` (see below). This script is used by the main
    QC script to run the screens.

*   `solid_preprocess_filter.sh`: given a csfasta and qual file pair, runs
    `SOLiD_preprocess_filter_v2.pl` and outputs the filtered csfasta and qual
    files.

*   `solid_preprocess_truncate_filter.sh`: similar to `solid_preprocess_filter.sh`,
    but performs the truncation step separately from the filtering.

*   `filter_stats.sh`: appends statistics comparing original SOLiD data files
    with the output from the preprocess filter step to a log file.

These also use `functions.sh` and `ngs_utils.sh` from the `share` directory.

Setup
-----

The QC scripts have an associated setup file called `qc.setup`, which
will be read automatically if it exists. Make a site-specific version by
copying `qc.setup.sample` and editing it as appropriate to specify
locations for the programs and data files.

Outputs
-------

For each sample the following output files will be produced by `qc.sh`:

### "Fragment" mode (default) ###

Say that the input SOLiD data file pair is `PB.csfasta` and `PB.qual`, then the
following FASTQ files are produced:

 * `PB.fastq`: all reads
 * `PB_T_F3.csfasta` and `PB_T_F3_QV.qual`: primary data after quality filtering
 * `PB_T_F3.fastq`: reads after quality filtering

### Paired-end mode ###

Say that the input SOLiD data file pairs are `PB_F3.csfasta`, `PB_F3.qual` and
`PB_F5.csfasta`, `PB_F5.qual`, then the following FASTQ files are produced:

#### Unfiltered data ####

Merging all the original unfiltered data into a single fastq gives:

 * `PB_paired.fastq`: all unfiltered F3 and F5 data merged into a single fastq
 * `PB_paired.F3.fastq`: unfiltered F3 data
 * `PB_paired.F5.fastq`: unfiltered F5 data

#### Quality filtered data ####

Quality filtering on the primary data gives:

 * `PB_F3_T_F3.csfasta` and `PB_F3_T_F3_QV.qual`: F3 data after quality filter
 * `PB_F5_T_F3.csfasta` and `PB_F5_T_F3_QV.qual`: F5 data after quality filter

(Note that the files with `F5` in the name only have F5 reads - ignore the `F3`
part of `T_F3`.)

"Lenient" filtering and merging the F3 filtered data with all F5 gives:

 * `PB_paired_F3_filt.fastq`: filtered F3 reads with the matching F5 partner
 * `PB_paired_F3_filt.F3.fastq`: just the F3 reads after filtering
 * `PB_paired_F3_filt.F5.fastq`: just the matching F5 partners

(This is called "lenient" as only the quality of the F3 reads is considered.)

"Strict" filtering and merging gives:

 * `PB_paired_F3_and_F5_filt.fastq`: filtered F3 reads and filtered F5 reads,
   with "unpartnered" reads removed
 * `PB_paired_F3_and_F5_filt.F3.fastq`: just the F3 reads
 * `PB_paired_F3_and_F5_filt.F5.fastq`: just the F5 reads

(This is called "strict" filtering as a pair of reads will be rejected on the
quality of either of the F3 or F5 components.)

### Contamination screens (`fastq_screen`) ###

Contamination screen outputs are written to the `qc` directory:

 * `PB_model_organisms_screen.*`: screen against a selection of commonly used genomes
 * `PB_other_organisms_screen.*`: screen against a selection of less common genomes
 * `PB_rRNA_screen.*`: screen against a selection of rRNAs

For each there are `.txt` and `.png` files.

### Boxplots ###

Boxplots are written to the `qc` subdirectory:

 * `PB.qual_seq-order_boxplot.*`: plot using all reads (PDF, PNG and PS formats)
 * `PB_T_F3_QV.qual_seq-order_boxplot.*`: plot using just the quality filtered reads

Pipeline recipes/examples
-------------------------

*   Run the full QC pipeline on a set of directories:

    `run_qc_pipeline.py qc.sh <dir1> <dir2> ...`

*   Generate gzipped fastq files only in a set of directories:

    `run_qc_pipeline.py "run_solid2fastq.sh --gzip" <dir1> <dir2> ...`

*   Run the fastq_screen steps only on a set of directories:

    `run_qc_pipeline.py --input=fastq fastq_screen.sh <dir1> <dir2> ...`

*   Run the preprocess filter steps only on a set of directories:

    `run_qc_pipeline.py solid_preprocess_filter.sh <dir1> <dir2> ...`

*   To get an email notification on completion of the pipeline:

    `run_qc_pipeline.py --email=foo@bar.com ...`
