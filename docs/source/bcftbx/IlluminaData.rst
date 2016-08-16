``bcftbx.IlluminaData``
=======================

.. automodule:: bcftbx.IlluminaData

Core data and run handling classes
**********************************

.. autoclass:: bcftbx.IlluminaData.IlluminaData
.. autoclass:: bcftbx.IlluminaData.IlluminaProject
.. autoclass:: bcftbx.IlluminaData.IlluminaRun
.. autoclass:: bcftbx.IlluminaData.IlluminaRunInfo
.. autoclass:: bcftbx.IlluminaData.IlluminaSample

Samplesheet handling
********************

.. autoclass:: bcftbx.IlluminaData.SampleSheet
.. autoclass:: bcftbx.IlluminaData.CasavaSampleSheet
.. autoclass:: bcftbx.IlluminaData.IEMSampleSheet

.. autofunction:: bcftbx.IlluminaData.convert_miseq_samplesheet_to_casava
.. autofunction:: bcftbx.IlluminaData.get_casava_sample_sheet
.. autofunction:: bcftbx.IlluminaData.verify_run_against_sample_sheet
.. autofunction:: bcftbx.IlluminaData.samplesheet_index_sequence
.. autofunction:: bcftbx.IlluminaData.normalise_barcode

Utility classes and functions
*****************************

.. autoclass:: bcftbx.IlluminaData.IlluminaFastq

.. autofunction:: bcftbx.IlluminaData.describe_project
.. autofunction:: bcftbx.IlluminaData.fix_bases_mask
.. autofunction:: bcftbx.IlluminaData.get_unique_fastq_names
.. autofunction:: bcftbx.IlluminaData.split_run_name
.. autofunction:: bcftbx.IlluminaData.summarise_projects
.. autofunction:: bcftbx.IlluminaData.get_unique_fastq_names

Exception classes
*****************

.. autoclass:: bcftbx.IlluminaData.IlluminaDataError
