illumina2cluster
================

Utilities for preparing data on the cluster from the Illumina instrument:

 *   `bclToFastq.sh`: generate FASTQ from BCL files
 *   `update_sample_sheet.py`: 


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
    --set-id=SAMPLE_ID    update/set the values in the 'SampleID' field;
                          SAMPLE_ID should be of the form '<lanes>:<name>',
                          where <lanes> is a single integer (e.g. 1), a set of
                          integers (e.g. 1,3,...), a range (e.g. 1-3), or a
                          combination (e.g. 1,3-5,7).
    --set-project=SAMPLE_PROJECT
                          update/set values in the 'SampleProject' field;
                          SAMPLE_PROJECT should be of the form '<lanes>:<name>',
                          where <lanes> is a single integer (e.g. 1), a set of
                          integers (e.g. 1,3,...), a range (e.g. 1-3), or a
                          combination (e.g. 1,3-5,7).

Example:

Read in the sample sheet file `SampleSheet.csv`, update the `SampleProject` and
`SampleID` for lanes 1 and 8, and write the updated sample sheet to the file
`SampleSheet2.csv`:

    update_sample_sheet.py -o SampleSheet2.csv --set-project=1,8:Control \
        --set-id=1:PhiX_10pM --set-id=8:PhiX_12pM SampleSheet.csv