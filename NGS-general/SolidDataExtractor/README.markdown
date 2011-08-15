SolidDataExtractor
==================
Utilities for analysing SOLiD runs, constructing analysis directories
and running QC pipeline.

Overview
--------
There are 3 programs:

*   `analyse_solid_run.py`: report the samples and libraries from the run
    and write XLS spreadsheet.

*   `build_analysis_dir.py`: automatically construct analysis directories for
    experiments which contain links to the primary data files.

*   `run_pipeline.py`: run a (QC) pipeline script via SGE's `qsub` command,
    to perform QC steps on each pairs of csfasta/qual data files in a
    specified analysis directory.

Each is used for a separate function and must be run independently. These are
built around some additional Python modules:

*   `SolidDataExtractor.py`: provides classes for reading data about a
    completed SOLiD run.

*   `Spreadsheet.py`: provides classes for constructing and appending to
    XLS spreadsheets. NB requires the `xlwt`, `xlrb` and `xlutils` Python
    libraries.

There is also a bash script to perform the QC:

*   `qc.sh`: given a csfasta and qual file pair, runs the QC pipeline
    (solid2fastq, fastq_screen and qc_boxplotter) on them.