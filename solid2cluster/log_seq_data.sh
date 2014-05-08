#!/bin/sh
#
# log_seq_data.sh <log_file> <seq_data_dir>
#
# Creates a new entry in a log of sequencing data directories
#
function usage() {
    echo "Usage:"
    echo "    `basename $0` <logging_file> [-d|-u] <seq_data_dir> [<description>]"
    echo "    `basename $0` <logging_file> -c <seq_data_dir> <new_dir> [<description>]"
    echo "    `basename $0` <logging_file> -v"
    echo ""
    echo "Add, update or delete an entry for <seq_data_dir> in <logging_file>, or"
    echo "verify entries."
    echo
    echo "<seq_data_dir> can be a primary data directory from a sequencer or a"
    echo "directory of derived data (e.g. analysis directory)"
    echo
    echo "By default an entry is added for the specified data directory; each"
    echo "entry is a tab-delimited line with the full path for the data directory"
    echo "followed by the UNIX timestamp and the optional description text."
    echo ""
    echo "If <logging_file> doesn't exist then it will be created; if"
    echo "<seq_data_dir> is already in the log file then it won't be added again."
    echo
    echo "Options:"
    echo ""
    echo "     -d     deletes an existing entry"
    echo "     -u     update description for an existing entry (or creates a new one"
    echo "            if an existing entry not found)"
    echo "     -c     changes an existing entry, updating the directory path and"
    echo "            (optionally) the description"
    echo "     -v     validates the entries in the logging file."
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
elif [ "$2" == "-v" ] ; then
    # Validate logging file
    MODE=validate
    shift
elif [ "$2" == "-c" ] ; then
    # Change entry
    MODE=change
    shift
fi
#
# Check remaining command line arguments
if [ $MODE == "validate" ] ; then
    if [ $# -ne 1 ] ; then
	echo "Unrecognised arguments after -v option: $@"
	exit 1
    fi
    retval=0
    while read dir timestamp descr ; do
	if [ ! -z  "$(echo $dir | grep -v ^#)" ] ; then
	    if [ ! -e $dir ] ; then
		echo "WARNING missing $dir"
		retval=1
	    fi
	fi
    done < $LOG_FILE
    if [ $retval -ne 0 ] ; then
	echo "ERROR invalid entries detected" >&2
	exit 1
    else
	exit
    fi
elif [ $MODE == "change" ] ; then
    CUR_DATA_DIR=$2
    SEQ_DATA_DIR=$(abs_path $3)
    DESCRIPTION=$4
else
    SEQ_DATA_DIR=$(abs_path $2)
    DESCRIPTION=$3
fi
SEQ_DATA_DIR=$(readlink -m $SEQ_DATA_DIR)
#
# Make a lock on the log file
lock_file $LOG_FILE --remove
if [ "$?" != "1" ] ; then
    echo "Couldn't get lock on $LOG_FILE"
    exit 1
fi
#
# Check that the sequencing data directory exists (unless
# in delete mode)
if [ ! -d "$SEQ_DATA_DIR" ] && [ $MODE != "delete" ] ; then
    echo "No directory $SEQ_DATA_DIR"
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
# Log of sequencing data directories
EOF
    fi
    #
    # Check if an entry already exists
    has_entry=`grep ${SEQ_DATA_DIR}$'\t' $LOG_FILE | wc -l`
    if [ $has_entry -gt 0 ] ; then
	echo "Entry already exists for $SEQ_DATA_DIR in $LOG_FILE"
	unlock_file $LOG_FILE
	exit 1
    fi
    #
    # Append an entry to the log file
    echo "Adding entry to $LOG_FILE"
    echo ${SEQ_DATA_DIR}$'\t'$(timestamp $SEQ_DATA_DIR)$'\t'${DESCRIPTION} >> $LOG_FILE
fi
#
# Delete entry
if [ $MODE == delete ] || [ $MODE == update ] || [ $MODE == change ] ; then
    #
    # For 'change', extract the existing entry
    if [ $MODE == change ] ; then
	# Check entry exists
	got_entry=$(grep ^${CUR_DATA_DIR}$'\t' $LOG_FILE)
	if [ -z "$got_entry" ] ; then
	    echo "ERROR entry not found: $CUR_DATA_DIR"
	    unlock_file $LOG_FILE
	    exit 1
	fi
	# Check that basename of old and new match up
	if [ $(basename $CUR_DATA_DIR) != $(basename $SEQ_DATA_DIR) ] ; then
	    echo ERROR basenames differ: $(basename $CUR_DATA_DIR) vs $(basename $SEQ_DATA_DIR)
	    unlock_file $LOG_FILE
	    exit 1
	fi
	# Collect existing description
	if [ -z "$DESCRIPTION" ] ; then
	    DESCRIPTION=$(grep ^$CUR_DATA_DIR $LOG_FILE | cut -f3)
	fi
	# Jiggle names for deletion step
	NEW_DATA_DIR=$SEQ_DATA_DIR
	SEQ_DATA_DIR=$CUR_DATA_DIR
    fi
    #
    # Make a temporary file
    tmpfile=`mktemp`
    #
    # Delete the entry
    echo "Removing entry for $SEQ_DATA_DIR"
    grep -v ^${SEQ_DATA_DIR}$'\t' $LOG_FILE > $tmpfile
    #
    # Re-add if updating
    if [ $MODE == update ] || [ $MODE == change ] ; then
	echo "Recreating entry for $SEQ_DATA_DIR"
	if [ $MODE == change ] ; then
	    SEQ_DATA_DIR=$NEW_DATA_DIR
	fi
	echo ${SEQ_DATA_DIR}$'\t'$(timestamp $SEQ_DATA_DIR)$'\t'${DESCRIPTION} >> $tmpfile
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
