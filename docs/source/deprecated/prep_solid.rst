Preparing SOLiD Data for analysis
=================================

Handling the SOLiD data
***********************

Copying SOLiD data from the sequencer
-------------------------------------

The script :ref:`rsync_solid_to_cluster` can be used to copy data from
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
:ref:`analyse_solid_run` to generate MD5 checksums for each of the primary
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

In these cases the :ref:`analyse_solid_run` script can be used generate a
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
5. Add the data and analysis directories to the logging file

Check the primary data
----------------------

The :ref:`analyse_solid_run` script can be used to check and report on the
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

To get a suggested layout command, run :ref:`analyse_solid_run` with the
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

The :ref:`build_analysis_dir` program creates the top level analysis
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
(regardless of where the ``QV`` part appears in the original name).

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
