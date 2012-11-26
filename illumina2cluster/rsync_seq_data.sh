#!/bin/sh -e
#
# rsync_seq_data
#
# Usage: rsync_seq_data.sh OPTIONS SEQ_DATA_DIR TARGET_DIR
#
# Make a copy of sequencing data directory SEQ_DATA_DIR under TARGET_DIR
#
# Deal with command line options
if [ $# -lt 2 ] ; then
    echo Usage: $0 OPTIONS SEQ_DATA_DIR TARGET_DIR
    exit 1
fi
RSYNC_OPTIONS=
DRY_RUN=
while [ $# -gt 2 ] ; do
    # Append to list of options
    echo "Adding $1 to rsync command line"
    RSYNC_OPTIONS="$RSYNC_OPTIONS $1"
    # Special case: --dry-run
    if [ $1 == "--dry-run" ] ; then
	DRY_RUN=yes
    fi
    # Next option
    echo $RSYNC_OPTIONS
    shift
done
#
# Arguments
# NB Strip trailing slash from source directory name
SEQ_DATA_DIR=${1%/}
TARGET_DIR=$2
#
# Determine if this is a local or remote rsync & check for local dirs
test -z `echo $SEQ_DATA_DIR | grep [a-z0-9]*@[a-z.]*:[a-z/]*`
is_remote_source=$?
if [ $is_remote_source == 0 ] && [ ! -d $SEQ_DATA_DIR ] ; then
    echo "ERROR source directory $SEQ_DATA_DIR not found or not a directory"
    exit 1
fi
test -z `echo $TARGET_DIR | grep [a-z0-9]*@[a-z.]*:[a-z/]*`
is_remote_target=$?
if [ $is_remote_target == 0 ] && [ ! -d $TARGET_DIR ] ; then
    echo "ERROR target directory $TARGET_DIR not found or not a directory"
    exit 1
fi
#
# Set rsync ssh option for remote source and/or target
if [ $is_remote_source == 1 ] || [ $is_remote_target == 1 ] ; then
    SSH_OPTION="-e ssh"
else
    SSH_OPTION=
fi
#
# Make log file name
SEQ_DATA_DIR_BASE=`basename $SEQ_DATA_DIR`
NOW=$(date +"%Y%m%d%H%M")
RSYNC_LOG="rsync.$SEQ_DATA_DIR_BASE.$NOW.log"
#
# Construct rsync command options
RSYNC_OPTIONS="-av ${SSH_OPTION} ${RSYNC_OPTIONS}"
rsync_cmd="rsync $RSYNC_OPTIONS $SEQ_DATA_DIR $TARGET_DIR"
#
# Report settings etc
echo "---------------------------------------------------------------"
echo "Sequence data dir: $SEQ_DATA_DIR"
echo "Destination dir  : $TARGET_DIR"
echo "rsync options    : $RSYNC_OPTIONS"
echo "---------------------------------------------------------------"
#
# Run the rsync
if [ -z "$DRY_RUN" ] ; then
    # Do the rsync
    echo "Running $rsync_cmd 2>&1 | tee $RSYNC_LOG"
    $rsync_cmd 2>&1 | tee $RSYNC_LOG
else
    # Do a dry run only
    echo "Running $rsync_cmd 2>&1 | less"
    $rsync_cmd 2>&1 | less
fi
#
# Finished
echo "Done"
exit
##
#

