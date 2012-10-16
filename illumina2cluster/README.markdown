illumina2cluster
================

Utilities for preparing data on the cluster from the Illumina instrument:

 *   `bclToFastq.sh`: generate FASTQ from BCL files
 *   `build_illumina_analysis_dir.py`: create and populate per-project analysis dirs
 *   `update_sample_sheet.py`: edit SampleSheet.csv before generating FASTQ


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
    -l, --list        list projects and samples without creating the analysis
                      directories but don't actually do them
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


update_sample_sheet.py
----------------------

View and manipulate sample sheet files for Illumina GA2 sequencer.

Usage:

    update_sample_sheet.py [OPTIONS] SampleSheet.csv

Utility to view and edit SampleSheet file from Illumina GA2 sequencer. Can be
used to update sample IDs and project names before running BCL to FASTQ
conversion.

Options:

    -h, --help            show this help message and exit
    -o SAMPLESHEET_OUT    output new sample sheet to SAMPLESHEET_OUT
    -v, --view            view contents of sample sheet
    --fix-spaces          replace spaces in SampleID and SampleProject fields
                          with underscores
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

Example:

Read in the sample sheet file `SampleSheet.csv`, update the `SampleProject` and
`SampleID` for lanes 1 and 8, and write the updated sample sheet to the file
`SampleSheet2.csv`:

    update_sample_sheet.py -o SampleSheet2.csv --set-project=1,8:Control \
        --set-id=1:PhiX_10pM --set-id=8:PhiX_12pM SampleSheet.csv