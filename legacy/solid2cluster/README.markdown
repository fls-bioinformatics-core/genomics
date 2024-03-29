solid2cluster (legacy)
======================

Deprecated utilities for transferring data from the SOLiD instrument to the
cluster:

 *   `rsync_solid_to_cluster.sh`: perform transfer of primary data
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
      either 'absolute' (default) or 'relative'
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
