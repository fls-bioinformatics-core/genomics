rsync_solid_to_cluster.sh
=========================

Interactive script to semi-automate the transfer of data from the SOLiD
instrument to a destination machine.

Usage:

    rsync_solid_to_cluster.sh <local_dir> <user>@<remote_host>:<remote_dir>

`<local_dir>` is the directory to be copied; `<user>` is an account on the
destination machine `<remote_host>` and `<remote_dir>` is the parent directory
where a copy of `<local_dir>` will be made.

The script operates interactively and prompts the user at each step to
confirm each action:

1. Check that the information is correct
2. Do `rsync --dry-run` and inspect the output
3. Perform the actual rsync operation
4. Check that the local and remote file sizes match
5. Remove group write permissions from the remote copy
