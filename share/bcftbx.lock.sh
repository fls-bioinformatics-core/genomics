#!/bin/sh
#
# lock.sh: shell function library for managing file locks
# Peter Briggs, University of Manchester 2011
#
# Shell functions for creating and managing locks on files
#
# Example: try to get the lock on a file "foo.bar":
#
# lock_file foo.bar
# has_lock foo.bar
# if [ "$?" == "1" ] ; then
#    # Process owns the lock
#    # Do stuff to foo.bar
#    unlock_file foo.bar
# fi
#
# NB Requires the functions from functions.sh.
#
# To include in a shell script, do:
#
# . `dirname $0`/functions.sh
# . `dirname $0`/lock.sh
#
# if this file is in the same directory as the script, or
#
# . `dirname $0`/relative/path/to/functions.sh
# . `dirname $0`/relative/path/to/lock.sh
#
# if it's elsewhere.
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
	if [ $(timestamp $lock) -lt $ts ] ; then
	    # Found an older lock file
	    return 0
	fi
    done
    # This process has the oldest lock
    return 1
}
#
# wait_for_lock(): try to create a lock, with timeout
#
# Usage: wait_for_lock <file> <timeout>
#
# Tries to get the lock on the named <file> once a
# second, until the lock is either acquired (returns 1)
# or the <timeout> limit (in seconds) is reach
# (returns 0).
#
# Example:
#
# wait_for_lock foo.bar 10
# if [ $? == 1 ] ; then
#    ...do something with foo.bar...
#    unlock_file foo.bar
# else
#    ...failed to get lock after 10 seconds...
# fi
function wait_for_lock() {
    timeout=$2
    tries=0
    lock_file $1 --remove
    while [ $? != 1 ] ; do
	tries=$((tries + 1))
	if [ $timeout -le $tries ] ; then
	    # Timed out before acquiring lock
	    return 0
	fi
	sleep 1s
	# Try again
	lock_file $1 --remove
    done
    # Lock has been acquired
    return 1
}
##
#
