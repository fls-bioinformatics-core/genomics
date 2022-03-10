General non-bioinformatic utilities
===================================

Logging details of sequencing runs (log_seq_runs.sh)
****************************************************

Script to add entries for transferred SOLiD run or analysis directories to a
logging file.

Usage::

    log_seq_data.sh [-u|-d] <logging_file> <solid_run_dir> [<description>]

A new entry for the directory ``<solid_run_dir>`` will be added to
``<logging_file>``, consisting of the path to the directory, a UNIX timestamp,
and the optional description.

The path can be relative or absolute; relative paths are automatically converted
to full paths.

If the logging file doesn't exist then it will be created. A new entry won't be
created for any SOLiD run directory that is already in the logging file.

Options:

.. cmdoption:: -u

    Updates an existing entry

.. cmdoption:: -d

    Deletes an existing entry

Examples:

Log a primary data directory::

    log_seq_data.sh /mnt/data/SEQ_DATA.log /mnt/data/solid0127_20110914_FRAG_BC "Primary data"

Log an analysis directory (no description)::

    log_seq_data.sh /mnt/data/SEQ_DATA.log /mnt/data/solid0127_20110914_FRAG_BC_analysis

Update an entry to add a description::

    log_seq_data.sh /mnt/data/SEQ_DATA.log -u /mnt/data/solid0127_20110914_FRAG_BC_analysis \
        "Analysis directory"

Delete an entry::

    log_seq_data.sh /mnt/data/SEQ_DATA.log -d /mnt/data/solid0127_20110914_FRAG_BC_analysis


Checking files and directories using MD5 sums
*********************************************

The ``md5checker.py`` utility provides a way of checking files and directories
using MD5 sums; it can generate a set of MD5 sums for a file or the contents of
a directory, and then use these to verify the contents of another file, directory
or set of files.

Its basic functionality is very much like the standard ``md5sum`` Linux program
(however note that ``md5checker.py`` should also work on Windows), but it can
also compare two directories directly with MD5 sums, without the need for an
intermediate checksum file. This function is intended to provide a straightforward
way of running MD5 checks for example when copying analysis of data generated in
a cluster scratch area to the archive area.

For example: say you have a directory in ``$SCRATCH`` called ``my_work``, which
holds the results of various analysis jobs that you've run on the cluster. At some
point you decide to copy these results to the data area::

    cp -a $SCRATCH/my_work /mnt/data/copy_of_my_work

Then you run an MD5 sum check on the copy by doing::

    md5checker.py --diff $SCRATCH/my_work /mnt/data/copy_of_my_work

which by default will generate output of the form::

    Recursively checking files in /scratch/my_work against copies in /mnt/data/copy_of_my_work
    important_data.sam: OK
    important_data.bam: OK
    ...
    Summary: 147 files checked, 147 okay 0 failed

(Note that this differencing mode only considers files that are in ``my_work``, so
if ``copy_of_my_work`` contains additional files then these won't be checked or
reported.)

Run ``md5checker.py -h`` to see the other available options.
