=====================
SOLiD sequencing data
=====================

This section outlines the general structure of the data from SOLiD
based sequencers.

****************************
Structure of SOLiD run names
****************************

For multiplex fragment sequencing the run names will have the form::

    <instrument-name>_<date-stamp>_FRAG_BC[_2]

(For example: ``solid0123_20110315_FRAG_BC``).

The components are:

 * ``<instrument_name>``: name of the SOLiD instrument e.g. ``solid0123``
 * ``<date-stamp>``: a date stamp in year-month-day format e.g. ``20110315``
   is 15th March 2011
 * ``FRAG``: indicates a fragment library was used
 * ``BC``: indicates bar-coding was used (note that not all samples in the
   run might be bar-coded, even if this appears in the name)
 * ``2``: if this is present then it indicates the data came from flow cell
   2; otherwise it's from flow cell 1.

For multiplex paired-end sequencing the run names have the form::

   <instrument-name>_<date-stamp>_PE_BC

Here the ``PE`` part of the name indicates a paired-end run.

.. note::

    If the run name contains ``WFA`` then it's a work-flow analysis and not
    final sequence data.

See also `SOLiD 4 System Instrument Operation Quick Reference <http://www3.appliedbiosystems.com/cms/groups/mcb_support/documents/generaldocuments/cms_082582.pdf>`_ (PDF)
for more information.

*************************************
Navigating SOLiD run data directories
*************************************

-------------------
Run definition file
-------------------

Typically the top-level of a SOLiD run data directory should contain the run
definition file which has information about the samples and libraries used in
the run, including the names that were assigned when the run was set up. For
example for a bar-coded sample this might look like:

::

 version	userId	runType	isMultiplexing	runName	runDesc	mask	protocol
 v1.3	lab_user	FRAGMENT	TRUE	solid0127_20111013_FRAG_BC		1_spot_mask_sf	SOLiD4 Multiplex
 primerSet	baseLength
 BC	10
 F3	50
 sampleName	sampleDesc	spotAssignments	primarySetting	library	application	secondaryAnalysis	multiplexingSeries	barcodes
 DB_SB_JL_pool		1	default primary	DB01	SingleTag	sacCer2	BC Kit Module 1-96	"1"
 DB_SB_JL_pool		1	default primary	DB02	SingleTag	sacCer2	BC Kit Module 1-96	"2"
 ...
 DB_SB_JL_pool		1	default primary	SB_DIMB_2	SingleTag	none	BC Kit Module 1-96	"14"
 DB_SB_JL_pool		1	default primary	SB_DMTA	SingleTag	none	BC Kit Module 1-96	"15"

Essentially the run definition file consists of a three sections, each
delimited by a header line. The last section (with the header line
beginning ``sampleName...``) has the information on each of the libraries,
and can be used to locate the primary data files.

-------------------------------------------------------------------
Primary data files (csfasta/qual) for multiplex fragment sequencing
-------------------------------------------------------------------

Locating the primary data files within the SOLiD data directories can be
quite tedious and confusing. For bar-coded samples the following heuristic
can be used:

1. From the top-level of the SOLiD run directory (e.g.
   ``solid0123_20111013_FRAG_BC``) move into the subdirectory with the sample
   name of interest (e.g. ``DB_SB_JL_pool``, from the run definition file in
   the previous section).

2. Within the sample subdirectory, look for a directory called ``results``
   (which will be a link to one of the other ``results...`` directories here).
   Move into the ``results`` directory.

3. Within the ``results`` subdirectory, look for a directory called
   ``libraries`` and move into this.

4. Within ``libraries`` you should see subdirectories named for each of the
   libraries associated with this sample, as they appear in the run definition
   file (e.g. ``DB01``, ``DB02``, ..., ``SB_DIMB_2``, ``SB_DMTA``). Move into
   the subdirectory for the library of interest.

5. Within the directory for a specific library, there should be one or more
   subdirectories with names of the form ``primary.20111015000420127`` (and
   possibly also ``secondary.20111015000420127``). Check each of these
   subdirectories looking for the one which itself contains three subdirectories
   ``reads``, ``rejects`` and ``reports`` (the others will only contain
   ``reads`` and ``reports``). Move into this directory, and then into the
   ``reads`` subdirectory. This is the location of the primary data files
   (csfasta and qual files).

Typically this results in a path of the form::

 solid0123_20111013_FRAG_BC/SAMPLE_NAME/results/libraries/LIBRARY_NAME/primary.TIMESTAMP/reads/

As a further check, the primary data file names should include ``F3`` in the name.

---------------------------------------------------------------------
Primary data files (csfasta/qual) for multiplex paired-end sequencing
---------------------------------------------------------------------

In the case of paired-end sequencing the final data consists of primary data
file pairs for both the ``F3`` and ``F5`` reads for each library.

Locating the ``F3`` and ``F5`` reads uses a similar heuristic to that
described above for multiplex fragment sequencing:

1. From the top-level of the SOLiD run directory, move into the subdirectory
   for the sample name of interest (e.g. ``DB_SB_JL_pool``).

2. Look for the ``results`` directory and move into it.

3. Look for the ``libraries`` directory and move into it.

4. Within ``libraries`` there are subdirectories for each of the libraries
   associated with this sample (e.g. ``DB01``, ``DB02``, ..., ``SB_DIMB_2``,
   ``SB_DMTA``) - move into the one for the library of interest.

5. Here there are one or more subdirectories with names of the form
   ``primary.20111015000420127`` etc. Check each of these subdirectories
   looking for those which contain three subdirectories ``reads``, ``rejects``
   and ``reports`` (not just ``reads`` and ``reports``). There should be two
   ``primary...`` directories which match this criterion: in the ``reads``
   directory of one there will be primary data files with ``F5-BC`` in the
   name, and in the other files with ``F3``.

-------------------------------------------------------------
Automatic location of primary data using analyse_solid_run.py
-------------------------------------------------------------

The heuristics described above are also encoded in the
:ref:`reference_analyse_solid_run`
program, which will identify and report the location of the primary data
files when without any other arguments i.e.:

::

    analyse_solid_run.py solid0123_20111101_FRAG_BC

This works for both multiplex fragment and multiplex paired-end sequencing.
