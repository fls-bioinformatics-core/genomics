solid2cluster
=============

Utilities for transferring data from the SOLiD instrument to the cluster:

 *   `rsync_solid_to_cluster.sh`: perform transfer of primary data
 *   `log_solid_run.sh`: maintain logging file of transferred runs
 *   `analyse_solid_run.py`: report on the primary data directories from SOLiD runs
 *   `build_analysis_dir.py`: construct analysis directories for experiments


rsync_solid_to_cluster.sh
-------------------------

Interactive script to semi-automate the transfer of data from the SOLiD
instrument to a destination machine.

Usage:

    rsync_solid_to_cluster.sh <local_dir> <user>@<remote_host>:<remote_dir> [<email_address>]

`<local_dir>` is the directory to be copied; `<user>` is an account on the
destination machine `<remote_host>` and `<remote_dir>` is the parent directory
where a copy of `<local_dir>` will be made.

The script operates interactively and prompts the user at each step to
confirm each action:

1. Check that the information is correct
2. Do `rsync --dry-run` and inspect the output
3. Perform the actual rsync operation (including removing group write permission from the remote copy)
4. Check that the local and remote file sizes match

If there is more than one run with the same base name then the script will detect the second run
and offer to copy both in a single script run.

The output from each `rsync` is also captured in a timestamped log file. If an email address is supplied
on the command line then a copy of the logs will be mailed to this address.


log_solid_run.sh
----------------

Script to add entries for transferred SOLiD run directories to a logging file.

Usage:

    log_solid_run.sh <logging_file> <solid_run_dir> [<description>]

A new entry for the directory `<solid_run_dir>` will be added to `<logging_file>`, consisting of
the full path to the directory, a UNIX timestamp, and the optional description.

If the logging file doesn't exist then it will be created, and a new entry won't be created for any
SOLiD run directory that is already in the logging file.


analyse_solid_run.py
--------------------

Utility for performing various checks and operations on SOLiD run directories.
If a single solid_run_dir is specified then analyse_solid_run.py automatically
finds and operates on all associated directories from the same instrument and
with the same timestamp.

Usage:

    analyse_solid_run.py OPTIONS solid_run_dir [ solid_run_dir ... ]

Options:

    -h, --help           show this help message and exit
    --only               only operate on the specified solid_run_dir, don't
                         locate associated run directories
    --report             print a report of the SOLiD run
    --xls                write report to Excel spreadsheet
    --verify             do verification checks on SOLiD run directories
    --layout             generate script for laying out analysis directories
    --md5sum             calculate md5sums for primary data files
    --rsync              generate script for rsyncing data
    --copy=COPY_PATTERN  copy primary data files to pwd from specific library
                         where names match COPY_PATTERN, which should be of the
                         form '<sample>/<library>'
    --gzip=GZIP_PATTERN  make gzipped copies of primary data files in pwd from
                         specific libraries where names match GZIP_PATTERN,
                         which should be of the form '<sample>/<library>'
    --quiet              suppress warnings
    --debug              turn on debugging output (nb overrides --quiet)


build_analysis_dir.py
---------------------

Automatically construct analysis directories for experiments which contain links to the primary
data files.

Usage:

    build_analysis_dir.py [OPTIONS] EXPERIMENT [EXPERIMENT ...] <solid_run_dir>

General Options:

    --dry-run: report the operations that would be performed
    --debug: turn on debugging output
    --top-dir=<dir>: create analysis directories as subdirs of <dir>;
      otherwise create them in cwd.
    --naming-scheme=<scheme>: specify naming scheme for links to
      primary data (one of 'minimal' - library names only, 'partial' -
      includes instrument name, datestamp and library name (default)
      or 'full' - same as source data file
    --link=<type>: type of links to create to primary data files,
      either 'relative' (default) or 'absolute'
    --run-pipeline=<script>: after creating analysis directories, run
      the specified <script> on SOLiD data file pairs in each

Options For Defining Experiments:

An "experiment" is defined by a group of options, which must be supplied
in this order for each experiment specified on the command line:

    --name=<name> [--type=<expt_type>] --source=<sample>/<library>
                                      [--source=... ]

`<name>` is an identifier (typically the user's initials) used for the
analysis directory e.g. `PB`

`<expt_type>` is e.g. `reseq`, `ChIP-seq`, `RNAseq`, `miRNA`...

`<sample>/<library>` specify the names for primary data files e.g.
`PB_JB_pool/PB*`

Example:

    --name=PB --type=ChIP-seq --source=PB_JB_pool/PB*

Both `<sample>` and `<library>` can include a trailing wildcard character
(i.e. `*`) to match multiple names. `*/*` will match all primary data files.
Multiple `--sources` can be declared for each experiment.

For each experiment defined on the command line, a subdirectory called
`<name>_<expt_type>` (e.g. `PB_ChIP-seq` - if no `<expt_type>`
was supplied then just the name is used) will be made containing links to
each of the primary data files.
