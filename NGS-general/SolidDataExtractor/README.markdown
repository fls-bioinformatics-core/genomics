SolidDataExtractor
==================
Utilities for analysing SOLiD runs, constructing analysis directories
and running QC pipeline.

There are 3 programs:

*   `analyse_solid_run.py`: report data about the samples and libraries
    from the run and write an entry for an XLS spreadsheet.

*   `build_analysis_dir.py`: automatically construct analysis directories for
    experiments which contain links to the primary data files.

*   `run_pipeline.py`: run a (QC) pipeline script via SGE's `qsub` command,
    to perform QC steps on each pairs of csfasta/qual data files in one or
    more analysis directories.

Each is used for a separate function and must be run independently. These are
built around some additional Python modules:

*   `SolidDataExtractor.py`: provides classes for reading data about a
    completed SOLiD run.

*   `Spreadsheet.py`: provides classes for constructing and appending to
    XLS spreadsheets. NB requires the `xlwt`, `xlrb` and `xlutils` Python
    libraries.

There are bash scripts to perform the QC:

*   `qc.sh`: given a csfasta and qual file pair, runs the QC pipeline
    (solid2fastq, fastq_screen and qc_boxplotter) on them.

*   `fastq_screen.sh`: given a fastq file, runs `fastq_screen` against
    three sets of genome indexes, specified by the following `.conf` files:

     * `fastq_screen_model_organisms.conf`
     * `fastq_screen_other_organisms.conf`
     * `fastq_screen_rRNA.conf`

    The location of the `.conf` files is set by the `FASTQ_SCREEN_CONF_DIR`
    variable in `qc.setup` (see below). This script is used by the main
    QC script to run the screens.

The QC scripts have an associated setup file called `qc.setup`, which
will be read automatically if it exists. Make a site-specific version by
copying `qc.setup.sample` and editing it as appropriate to specify
locations for the programs and data files.

Pipeline recipes
----------------

*   Run the full QC pipeline on a set of directories:

    `.../run_qc_pipeline.py qc.sh <dir1> <dir2> ...`

*   Run the fastq_screen steps only on a set of directories:

    `.../run_qc_pipeline.py --input=fastq fastq_screen.sh <dir1> <dir2> ...`
