Preparing SOLiD Data for analysis
=================================

Background
**********

Structure of SOLiD run names
----------------------------

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

See also `Link SOLiD 4 System Instrument Operation Quick Reference <http://www3.appliedbiosystems.com/cms/groups/mcb_support/documents/generaldocuments/cms_082582.pdf>`_ (PDF)
for more information.

Navigating the SOLiD run data directories
-----------------------------------------

**Run definition file**

Typically the top-level of a SOLiD run data directory should contain the run
definition file which has information about the samples and libraries used in
the run, including the names that were assigned when the run was set up. For
example for a bar-coded sample this might look like::

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

**Primary data files (csfasta/qual) for multiplex fragment sequencing**

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

**Primary data files (csfasta/qual) for multiplex paired-end sequencing**

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

**Automatic location of primary data using analyse_solid_run.py**

The heuristics described above are also encoded in the ``analyse_solid_run.py``
program, which will identify and report the location of the primary data files
when without any other arguments i.e.::

    analyse_solid_run.py solid0123_20111101_FRAG_BC

This works for both multiplex fragment and multiplex paired-end sequencing.

Handling the SOLiD data
***********************

Copying SOLiD data from the sequencer
-------------------------------------

The script ``rsync_solid_to_cluster.sh`` can be used to copy data from
the sequencing instrument in a semi-automatic fashion, by prompting the user
at each point to ask if they wish to proceed with the next step.

.. note::

    The script needs to be run on the sequencer.

It is recommended to run the script from within a ``screen`` session; it is
started using the command::

    rsync_solid_to_cluster.sh <solid_run> <user>@<host>:<datadir> [<email_address>]

This creates a copy of ``<solid_run>`` in ``<data_dir>`` on the remote system,
for example::

    rsync_solid_to_cluster.sh solid0123_20110827_FRAG_BC me@dataserver.foo.ac.uk:/mnt/data me@foo.ac.uk

If there are multiple runs (i.e. flowcells) with the same base name then the
script will detect the second run and also offer to transfer that as part of
the procedure. The output of the actual ``rsync`` command is written to a
time-stamped log file, and if an email address is given then the log will be
mailed to that address.

The script performs the following actions, prompting for user confirmation at
each stage:

1. Checks that the information provided by the user is correct
2. Does ``rsync --dry-run`` and presents the output for inspection by the user
3. Performs the rsync operation to copy the data (including removal of group
   write permissions on the remote copy) and emails a copy of the log file to the user
4. Checks that the local and remote file sizes match

See :ref:`rsync_solid_to_cluster` for more information on the script.

Verifying the transferred data using MD5 checksums
--------------------------------------------------

Once the data has been transferred use the ``--md5sum`` option of
``analyse_solid_run.py`` to generate MD5 checksums for each of the primary
data files, for example::

    analyse_solid_run.py --md5sum solid 0123_20110827_FRAG_BC > chksums

.. note::

    This step should be run on the remote system.

The ``chksums`` file generated above will consist of lines of the form::

    229e9a651451c9e47f35e45792273185  solid0123_20111014_FRAG_BC/AB_CD_EF_pool/results.F1B1/libraries/AB_A1M1/primary.201312345678901/reads/solid0123_20111014_FRAG_BC_AB_CD_EF_pool_F3_AB_A1M1.csfasta

and can be fed into the Linux ``md5sum`` program on the SOLiD instrument
to verify that the original files are the same, e.g.::

    md5sum -c chksums

.. note::

    This should be performed from the parent directory holding the runs
    on the SOLiD instrument.

Copying sequencing data to another location
-------------------------------------------

Once the data has been transferred from the sequencer to the data store, it
maybe be necessary to copy a subset of the data to another location.

In these cases the ``analyse_solid_run.py`` script can be used generate a
template ``rsync`` script to perform the transfer, for example::

    analyse_solid_run.py --rsync solid 0127_20110914_FRAG_BC > rsync.sh

The template ``rsync.sh`` script will contain something like::

    #!/bin/sh
    #
    # Script command to rsync a subset of data to another location
    # Edit the script to remove the exclusions on the data sets to be copied
    rsync --dry-run -av -e ssh \
    --exclude=AB_SEQ1 \
    --exclude=AB_SEQ2 \
    --exclude=AB_SEQ3 \
    --exclude=AB_SEQ4 \
    --exclude=AB_SEQ5 \
    --exclude=AB_SEQ6 \
    --exclude=AB_SEQ7 \
    --exclude=AB_SEQ8 \
    /mnt/data/solid0127_20120227_FRAG_BC user@remote.system:/destination/parent/dir

You must then edit the script:

* Remove the ``--exclude`` lines for each of the data sets you wish
  to transfer (yes, this is counter-intuative!);
* Edit ``user@remote.system:/destination/parent/dir`` and set to the user,
  system and directory you want to copy the data to.

To execute do::

    ./rsync.sh

which will perform a "dry run" - remove the ``--dry-run`` argument at the
start of the generated script to perform the copy itself.

Preparing analysis directories
******************************

Overview
--------

Once the SOLiD data has been transferred to the data store, the steps
for creating the analysis directories:

0. Set up the environment to use the scripts
1. Check that the primary data
2. Create and populate the analysis directories
3. Run the automated QC pipeline
4. Generate XLS spreadsheet entry
5. Add the data and analysis directories to the `ngsdata` logging file

Check the primary data
----------------------

The ``analyse_solid_run.py`` script can be used to check and report on the
SOLiD data. Running with the ``--verify`` option checks that the primary
data is available for each sample and library::


    analyse_solid_run.py --verify <solid_run_dir>

Use the ``--report`` option for a summary of the run::

    analyse_solid_run.py --report <solid_run_dir>

to analyse the run data and get a report of the samples and libraries, e.g.::

    $ analyse_solid_run.py solid0127_20110725_FRAG_BC
    Flow Cell 1 (Quads)
    ===================
    I.D.   : solid0127_20110725_FRAG_BC
    Date   : 25/07/11
    Samples: 4
    
    Sample AB_E
    -----------
    
    Project E: E01-16 (16 libraries)
    --------------------------------
    Pattern: AB_E/E*
    /mnt/data/solid0127_20110725_FRAG_BC/AB_E/.../solid0127_20110725_FRAG_BC_AB_E_F3_E01.csfasta
    /mnt/data/solid0127_20110725_FRAG_BC/AB_E/.../solid0127_20110725_FRAG_BC_AB_E_F3_QV_E01.qual
    <...15 more file pairs snipped...>

    Sample AB_F
    -----------

    Project F: F01-16 (16 libraries)
    --------------------------------
    Pattern: AB_F/F*
    /mnt/data/solid0127_20110725_FRAG_BC/AB_F/.../solid0127_20110725_FRAG_BC_AB_F_F3_F01.csfasta
    /mnt/data/solid0127_20110725_FRAG_BC/AB_F/.../solid0127_20110725_FRAG_BC_AB_F_F3_QV_F01.qual
    <...15 more file pairs snipped...>
  
    ...

This reports details of the location of the primary data for each
library (e.g. ``E01``) within each sample (e.g. ``AB_E``).

Create and populate analysis directories
----------------------------------------

To get a suggested layout command, run ``analyse_solid_run.py`` with the
``--layout`` option, e.g.::

    analyse_solid_run.py --layout <solid_run_dir>

which produces output of the form e.g.::

    #!/bin/sh
    #
    # Script commands to build analysis directory structure
    #
    ./build_analysis_dir.py \
    --link=relative \
    --top-dir=/mnt/analyses/solid0127_20111013_FRAG_BC_analysis \
    --name=AB --type=expt --source=AB_CD_EF_pool/AB0* \
    --name=CD --type=expt --source=AB_CD_EF_pool/CD_* \
    --name=EF --type=expt --source=AB_CD_EF_pool/EF_* \
    /mnt/data/solid0127_20111013_FRAG_BC
    #
    ./build_analysis_dir.py \
    --link=relative \
    --top-dir=/mnt/analyses/solid0127_20111013_FRAG_BC_2_analysis \
    --name=UV --type=expt --source=UV_XY_pool/UV_* \
    --name=XY --type=expt --source=UV_XY_pool/XY* \
    /mnt/data/solid0127_20111013_FRAG_BC_2

This output can be redirected to a file e.g.::

    analyse_solid_dir.py --layout /mnt/data/solid0127_20111013_FRAG_BC > layout.sh

and edited as appropriate (specifically: the ``--type`` arguments
should be updated to the appropriate experimental method e.g.
``--type=ChIP-seq``, ``--type=RNA-seq`` etc), before being executed
from the command line i.e.::

    sh layout.sh

The ``build_analysis_dir.py`` program creates the top level analysis
directories, with subdirectories for each of the experiments (using
a combination of the name and experiment type e.g. ``AB_ChIP-seq``).
Each subdirectory will contain symbolic links to the primary data
files.

**Experiment types**

The suggested experiment types are:

* `ChIP-seq`
* `RNA-seq`
* `RIP-seq`
* `reseq`
* `miRNA`

**Naming schemes**

By default the symbolic link names are "partial" versions of the full
primary data file names. Add the ``--naming-scheme=SCHEME`` option to
the layout script to explicitly choose a naming scheme:

 +-------------+-------------------------------------------+----------------------------------------------------+
 | Scheme      | Template                                  | Example                                            |
 +=============+===========================================+====================================================+
 | ``partial`` | ``INSTRUMENT_TIMESTAMP_LIBRARY[_QV].ext`` | ``solid0127_20110725_F01.csfasta``                 |
 +-------------+-------------------------------------------+----------------------------------------------------+
 | ``minimal`` | ``LIBRARY.ext``                           | ``F01.csfasta``                                    |
 +-------------+-------------------------------------------+----------------------------------------------------+
 | ``full``    | Same as primary data file                 | ``solid0127_20110725_FRAG_BC_AB_F_F3_F01.csfasta`` |
 +-------------+-------------------------------------------+----------------------------------------------------+

For the partial scheme, the qual file names always end with ``_QV``
(regardless of where the `QV` part appears in the original name).

For paired-end data, both the partial and minimal schemes append
either ``_F3`` or ``_F5`` to the names as appropriate.

**Specifying symbolic link types**

The ``--link`` option allows you to specify whether links to primary
data should be ``relative`` (recommended) or ``absolute``. If it's not
possible to create relative links then absolute links are created
even if ``relative`` links were requested.

Use the ``symlinks`` utility on Linux to update absolute links to
relative links if required.

Generate XLS spreadsheet entry
******************************

Running::

     analyse_solid_run.py --spreadsheet=<output_spreadsheet> <solid_run_dir>

writes the data for the last run to a new spreadsheet, or appends it if the
named spreadsheet already exists.

Note that if there are two directories for the SOLiD run then the script
automatically detects the second one and writes the data for both.
