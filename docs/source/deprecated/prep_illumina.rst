Preparing Illumina Data for analysis
====================================

FASTQ generation and analysis directory setup
*********************************************

Overview
--------

This section outlines the protocol for generating FASTQ files from the
raw bcl data and setting up per-project analysis directories using the
scripts and utilities included in this package.

The basic procedure is:

1. Create top-level analysis directory
2. Generate FASTQ files
3. Populate analysis subdirectories for each project

Subsequently the QC pipeline should be run for each project.

Create top-level analysis directory
-----------------------------------

Create a top-level analysis directory where the FASTQs and per-project
analysis directories will be created, for example::

    mkdir /scratch/120919_SN7001250_0035_BC133VACXX_analysis

.. note::

    Conventionally we name analysis directories by appending ``_analysis``
    to the primary data directory name.

FASTQ generation
----------------

Within the top-level directory create a customised copy of the original
``SampleSheet.csv`` from the primary data directory. This is best done
using the :ref:`prep_sample_sheet` utility, as it will automatically
convert the original file to the correct format.

``prep_sample_sheet.py`` can automatically address specific issues, for
example:

.. cmdoption:: --fix-spaces

    replaces spaces in sampleId and sampleProject fields with underscore
    characters

.. cmdoption:: --fix-duplicates

    appends indices to sampleIds to make sampleId/sampleProject
    combinations unique 

These two options together should automatically fix most problems with
sample sheets, e.g.::

    prep_sample_sheet.py \
        --fix-spaces --fix-duplicates \
        -o custom_samplesheet.csv \
        /mnt/data/120919_SN7001250_0035_BC133VACXX/SampleSheet.csv

It also has options to edit the sample sheet file fields: for example the
``--set-id=...`` and ``--set-project=`` options allow resetting of sampleId
and sampleProject fields.

.. note::

    ``prep_sample_sheet.py`` will only write a new sample sheet file if
    it thinks that the problems have been addressed; to override this use
    the ``--ignore-warnings`` option.

To generate FASTQS, run the :ref:`bclToFastq` script in the top-level
analysis directory, e.g.::

    qsub -b y -cwd -V bclToFastq.sh \
        /mnt/data/120919_SN7001250_0035_BC133VACXX \
        Unaligned custom_samplesheet.csv

This automatically runs the ``configureBlcToFastq.ps`` and ``make`` steps
(above) together and creates a new subdirectory called ``Unaligned`` with
the FASTQS.

The general syntax for this step is::

    bclToFastq.sh /path/to/ILLUMINA_RUN_DIR output_dir [ samplesheet.csv ]

.. note::

    If bcl-to-fastq fails to generate the FASTQ files due to some problem
    with the input data then the
    :ref:`troubleshooting_bcl_to_fastq_conversion` section below may help.

Populate analysis subdirectories
--------------------------------

Use the :ref:`build_illumina_analysis_dirs` utility to create subdirectories
for each project named in the input sample sheet file, and populate these
with links to the FASTQ files generated in the previous step.

Use the ``--list`` option to see what projects and samples the program will
use, e.g.::

    build_illumina_analysis_dir.py --list \
       /scratch/120919_SN7001250_0035_BC133VACXX_analysis

which produces output of the form::

 Project: AB (4 samples)
         AB1
                 AB1_NoIndex_L002_R1_001.fastq.gz
         AB2
                 AB2_NoIndex_L003_R1_001.fastq.gz
         AB3
                 AB3_NoIndex_L004_R1_001.fastq.gz
         AB4
                 AB4_NoIndex_L005_R1_001.fastq.gz
 Project: Control (4 samples)
         PhiX1
                 PhiX1_NoIndex_L001_R1_001.fastq.gz
         PhiX2
                 PhiX2_NoIndex_L006_R1_001.fastq.gz
         PhiX3
                 PhiX3_NoIndex_L007_R1_001.fastq.gz
         PhiX4
                 PhiX4_NoIndex_L008_R1_001.fastq.gz

Use the ``--expt=EXPT_TYPE`` option to specify a library type for one or
more projects, e.g.::

    build_illumina_analysis_dir.py \
       --expt=AB:ChIP-seq \
       /mnt/analyses/120919_ILLUMINA-73D9FA_00008_FC_analysis

This creates new subdirectories for each project which contain symbolic
links to the FASTQ files::

  <YYMMDD>_<machinename>_<XXXXX>_FC_analysis/
          |
          +-- Unaligned/
          |     |
          |    ...
          |
          +-- <PI>_<library>/
          |     |
          |     +-- *.fastq.gz -> ../Unaligned/.../*.fastq.gz
          |
          |
          +-- <PI>_<library>/
          |     |
          |     +-- *.fastq.gz -> ../Unaligned/.../*.fastq.gz
          |
         ...

``Unaligned`` is the output from the ``bclToFastq.sh`` run (see the
previous section), and will contain the fastq files.  The fastq.gz files
in these directories are symbolic links to the files in the ``Unaligned``
directory.

By default the FASTQ names are simplified versions of the original FASTQs;
use the ``--keep-names`` to preserve the full names of the FASTQ files.


Merging replicates
------------------

Multiplexed runs can produce large numbers of replicates of each sample,
with each replicate producing a single FASTQ file - so if there are 20
samples each with 8 replicates then this will produce 160 FASTQ files.

In this situation it can be more helpful to concatenate the replicates
into single FASTQ files, and can be done automatically when creating the
analysis subdirectories using the ``--merge-replicates`` option.

``--merge-replicates`` doesn't require any additional input; it produces
concatenated FASTQ files (rather than symbolic links) when creating the
analysis subdirectory for each project, e.g.::

    build_illumina_analysis_dir.py \
        --expt=AB:RNA-seq \
        --merge-replicates \
        /mnt/analyses/120919_SN7001250_0035_BC133VACXX_analysis

.. note::

    Use the :ref:`verify_paired` utility to check that the order of
    reads in the merged files are correct.

.. _troubleshooting_bcl_to_fastq_conversion:

Troubleshooting bcl to FASTQ conversion
***************************************

**Failure with error "sample-dir not valid: number of directories must
match the number of barcodes"**

This might be due to the presence of spaces in the ``sampleID`` and
``sampleProjects`` fields in the ``sampleSheet.csv`` file, which seems
to confuse CASAVA.

The solution is to edit the sample sheet file to remove the spaces;
this can be done automatically using the ``--fix-spaces`` option of the
:ref:`prep_sample_sheet` program e.g.::

    prep_sample_sheet.py --fix-spaces -o custom_SampleSheet.csv sampleSheet.csv

will create a copy of the original sample sheet file with any spaces
replaced by underscores.

**Failure with error "barcode XXXXXX for lane 1 has length Y: expected
barcode lenth (including delimiters) is Z"**

This can happen when attempting to demultiplex paired barcoded samples.
The information that CASAVA needs should be read automatically from the
``RunInfo.xml`` file, but it appears that this doesn't always happen (or
perhaps the information is not consistent with the ``bcl`` files e.g.
because the sequencing run didn't complete properly).

To fix this use the ``--use-bases-mask`` option of
``configureBclToFastq.pl`` (or ``bclToFastq.sh``) to tell CASAVA how to
deal with each base. For example::

    --use-bases-mask y101,I8,I8,y85

instructs the software to treat the first 101 bases as the first sequence,
the next 8 as the first index (i.e. barcoded tag attached to the first
sequence), the next 8 as the second index, and then the next 85 bases as
the second sequence.

.. note::

    See also this BioStars question about dealing with the CASAVA error:
    *"barcode CTTGTA for lane 1 has length X: expected barcode lenth is Y"*
    http://www.biostars.org/post/show/49599/casava-error-barcode-cttgta-for-lane-1-has-length-6-expected-barcode-lenth-is-7/#55718
