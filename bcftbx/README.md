bcftbx: Python package for BCF 'genomics' applications
======================================================

### General utilities ###

*   `htmlpagewriter.py`: programmatic generation of HTML files
*   `Md5sum.py`: classes and functions for md5 checksum operations
*   `platforms.py`: utilities and data to identify NGS sequencer platforms
*   `utils.py`: general utility classes and functions shared between BCF codes

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

### Testing ###

*   `test/mock_data.py`: classes and functions for setting up test data directories