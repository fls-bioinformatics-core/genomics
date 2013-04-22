illumina2cluster
================

Utilities for preparing data on the cluster from the Illumina instrument:

 *   `analyse_illumina_run.py`: reporting and manipulations of Illumina run data
 *   `auto_process_illumina.sh`: automatically process Illumina-based sequencing run
 *   `bclToFastq.sh`: generate FASTQ from BCL files
 *   `build_illumina_analysis_dir.py`: create and populate per-project analysis dirs
 *   `demultiplex_undetermined_fastq.py`: demultiplex undetermined Illumina reads
 *   `prep_sample_sheet.py`: edit SampleSheet.csv before generating FASTQ
 *   `rsync_seq_data.sh`: copy sequencing data using rsync


analyse_illumina_run.py
-----------------------

Utility for performing various checks and operations on Illumina data.

Usage:

    analyse_illumina_run.py OPTIONS illumina_data_dir

`illumina_data_dir` is the top-level directory containing the `Unaligned` directory with
the fastq.gz files produced by the BCL-to-FASTQ conversion step.

Options:

    -h, --help            show this help message and exit
    --report              report sample names and number of samples for each
                          project
    -l, --list            list projects, samples and fastq files directories
    --unaligned=UNALIGNED_DIR
                          specify an alternative name for the 'Unaligned'
                          directory conatining the fastq.gz files
    --copy=COPY_PATTERN   copy fastq.gz files matching COPY_PATTERN to current
                          directory
    --verify=SAMPLE_SHEET
                          check CASAVA outputs against those expected for
                          SAMPLE_SHEET


auto_process_illumina.sh
------------------------

Automatically process data from an Illumina-based sequencing platform

Usage:

    auto_process_illumina.sh COMMAND [ PLATFORM DATA_DIR ]

COMMAND can be one of:

    setup: prepares a new analysis directory. This step must be
           done first and requires that PLATFORM and DATA_DIR 
           arguments are also supplied (these do not have to be
           specified for other commands).
           This creates an analysis directory in the current dir
           with a custom_SampleSheet.csv file; this should be
           examined and edited before running the subsequent 
           steps.

    make_fastqs: runs CASAVA to generate Fastq files from the
           raw bcls.

    run_qc: runs the QC pipeline and generates reports.

The make_fastqs and run_qc commands must be executed from the
analysis directory created by the setup command.


bclToFastq.sh
-------------

Bcl to Fastq conversion wrapper script

Usage:

    bclToFastq.sh <illumina_run_dir> <output_dir>

`<illumina_run_dir>` is the top-level Illumina data directory; Bcl files are expected to
be in the `Data/Intensities/BaseCalls` subdirectory. `<output_dir>` is the top-level
target directory for the output from the conversion process (including the generated fastq
files).

The script runs `configureBclToFastq.pl` from `CASAVA` to set up conversion scripts,
then runs `make` to perform the actual conversion. It requires that `CASAVA` is available
on the system.

Options:

    -h, --help        display usage text
    --nmismatches N   set number of mismatches to allow; recommended values are 0 for
                      samples without multiplexing, 1 for multiplexed samples with tags
                      of length 6 or longer (see the CASAVA user guide for details of
                      the --nmismatches option)
    --use-bases-mask BASES_MASK
                      specify a bases-mask string tell CASAVA how to use each cycle.
		      The supplied value is passed directly to configureBcltoFastq.pl
		      (see the CASAVA user guide for details of how --use-bases-mask
		      works)


build_illumina_analysis_dirs.py
-------------------------------

Query/build per-project analysis directories for post-bcl-to-fastq data from Illumina GA2
sequencer.

Usage:

    build_illumina_analysis_dir.py OPTIONS illumina_data_dir

Create per-project analysis directories for Illumina run. 'illumina_data_dir'
is the top-level directory containing the 'Unaligned' directory with the
fastq.gz files generated from the bcl files. For each 'Project_...' directory
build_illumina_analysis_dir.py makes a new subdirectory and populates with
links to the fastq.gz files for each sample under that project.

Options:

    -h, --help        show this help message and exit
    --dry-run         report operations that would be performed if creating the
                      analysis directories but don't actually do them
    --unaligned=UNALIGNED_DIR
                      specify an alternative name for the 'Unaligned'
                      directory conatining the fastq.gz files
    --expt=EXPT_TYPE  specify experiment type (e.g. ChIP-seq) to append to the
                      project name when creating analysis directories. The
                      syntax for EXPT_TYPE is '<project>:<type>' e.g. --expt=NY
                      :ChIP-seq will create directory 'NY_ChIP-seq'. Use
                      multiple --expt=... to set the types for different
                      projects
    --keep-names      preserve the full names of the source fastq files when
                      creating links
    --merge-replicates   
                      create merged fastq files for each set of replicates
                      detected


demultiplex_undetermined_fastq.py
---------------------------------

Demultiplex undetermined Illumina reads output from CASAVA.

Usage:

    demultiplex_undetermined_fastq.py OPTIONS DIR

Reassign reads with undetermined index sequences. (i.e. barcodes). DIR is the
name (including any leading path) of the 'Undetermined_indices' directory
produced by CASAVA, which contains the FASTQ files with the undetermined reads
from each lane.

Options:

    --version             show program's version number and exit
    -h, --help            show this help message and exit
    --barcode=BARCODE_INFO
                          specify barcode sequence and corresponding sample name
                          as BARCODE_INFO. The syntax is
                          '<name>:<barcode>:<lane>' e.g. --barcode=PB1:ATTAGA:3
    --samplesheet=SAMPLE_SHEET
                          specify SampleSheet.csv file to read barcodes, sample
                          names and lane assignments from (as an alternative to
                          --barcode).


prep_sample_sheet.py
--------------------

Prepare sample sheet files for Illumina sequencers for input into CASAVA.

Usage:

    prep_sample_sheet.py [OPTIONS] SampleSheet.csv

Utility to prepare SampleSheet files from Illumina sequencers. Can be used to
view, validate and update or fix information such as sample IDs and project
names before running BCL to FASTQ conversion.

Options:

    -h, --help            show this help message and exit
    -o SAMPLESHEET_OUT    output new sample sheet to SAMPLESHEET_OUT
    -v, --view            view contents of sample sheet
    --miseq               convert input sample sheet MiSEQ to CASAVA-compatible
                          format
    --fix-spaces          replace spaces in SampleID and SampleProject fields
                          with underscores
    --fix-duplicates      append unique indices to SampleIDs where original
                          SampleID/SampleProject combination are duplicated
    --fix-empty-projects  create SampleProject names where these are blank in
                          the original sample sheet
    --set-id=SAMPLE_ID    update/set the values in the 'SampleID' field;
                          SAMPLE_ID should be of the form '<lanes>:<name>',
                          where <lanes> is a single integer (e.g. 1), a set of
                          integers (e.g. 1,3,...), a range (e.g. 1-3), or a
                          combination (e.g. 1,3-5,7)
    --set-project=SAMPLE_PROJECT
                          update/set values in the 'SampleProject' field;
                          SAMPLE_PROJECT should be of the form '<lanes>:<name>',
                          where <lanes> is a single integer (e.g. 1), a set of
                          integers (e.g. 1,3,...), a range (e.g. 1-3), or a
                          combination (e.g. 1,3-5,7)
    --ignore-warnings     ignore warnings about spaces and duplicated
                          sampleID/sampleProject combinations when writing new
                          samplesheet.csv file

Examples:

Read in the sample sheet file `SampleSheet.csv`, update the `SampleProject` and
`SampleID` for lanes 1 and 8, and write the updated sample sheet to the file
`SampleSheet2.csv`:

    prep_sample_sheet.py -o SampleSheet2.csv --set-project=1,8:Control \
        --set-id=1:PhiX_10pM --set-id=8:PhiX_12pM SampleSheet.csv

Automatically fix spaces and duplicated `sampleID`/`sampleProject` combinations
and write out to `SampleSheet3.csv`:

    prep_sample_sheet.py --fix-spaces --fix-duplicates \
        -o SampleSheet3.csv SampleSheet.csv


rsync_seq_data.sh
-----------------

Rsync a copy of a sequencing data directory to a local or remote destination.

Usage:

    rsync_seq_data.sh OPTIONS SEQ_DATA_DIR TARGET_DIR

Makes a copy of sequencing data directory SEQ_DATA_DIR under TARGET_DIR, and writes
the rsync log both to STDOUT and to a timestamped log file (except for `--dry-run`).

Options are passed directly to the `rsync` command.
