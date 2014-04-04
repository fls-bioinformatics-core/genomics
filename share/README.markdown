share: common libraries and modules shared by applications
==========================================================

Shell function libraries
------------------------

*   `functions.sh`: various useful shell functions to deal with file names, string
     manipulations and program versions amongst others.

*   `lock.sh`: library functions for locking files shared between scripts.

*   `ngs_utils.`: shell functions wrapping NGS programs (e.g. `solid2fastq`) and
    providing NGS-specific helper functions.

Python modules
--------------

### General utilities ###

*   `bcf_utils.py`: general utility classes and functions shared between BCF codes

*   `platforms.py`: utilities and data to identify NGS sequencer platforms

### SOLiD data ###

*   `Experiment.py`: classes for defining SOLiD sequencing experiments (i.e. collections
    of related primary data).

*   `SolidData.py`: classes for extracting data about SOLiD runs from directory structure,
    data files and naming conventions.

### Illumina data ###

*   `IlluminaData.py`: classes for extracting data about runs from Illumina-based
    sequencing platforms.

### Job execution and management ###

*   `JobRunner.py`: classes providing generic interface for starting and managing job
    runs

*   `Pipeline.py`: classes for running jobs iteratively

### Handling files ###

*   `FASTQFile.py`: classes for iterating through records in FASTQ files.

*   `simple_xls.py`: classes and functions provide a nicer programmatic interface to XLS
    spreadsheet generation (built on top of `Spreadsheet.py`).

*   `Spreadsheet.py`: classes for creating and updating XLS format spreadsheets (requires
    the 3rd-party `xlwt`, `xlrd` and `xlutil` Python packages).

*   `TabFile.py`: classes for handling data from generic tab-delimited files.
