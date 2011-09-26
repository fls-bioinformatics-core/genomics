solid2cluster
=============

Utilities for transferring data from the SOLiD instrument to the cluster:

 *   `rsync_solid_to_cluster.sh`: perform transfer of primary data
 *   `log_solid_run.sh`: maintain logging file of transferred runs


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
