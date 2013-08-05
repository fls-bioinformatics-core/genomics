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

*   `bcf_utils.py`: utility classes and functions shared between BCF codes.

*   `Experiment.py`: classes for defining SOLiD sequencing experiments (i.e. collections
    of related primary data).

*   `FASTQFile.py`: classes for iterating through records in FASTQ files.

*   `IlluminaData.py`: classes for extracting data about runs from Illumina-based
    sequencing platforms.

*   `JobRunner.py`: classes providing generic interface for starting and managing job
    runs.

*   `Pipeline.py`: classes for running jobs iteratively

*   `platforms.py`: utilities and data to identify NGS sequencer platforms

*   `SolidData.py`: classes for extracting data about SOLiD runs from directory structure,
    data files and naming conventions.

*   `Spreadsheet.py`: classes for creating and updating XLS format spreadsheets (requires
    the 3rd-party `xlwt`, `xlrd` and `xlutil` Python packages).

*   `TabFile.py`: classes for handling data from generic tab-delimited files.
