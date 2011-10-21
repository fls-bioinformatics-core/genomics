share: common libraries and modules shared by applications
==========================================================

Shell function libraries
------------------------

*   `functions.sh`: various useful shell functions to deal with file names, string
     manipulations and program versions amongst others.

*   `lock.sh`: library functions for locking files shared between scripts.

Python modules
--------------

*   `Experiment.py`: Python module providing classes for defining SOLiD sequencing
    experiments (collections of related primary data)

*   `JobRunner.py`: classes providing generic interface for starting and managing job
    runs

*   `Pipeline.py`: classes for running jobs iteratively

*   `SolidData.py`: Python module providing classes for extracting data about SOLiD
    runs from directory structure, data files and naming conventions.

*   `Spreadsheet.py`: Python module for creating and updating XLS format spreadsheets.
     Requires the 3rd-party `xlwt`, `xlrd` and `xlutil` Python packages.

*   `TabFile.py`: Python module providing classes for handling data from
    tab-delimited files.
