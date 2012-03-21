#!/bin/sh
#
# log_solid_run.sh <log_file> <solid_run_dir>
#
# Creates a new entry in a log of SOLiD data directories
#
function usage() {
    echo "`basename $0` <logging_file> [-d|-u] <solid_run_dir> [<description>]"
    echo ""
    echo "Add, update or delete an entry for <solid_run_dir> in <logging_file>."
    echo
    echo "By default an entry is added for the run. Each entry is a tab-delimited"
    echo "line with the full path for the run directory, followed by the UNIX"
    echo "timestamp and the optional description text."
    echo ""
    echo "If <logging_file> doesn't exist then it will be created; if"
    echo "<solid_run_dir> is already in the log file then it won't be added again."
    echo
    echo "-d deletes an existing entry, while -u updates it (or adds a new one if"
    echo "not found). -u is intended to allow descriptions to be modified."
}
#
# Import external function libraries
. `dirname $0`/../share/functions.sh
. `dirname $0`/../share/lock.sh
#
# Initialise
if [ $# -lt 2 ] ; then
    usage
    exit
fi
MODE=add
#
# Command line
LOG_FILE=$1
if [ "$2" == "-d" ] ; then
    # Delete entry
    MODE=delete
    shift
elif [ "$2" == "-u" ] ; then
    # Update entry
    MODE=update
    shift
fi
SOLID_RUN=`readlink -m $(abs_path $2)`
DESCRIPTION=$3
#
# Make a lock on the log file
lock_file $LOG_FILE --remove
if [ "$?" != "1" ] ; then
    echo "Couldn't get lock on $LOG_FILE"
    exit 1
fi
#
# Check that the SOLiD run directory exists (unless
# in delete mode)
if [ ! -d "$SOLID_RUN" ] && [ $MODE != "delete" ] ; then
    echo "No directory $SOLID_RUN"
    unlock_file $LOG_FILE
    exit 1
fi
#
# Add entry
if [ $MODE == add ] ; then
    #
    # Check that log file exists
    if [ ! -e "$LOG_FILE" ] ; then
	echo "Making $LOG_FILE"
	touch $LOG_FILE
	# Write a header
	cat > $LOG_FILE <<EOF
# Log of SOLiD data directories
EOF
    fi
    #
    # Check if an entry already exists
    has_entry=`grep ${SOLID_RUN}$'\t' $LOG_FILE | wc -l`
    if [ $has_entry -gt 0 ] ; then
	echo "Entry already exists for $SOLID_RUN in $LOG_FILE"
	unlock_file $LOG_FILE
	exit 1
    fi
    #
    # Append an entry to the log file
    echo "Adding entry to $LOG_FILE"
    echo ${SOLID_RUN}$'\t'$(timestamp $SOLID_RUN)$'\t'${DESCRIPTION} >> $LOG_FILE
fi
#
# Delete entry
if [ $MODE == delete ] || [ $MODE == update ] ; then
    #
    # Make a temporary file
    tmpfile=`mktemp`
    #
    # Delete the entry
    echo "Removing entry for $SOLID_RUN"
    grep -v ^${SOLID_RUN}$'\t' $LOG_FILE > $tmpfile
    #
    # Re-add if updating
    if [ $MODE == update ] ; then
	echo "Recreating entry for $SOLID_RUN"
	echo ${SOLID_RUN}$'\t'$(timestamp $SOLID_RUN)$'\t'${DESCRIPTION} >> $tmpfile
    fi
    #
    # Replace log file with new version
    echo "Updating $LOG_FILE"
    /bin/mv $tmpfile $LOG_FILE
    /bin/rm -f $tmpfile
fi
#
# Sort into order
sortfile=`mktemp`
sort -r -k 2 $LOG_FILE > $sortfile
/bin/mv $sortfile $LOG_FILE
/bin/rm -f $sortfile
#
# Finished
unlock_file $LOG_FILE
exit
##
#
