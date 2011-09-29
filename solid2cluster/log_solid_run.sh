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
# Import external function library
. `dirname $0`/../share/functions.sh
#
# timestamp(): get timestamp on file as seconds from epoch
#
# Usage: timestamp <file>
function timestamp() {
    echo `stat -c %X $1`
}
#
# abs_path(): get the absolute path
#
# Usage: abs_path <file>
function abs_path() {
    if [ "$1" == "." ] ; then
	echo `pwd`
    elif [ -e "$1" ] ; then
	try_path=`pwd`/$1
	if [ -e "$try_path" ] ; then
	    echo $try_path
	else
	    echo $1
	fi
    else
	echo $1
    fi
}
#
# lock_file_name(): get the name for a lock file
#
# Usage: lock_file_name <file>
function lock_file_name() {
    pid=$$
    echo "$(rootname $1).lock.${pid}"
}
#
# lock_file(): try to create a lock on file
#
# Usage: lock_file <file> [--remove]
#
# Creates a lock file on <file> and returns 1 if successful and
# the created lock has precedence; otherwise returns 0.
#
# If --remove is specified then the lock file is automatically
# deleted if it doesn't have precedence.
function lock_file() {
    # Make a lock file
    lock_file=$(lock_file_name $1)
    if [ ! -f "$lock_file" ] ; then
	touch ${lock_file}
    fi
    # See if this actually has the lock
    has_lock $1
    if [ "$?" == "0" ] ; then
	# Doesn't have precedence
	if [ "$2" == "--remove" ] ; then
	    # Removing lock
	    unlock_file $1
	fi
	return 0
    fi
    # Lock has precedence
    return 1
}
#
# unlock_file(): remove the lock on a file
#
# Usage: unlock_file <file>
function unlock_file() {
    lock_file=$(lock_file_name $1)
    if [ -f "$lock_file" ] ; then
	/bin/rm -f $lock_file
    fi
}
#
# has_lock(): check if this process owns the lock
#
# Usage: has_lock <file>
#
# Returns 1 if the current process has the lock on the named
# file, 0 otherwise.
function has_lock() {
    lock_file=$(lock_file_name $1)
    lock_dir=`dirname $lock_file`
    if [ ! -f "$lock_file" ] ; then
	# Lock file doesn't exist
	echo "Lock file not found"
	return 0
    fi
    ts=$(timestamp $lock_file)
    for lock in `ls ${lock_dir}/*.lock.*` ; do
	if [ "$lock" != "$lock_file" ] ; then
	    echo $lock $(timestamp $lock)
	    if [ $(timestamp $lock) -lt $ts ] ; then
		# Found an older lock file
		return 0
	    fi
	fi
    done
    # This process has the oldest lock
    return 1
}
#
# Main script
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
# Check that the SOLiD run directory exists
if [ ! -d "$SOLID_RUN" ] ; then
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
