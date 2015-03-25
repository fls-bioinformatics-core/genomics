QC Protocols
============

QC for Illumina sequencing data
*******************************

The full QC pipeline for Illumina data (GA2x, MiSEQ and HiSEQ sequencers) is
encoded in the ``illumina_qc.sh`` script.

This can be run for a set of Illumina ``fastq`` or ``fastq.gz`` format files
in a specific directory using the ``run_qc_pipeline.py`` command. In its
simplest form::

    run_qc_pipeline.py --input=FORMAT illumina_qc.sh DIR

``FORMAT`` can be either ``fastq`` or ``fastqgz``; this will detect all matching
files in the directory ``DIR`` and then use ``qsub`` to submit Grid Engine jobs
to run the QC script on each file.

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

To verify that the QC has worked, run the ``qcreporter.py`` command::

    qcreporter.py --platform=illumina --format=FORMAT --verify DIR 

and to generate the HTML QC report::


    qcreporter.py --platform=illumina --format=FORMAT DIR

QC for SOLiD sequencing data
****************************

The full QC pipeline for SOLiD data is encoded in the ``solid_qc.sh`` script.
It runs in either "fragment mode", which takes a CSFASTA/QUAL file pair as input,
or in "paired-end mode", which takes two CSFASTA/QUAL file pairs as input (the
first should be the F3 pair and the second the corresponding F5 pair).

This can be run in either mode for a set of SOLiD data files in a specific
directory using the ``run_qc_pipeline.py`` command. In its simplest form, for
"fragment" (F3) data::


    run_qc_pipeline.py --input=solid solid_qc.sh DIR

or for paired-end (F3/F5) data::

    run_qc_pipeline.py --input=solid_paired_end solid_qc.sh DIR

In each case this will detect all matching file groups in the directory ``DIR``
and then use ``qsub`` to submit Grid Engine jobs to run the QC script on each group.

The pipeline consists of:

* ``solid2fastq``: creates a FASTQ file from the input CSFASTA/QUAL file pair
* ``fastq_screen``: checks the reads against 3 different screens (model organisms,
  "other" organisms and rRNA) to look for contaminants
* ``solid_preprocess_filter``: runs the ``SOLiD_prepreprocess_filter_v2.pl`` program
  on the input CSFASTA/QUAL file pair to filter out "bad" reads, and reports the
  percentage filtered out (also produces a FASTQ and boxplot for the filtered data)
* ``qc_boxplotter``: generates quality-score boxplots from the input QUAL file

The main outputs are the FASTQ file and a subdirectory ``qc`` which holds the screen
and boxplot files.

(See the section above on "Illumina QC" for additional options available for
``run_qc_pipeline.py``.)

To verify that the QC has worked, run the ``qcreporter.py`` command::

    qcreporter.py --platform=solid --format=FORMAT --verify DIR 

(where ``FORMAT`` is either ``solid`` or ``solid_paired_end``), and to generate the
HTML QC report::

    qcreporter.py --platform=solid --format=FORMAT DIR 

General information on QC scripts
*********************************

These automatically run a series of checks and data preparation steps on the data
prior to any real analysis taking place.

Both QC scripts read their settings from the ``qc.setup`` file, which tells them
where to find some of the underlying software and data files. This is already set
up for the cluster, and is in the same directory as the scripts themselves (do e.g.
``which illumina_qc.sh`` to find this location).

Some of the pipeline components can also be run independently (e.g.
``qc_boxplotter.sh``, ``fastq_screen.sh``, ``solid_preprocess_filter.sh``) - see
the following sections.

Note that the QC script won't overwrite outputs from a previous run; if you want to
regenerate the outputs then you'll need to remove the previous outputs first.

Specific QC scripts
*******************

Contamination screening: fastq_screen.sh
----------------------------------------

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

Quality boxplots: qc_boxplotter.sh
----------------------------------

The boxplotter takes a SOLiD QUAL file as input, e.g.::

    qsub -V -b Y -N qc_boxplotter -wd /path/to/dir/with/data qc_boxplotter.sh sample.qual

The outputs are a boxplot (in both Postscript and PDF formats) indicating the quality of
the reads as a function of position.

SOLiD preprocess filter: solid_preprocess_filter.sh
---------------------------------------------------

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

SOLiD preprocess truncate/filter: solid_preprocess_truncation_filter.sh
-----------------------------------------------------------------------

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

Outputs from QC pipeline
************************

SOLiD paired-end data outputs
-----------------------------

Say that the input files are ``PB_F3.csfasta``, ``PB_F3.qual`` and ``PB_F5.csfasta``,
``PB_F5.qual``.

 +------------+---------------------------------------+------------------------------------+---------------------+
 | Stage      | Files                                 | Description                        | Comments            |
 +============+=======================================+====================================+=====================+
 | Quality    | ``PB_F3_T_F3.csfasta``,               | F3 data after                      |                     |
 | filtering  | ``PB_F3_T_F3_QV.qual``                | quality filter                     |                     |
 +------------+---------------------------------------+------------------------------------+---------------------+
 |            | ``PB_F5_T_F3.csfasta``,               | F5 data after                      | Only has F5 reads:  |
 |            | ``PB_F5_T_F3_QV.qual``                | quality filter                     | ignore the F3 part  |
 |            |                                       |                                    | of "T_F3"           |
 +------------+---------------------------------------+------------------------------------+---------------------+
 | Merge      | ``PB_paired.fastq``                   | All unfiltered                     | Used for            |
 | unfiltered |                                       | F3 and F5 data in                  | fastq_screen        |
 |            |                                       | one fastq file                     |                     |
 +------------+---------------------------------------+------------------------------------+---------------------+
 | Merge F3   | ``PB_paired_F3_filt.fastq``           | Filtered F3 reads                  | "Lenient" filtering:|
 | filtered   |                                       | with the matching                  | only the quality of |
 |            |                                       | F5 partner                         | the F3 reads is     |
 |            |                                       |                                    | considered          |
 +------------+---------------------------------------+------------------------------------+---------------------+
 | Merge all  | ``PB_paired_F3_and_F5_filt.fastq``    | Filtered F3 reads                  | "Strict" filtering: |
 | filtered   |                                       | and filtered F5                    | pairs of reads are  |
 |            |                                       | reads                              | rejected on the     |
 |            |                                       |                                    | quality of either   |
 |            |                                       |                                    | of the F3 or F5     |
 |            |                                       |                                    | components          |
 +------------+---------------------------------------+------------------------------------+---------------------+
 | Split      | ``PB_paired_F3_filt.F3.fastq``        | F3 reads only                      | Data to use for     |
 | FASTQs     |                                       | from                               | mapping             |
 |            |                                       | ``PB_paired_F3_filt.fastq``        |                     |
 +------------+---------------------------------------+------------------------------------+---------------------+
 |            | ``PB_paired_F3_filt.F5.fastq``        | F5 reads only from                 |                     |
 |            |                                       | ``PB_paired_F3_filt.fastq``        |                     |
 +------------+---------------------------------------+------------------------------------+---------------------+
 |            | ``PB_paired_F3_and_F5_filt.F3.fastq`` | F3 reads only from                 | Data to use for     |
 |            |                                       | ``PB_paired_F3_and_F5_filt.fastq`` | mapping             |
 +------------+---------------------------------------+------------------------------------+---------------------+
 |            | ``PB_paired_F3_and_F5,filt.F5.fastq`` | F5 reads only from                 |                     |
 |            |                                       | ``PB_paired_F3_and_F5_filt.fastq`` |                     |
 +------------+---------------------------------------+------------------------------------+---------------------+

