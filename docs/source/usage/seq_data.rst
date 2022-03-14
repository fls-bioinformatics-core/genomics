Handling sequencing run data
============================

************************
Illumina sequencing runs
************************

The :ref:`reference_prep_sample_sheet` utility can be used for editing
and clean-up of sample sheet files that are used as input to the Fastq
generation process, including converting between different sample sheet
formats.

Examples:

1. Read in the sample sheet file ``SampleSheet.csv``, update the
   ``SampleProject`` and ``SampleID`` for lanes 1 and 8, and write
   the updated sample sheet to the file ``SampleSheet2.csv``:

   ::

     prep_sample_sheet.py -o SampleSheet2.csv --set-project=1,8:Control \
          --set-id=1:PhiX_10pM --set-id=8:PhiX_12pM SampleSheet.csv

2. Automatically fix spaces and duplicated ``sampleID``/``sampleProject``
   combinations and write out to ``SampleSheet3.csv``:

   ::

     prep_sample_sheet.py --fix-spaces --fix-duplicates \
          -o SampleSheet3.csv SampleSheet.csv

The ``bcftbx`` library also provides classes and functions for handling
Illumina sequencing data:

* :doc:`../bcftbx/IlluminaData`

See :doc:`../background/illumina` for details of the data structures
of raw and processed Illumina sequencing runs.

*********************
SOLiD sequencing runs
*********************

The :ref:`reference_analyse_solid_run` utility can be used to report on
the primary data from a run of a SOLiD sequencer instrument, and perform
various checks and operations those data.

The ``bcftbx`` library also provides classes and functions for handling
SOLiD sequencing data:

* :doc:`../bcftbx/SolidData`
* :doc:`../bcftbx/Experiment`

See :doc:`../background/solid` for details of the directory structure
and contents of a SOLiD sequencing run.
