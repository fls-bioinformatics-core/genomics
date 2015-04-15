``bcftbx.IlluminaData``
=======================

.. automodule:: bcftbx.IlluminaData

Data handling
*************

.. autoclass:: bcftbx.IlluminaData.IlluminaData
.. autoclass:: bcftbx.IlluminaData.IlluminaProject
.. autoclass:: bcftbx.IlluminaData.IlluminaRun
.. autoclass:: bcftbx.IlluminaData.IlluminaRunInfo
.. autoclass:: bcftbx.IlluminaData.IlluminaSample

.. autofunction:: bcftbx.IlluminaData.describe_project
.. autofunction:: bcftbx.IlluminaData.fix_bases_mask
.. autofunction:: bcftbx.IlluminaData.get_unique_fastq_names
.. autofunction:: bcftbx.IlluminaData.split_run_name
.. autofunction:: bcftbx.IlluminaData.summarise_projects

Samplesheet handling
********************

.. autoclass:: bcftbx.IlluminaData.CasavaSampleSheet
.. autoclass:: bcftbx.IlluminaData.IEMSampleSheet

.. autofunction:: bcftbx.IlluminaData.convert_miseq_samplesheet_to_casava
.. autofunction:: bcftbx.IlluminaData.get_casava_sample_sheet
.. autofunction:: bcftbx.IlluminaData.verify_run_against_sample_sheet

Exception classes
*****************

.. autoclass:: bcftbx.IlluminaData.IlluminaDataError
