QC utilities
============

Scripts for running general QC and data preparation on SOLiD and Illumina
sequencing data prior to library-specific analyses.

* :ref:`run_qc_pipeline`
* :ref:`qcreporter`
* :ref:`fastq_screen`
* :ref:`qc_boxplotter`: generate QC boxplot from SOLiD qual file
* :ref:`boxplotps2png`: make PNGs of PS plots from :ref:`qc_boxplotter`
* :ref:`solid_preprocess_filter`
* :ref:`solid_preprocess_truncation_filter`

.. _run_qc_pipeline:

run_qc_pipeline.py
******************

Overview
--------

The pipeline runner program ``run_qc_pipeline.py`` is designed to automate running
a specified script for all available datasets in one or more directories.

Datasets are assembled in an automated fashion by examining and grouping files in
a given directory based on their file names and file extensions. The specified
script is then run for each of the datasets, using the specified job runner to
handle execution and monitoring for each run. The master pipeline runner performs
overall monitoring, basic scheduling and reporting of jobs.

*   The ``--input`` and ``--regex`` options control the assembly of datasets
*   The ``--runner`` option controls which job runner is used
*   The ``--limit`` and ``--email`` options control scheduling and reporting

See below for more information on these options.

Usage and options
-----------------

Usage::

     run_qc_pipeline.py [options] SCRIPT DIR [ DIR ...]

Execute SCRIPT on data in each directory DIR. By default the ``SCRIPT`` is
executed on each CSFASTA/QUAL file pair found in ``DIR``, as ``SCRIPT CSFASTA
QUAL``. Use the --input option to run ``SCRIPT`` on different types of data (e.g.
FASTQ files). ``SCRIPT`` can be a quoted string to include command line options
(e.g. ``'run_solid2fastq.sh --gzip'``).

Basic Options:

.. cmdoption:: --limit=MAX_CONCURRENT_JOBS

    queue no more than ``MAX_CONCURRENT_JOBS`` at one time (default 4)
    
.. cmdoption:: --queue=GE_QUEUE

    explicitly specify Grid Engine queue to use

.. cmdoption:: --input=INPUT_TYPE

    specify type of data to use as input for the script. ``INPUT_TYPE`` can
    be one of: ``solid`` (CSFASTA/QUAL file pair, default), ``solid_paired_end``
    (CSFASTA/QUAL_F3 and CSFASTA/QUAL_F5 quartet), ``fastq`` (FASTQ file),
    ``fastqgz`` (gzipped FASTQ file)

.. cmdoption:: --email=EMAIL_ADDR

    send email to ``EMAIL_ADDR`` when each stage of the pipeline is complete

Advanced Options:

.. cmdoption:: --regexp=PATTERN

    regular expression to match input files against

.. cmdoption:: --test=MAX_TOTAL_JOBS

    submit no more than ``MAX_TOTAL_JOBS`` (otherwise submit all jobs)

.. cmdoption:: --runner=RUNNER

    specify how jobs are executed: ``ge`` = Grid Engine, ``drmma`` = Grid Engine
    via DRMAA interface, ``simple`` = use local system. Default is ``ge``

.. cmdoption:: --debug

    print debugging output

Recipes and examples
--------------------

* Run the full SOLiD QC pipeline on a set of directories::

    run_qc_pipeline.py solid_qc.sh <dir1> <dir2> ...

* Run the SOLiD QC pipeline on paired-end data::

    run_qc_pipeline.py --input=solid_paired_end solid_qc.sh <dir1> <dir2> ...

* Run the Illumina QC pipeline on fastq.gz files in a set of directories::

    run_qc_pipeline.py --input=fastqgz illumina_qc.sh <dir1> <dir2> ...

* Generate gzipped fastq files only in a set of directories::

    run_qc_pipeline.py "run_solid2fastq.sh --gzip" <dir1> <dir2> ...

* Run the fastq_screen steps only on a set of directories::

    run_qc_pipeline.py --input=fastq fastq_screen.sh <dir1> <dir2> ...

* Run the SOLiD preprocess filter steps only on a set of directories::

    run_qc_pipeline.py solid_preprocess_filter.sh <dir1> <dir2> ...

* To get an email notification on completion of the pipeline::

    run_qc_pipeline.py --email=foo@bar.com ...

Hints and tips
--------------

.. note::

    To run without using Grid Engine submission, specify ``--runner=simple``

This creates a ``qc`` subdirectory in ``DIR`` which contains the output QC
products from ``FastQC`` and ``fastq_screen``.

Useful additional options for ``run_qc_pipeline.py`` include:

 +----------------------+---------------------------------------------+
 | Option               | Function                                    |
 +======================+=============================================+
 | ``--limit=N``        | Specify maximum number of jobs that will be |
 |                      | submitted at one time (default is 4)        |
 +----------------------+---------------------------------------------+
 | ``--log-dir=DIR``    | Specify a directory to write log files to   |
 +----------------------+---------------------------------------------+
 | ``--ge_args=ARGS``   | Specify additional arguments to use with    |
 |                      | ``qsub``, for example:                      |
 |                      | ``--ge_args="-j y -l short"``               |
 +----------------------+---------------------------------------------+
 | ``--regexp=PATTERN`` | Specify a regular expression pattern; only  |
 |                      | filenames that match the pattern will have  |
 |                      | the QC script run on them                   |
 +----------------------+---------------------------------------------+

.. note::

    It is recommended to run ``run_qc_pipeline.py`` within a Linux ``screen`` session.

.. _qcreporter:

qcreporter.py
*************

Overview
--------

``qcreporter.py`` generates HTML reports for QC. It can be run on the outputs from
either ``solid_qc.sh`` or ``illumina_qc.sh`` scripts and will try to determine the
platform and run type automatically.

In some cases this automatic detection may fail, in which case the ``--platform``
and ``--format`` options can be used to explicit speciy the platform type and/or
the type of input files that are expected; see the section on "Reporting
recipes" below.

Usage and options
-----------------

Usage::

    qcreporter.py [options] DIR [ DIR ...]

Generate QC report for each directory ``DIR`` which contains the outputs from a QC
script (either SOLiD or Illumina). Creates a ``qc_report.<run>.<name>.html``
file in ``DIR`` plus an archive ``qc_report.<run>.<name>.zip`` which contains the
HTML plus all the necessary files for unpacking and viewing elsewhere.

Options:

.. cmdoption:: --platform=PLATFORM

    explicitly set the type of sequencing platform (``solid``, ``illumina``)

.. cmdoption:: --format=DATA_FORMAT

    explicitly set the format of files (``solid``, ``solid_paired_end``,
    ``fastq``, ``fastqgz``)

.. cmdoption:: --qc_dir=QC_DIR

    specify a different name for the QC results subdirectory (default is ``qc``)

.. cmdoption:: --verify

    don't generate report, just verify the QC outputs

.. cmdoption:: --regexp=PATTERN

    select subset of files which match regular expression ``PATTERN``



Reporting recipes
-----------------

The table below indicates the situations in which the reporter should work
automatically, and which options to use in cases when it doesn't:

    +-------------+------------+------------+-----------------------------+
    | Platform    | Data type  | QC mode    | Autodetect?                 |
    +=============+============+============+=============================+
    | SOLiD4      | Fragment   | Fragment   | Yes                         |
    +-------------+------------+------------+-----------------------------+
    | SOLiD4      | Paired-end | Fragment   | Yes                         |
    +-------------+------------+------------+-----------------------------+
    | SOLiD4      | Paired-end | Paired-end | Yes                         |
    +-------------+------------+------------+-----------------------------+
    | GA2x        | Fastq.gz   | n/a        | Yes                         |
    +-------------+------------+------------+-----------------------------+
    | GA2x        | Fastq      | n/a        | No: use --format=fastq      |
    +-------------+------------+------------+-----------------------------+
    | HiSEQ/MiSEQ | Fastq.gz   | n/a        | No: use --platform=illumina |
    +-------------+------------+------------+-----------------------------+
    | HiSEQ/MiSEQ | Fastq      | n/a        | No: use --platform=illumina |
    |             |            |            |         --format=fastq      |
    +-------------+------------+------------+-----------------------------+

.. _fastq_screen:

fastq_screen.sh
***************

The fastq_screen part of the QC pipeline is implemented as a shell script
fastq_screen.sh which can be run independently of the main qc.sh script. It
takes a single FASTQ file as input, e.g.::

    qsub -V -b Y -N fastq_screen -wd /path/to/dir/with/data fastq_screen.sh sample.fastq

This runs the ``fastq_screen`` program using three sets of genome indexes: common
"model" organisms (e.g. human, mouse, rat, fly etc), "other" organisms (e.g.
dictystelium), and a set of rRNa indexes.

Information on the ``fastq_screen`` program can be found at
http://www.bioinformatics.bbsrc.ac.uk/projects/fastq_screen/

The outputs are written to a ``qc`` subdirectory of the working directory, and consist
of a tab-file and a plot (in PNG format) for each screen indicating the percentage of
reads in the input which mapped against each genome. This acts as a check on whether
your sample contains what you expect, or whether it has contamination from other sources.

An example::

    Library	Unmapped	Mapped	Multi_mapped
    hg18	99.86	0.05	0.10
    mm9	99.79	0.04	0.17
    rn4	99.43	0.35	0.22
    dm3	99.86	0.00	0.14
    ws200	99.91	0.04	0.05
    ecoli	100.00	0.00	0.00
    saccer	39.63	54.42	5.95
    PhiX	100.00	0.00	0
    Vectors	99.87	0.11	0.02
    SpR6	100.00	0.00	0

which indicates that a large percentage of reads (~54%) mapped to 'C.elegans' (ws200).

.. _qc_boxplotter:

qc_boxplotter
*************

Generates a QC boxplot from a SOLiD .qual file.

Usage::

    qc_boxplotter.sh <solid.qual>

Outputs:

Two files (PostScript and PDF format) with the boxplot, called
``<solid.qual>_seq-order_boxplot.ps`` and
``<solid.qual>_seq-order_boxplot.pdf``, which indicate the quality
of the reads as a function of position.

Use :ref:`boxplotps2png` to convert the PS outputs to PNG.

.. _boxplotps2png:

boxplotps2png.sh
****************

Utility to generate PNGs from PS boxplots produced from :ref:`qc_boxplotter`.

Usage::

    boxplotps2png.sh BOXPLOT1.ps [ BOXPLOT2.ps ... ]

Outputs:

PNG versions of the input postscript files as ``BOXPLOT1.png``,
``BOXPLOT2.png`` etc.

.. note::

    This uses the ImageMagick ``convert`` program to do the image
    format conversion.

.. _solid_preprocess_filter:

solid_preprocess_filter.sh
**************************

The SOLiD_preprocess_filter part of the QC pipeline is implemented as a shell
script ``solid_preprocess_filter.sh``. which can be run independently of the main
``solid_qc.sh`` script. It takes a CSFASTA/QUAL file pair as input, e.g.::

    qsub -V -b Y -N solid_preprocess_filter -wd /path/to/dir/with/data solid_preprocess_filter.sh sample.csfasta sample.qual

and runs the ``SOLiD_preprocess_filter_v2.pl`` program on it.

The outputs are a "filtered" CSFASTA/QUAL file pair with the same name the inputs but
with ``_T_F3`` appended (e.g. for the example above they would be ``sample_T_F3.csfasta``
and ``sample_T_F3.qual``).

The script also runs a basic comparison of the input and output files to determine how
many reads were removed by the filtering process. This analysis is written to the log
file and also to a file called ``SOLiD_preprocess_filter.stats``, for example::

    #File	Reads	Reads after filter	Difference	% Filtered
    sample01.csfasta	82352	28252	54100	65.69
    sample02.csfasta	19479505	15510259	3969246	20.37
    sample03.csfasta	19816967	15501222	4315745	21.77
    sample04.csfasta	19581546	15293103	4288443	21.90
    ...

Typically around 20-30% of reads removed seems to be normal, anything much higher than
this suggests something unusual is going on.

By default the script uses a custom set of options. To replace these with your own
preferred set of options for ``SOLiD_preprocess_filter_v2.pl``, specify them as
arguments to the ``solid_preprocess_filter.sh`` script, e.g.::

    qsub -V -b Y -N solid_preprocess_filter -wd /path/to/dir/with/data solid_preprocess_filter.sh -q 3 -p 22 sample.csfasta sample.qual

Information on the ``SOLiD_preprocess_filter_v2.pl`` program can be found at
http://hts.rutgers.edu/filter/

.. _solid_preprocess_truncation_filter:

solid_preprocess_truncation_filter.sh
*************************************

This is a variation on the ``solid_preprocess_filter.sh`` script which truncates the
reads before applying the quality filter. It is not currently part of the QC pipeline
so it must be run independently. It takes a CSFASTA/QUAL file pair as input, e.g.::

    qsub -V -b Y -N solid_preprocess_filter -wd /path/to/dir/with/data solid_preprocess_truncation_filter.sh sample.csfasta sample.qual

By default the truncation length is 30 bp, but this can be changed by specifying the
``-u <length>`` option e.g. to use 35 bp do::


    qsub -V -b Y -N solid_preprocess_filter -wd /path/to/dir/with/data solid_preprocess_truncation_filter.sh -u 35 sample.csfasta sample.qual

By default the output files use the input CSFASTA file name as a base for the output
files, with the truncation length added (e.g. "sample_30bp"); to specify your own, use
the ``-o <basename>`` option e.g.::

    qsub -V -b Y -N solid_preprocess_filter -wd /path/to/dir/with/data solid_preprocess_truncation_filter.sh -o myoutput sample.csfasta sample.qual

The script outputs the following files:

* ``<basename>_T_F3.csfasta``
* ``<basename>_QV_T_F3.qual``
* ``<basename>_T_F3.fastq``

The script also writes statistics on the numbers of input/output reads to the
``SOLiD_preprocess_filter.stats`` file.

Other options supplied to the script are directly passed to the underlying
``SOLiD_preprocess_filter_v2.pl`` program
