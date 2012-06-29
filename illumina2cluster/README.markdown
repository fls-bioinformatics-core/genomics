illumina2cluster
================

Utilities for preparing data on the cluster from the Illumina instrument:

 *   `bclToFastq.sh`: generate FASTQ from BCL files


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
