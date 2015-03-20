QC-pipeline
===========

Pipeline runner: run_qc_pipeline.py
***********************************

Overview
--------

The pipeline runner program `run_qc_pipeline.py` is designed to automate running
a specified script for all available datasets in one or more directories.

Datasets are assembled in an automated fashion by examining and grouping files in
a given directory based on their file names and file extensions. The specified
script is then run for each of the datasets, using the specified job runner to
handle execution and monitoring for each run. The master pipeline runner performs
overall monitoring, basic scheduling and reporting of jobs.

*   The `--input` and `--regex` options control the assembly of datasets
*   The `--runner` option controls which job runner is used
*   The `--limit` and `--email` options control scheduling and reporting

See below for more information on these options.

Usage and options
-----------------

Usage::

     run_qc_pipeline.py [options] SCRIPT DIR [ DIR ...]

Execute SCRIPT on data in each directory DIR. By default the SCRIPT is
executed on each CSFASTA/QUAL file pair found in DIR, as 'SCRIPT CSFASTA
QUAL'. Use the --input option to run SCRIPT on different types of data (e.g.
FASTQ files). SCRIPT can be a quoted string to include command line options
(e.g. 'run_solid2fastq.sh --gzip').

Options:

    -h, --help            show this help message and exit

Basic Options:

    --limit=MAX_CONCURRENT_JOBS
                        queue no more than MAX_CONCURRENT_JOBS at one time
                        (default 4)
    --queue=GE_QUEUE    explicitly specify Grid Engine queue to use
    --input=INPUT_TYPE  specify type of data to use as input for the script.
                        INPUT_TYPE can be one of: 'solid' (CSFASTA/QUAL file
                        pair, default), 'solid_paired_end' (CSFASTA/QUAL_F3
                        and CSFASTA/QUAL_F5 quartet), 'fastq' (FASTQ file),
                        'fastqgz' (gzipped FASTQ file)
    --email=EMAIL_ADDR  send email to EMAIL_ADDR when each stage of the
                        pipeline is complete

Advanced Options:

    --regexp=PATTERN    regular expression to match input files against
    --test=MAX_TOTAL_JOBS
                        submit no more than MAX_TOTAL_JOBS (otherwise submit
                        all jobs)
    --runner=RUNNER     specify how jobs are executed: ge = Grid Engine, drmma
                        = Grid Engine via DRMAA interface, simple = use local
                        system. Default is 'ge'
    --debug             print debugging output


Reporting: qcreporter.py
************************

Overview
--------

`qcreporter.py` generates HTML reports for QC. It can be run on the outputs from
either `solid_qc.sh` or `illumina_qc.sh` scripts and will try to determine the
platform and run type automatically.

In some cases this automatic detection may fail, in which case the `--platform`
and `--format` options can be used to explicit speciy the platform type and/or
the type of input files that are expected; see the section on "Reporting
recipes" below.

Usage and options
-----------------

Usage::

    qcreporter.py [options] DIR [ DIR ...]

Generate QC report for each directory DIR which contains the outputs from a QC
script (either SOLiD or Illumina). Creates a 'qc_report.<run>.<name>.html'
file in DIR plus an archive 'qc_report.<run>.<name>.zip' which contains the
HTML plus all the necessary files for unpacking and viewing elsewhere.

Options:

    -h, --help            show this help message and exit
    --platform=PLATFORM   explicitly set the type of sequencing platform
                          ('solid', 'illumina')
    --format=DATA_FORMAT  explicitly set the format of files ('solid',
                          'solid_paired_end', 'fastq', 'fastqgz')
    --qc_dir=QC_DIR       specify a different name for the QC results
                          subdirectory (default is 'qc')
    --verify              don't generate report, just verify the QC outputs
    --regexp=PATTERN      select subset of files which match regular expression
                          PATTERN
