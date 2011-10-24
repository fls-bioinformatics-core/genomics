QC-pipeline
===========

Scripts and utilities for running QC pipelines on SOLiD data.

There is a core pipeline runner program:

*   `run_pipeline.py`: run a (QC) pipeline script via SGE's `qsub` command,
    to perform QC steps on each pairs of csfasta/qual data files in one or
    more analysis directories.

There are bash scripts to perform the QC and specific substeps:

*   `qc.sh`: given a csfasta and qual file pair, runs the QC pipeline
    (solid2fastq, fastq_screen, solid_preprocess_filter and qc_boxplotter).

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

*   `filter_stats.sh`: appends statistics comparing original SOLiD data files
    with the output from the preprocess filter step to a log file.

Setup
-----

The QC scripts have an associated setup file called `qc.setup`, which
will be read automatically if it exists. Make a site-specific version by
copying `qc.setup.sample` and editing it as appropriate to specify
locations for the programs and data files.

Pipeline recipes
----------------

*   Run the full QC pipeline on a set of directories:

    `run_qc_pipeline.py qc.sh <dir1> <dir2> ...`

*   Run the fastq_screen steps only on a set of directories:

    `run_qc_pipeline.py --input=fastq fastq_screen.sh <dir1> <dir2> ...`

*   Run the preprocess filter steps only on a set of directories:

    `run_qc_pipeline.py solid_preprocess_filter.sh <dir1> <dir2> ...`

*   To get an email notification on completion of the pipeline:

    `run_qc_pipeline.py --email=foo@bar.com ...`
