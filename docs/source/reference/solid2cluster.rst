SOLiD data handling utilities
=============================

Utilities for transferring data from the SOLiD instrument to the cluster:

* :ref:`log_seq_data`: maintain logging file of transferred runs and analysis data
* :ref:`analyse_solid_run`: report on the primary data directories from SOLiD runs

.. _log_seq_data:

log_seq_data.sh
***************

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

.. _analyse_solid_run:

analyse_solid_run.py
********************

Utility for performing various checks and operations on SOLiD run directories.
If a single solid_run_dir is specified then analyse_solid_run.py automatically
finds and operates on all associated directories from the same instrument and
with the same timestamp.

Usage::

    analyse_solid_run.py OPTIONS solid_run_dir [ solid_run_dir ... ]

Options:

.. cmdoption:: --only

    only operate on the specified solid_run_dir, don't
    locate associated run directories

.. cmdoption:: --report

    print a report of the SOLiD run

.. cmdoption:: --report-paths

    in report mode, also print full paths to primary data files

.. cmdoption:: --xls

    write report to Excel spreadsheet

.. cmdoption:: --verify

    do verification checks on SOLiD run directories

.. cmdoption:: --layout

    generate script for laying out analysis directories

.. cmdoption:: --rsync

    generate script for rsyncing data

.. cmdoption:: --copy=COPY_PATTERN

    copy primary data files to pwd from specific library
    where names match ``COPY_PATTERN``, which should be of the
    form ``'<sample>/<library>'``

.. cmdoption:: --gzip=GZIP_PATTERN

    make gzipped copies of primary data files in pwd from
    specific libraries where names match ``GZIP_PATTERN``,
    which should be of the form ``'<sample>/<library>'``

.. cmdoption:: --md5=MD5_PATTERN

    calculate md5sums for primary data files from specific
    libraries where names match ``MD5_PATTERN``, which should
    be of the form ``'<sample>/<library>'``

.. cmdoption:: --md5sum

    calculate md5sums for all primary data files (equivalent to ``--md5=*/*``)

.. cmdoption:: --no-warnings

    suppress warning messages
