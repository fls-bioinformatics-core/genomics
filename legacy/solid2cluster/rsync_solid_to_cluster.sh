#!/bin/bash
#
# rsync_solid_to_cluster.sh
#
# Script to do rsync of data from solid machine to cluster
#
# Usage: [ssh-agent] rsync_solid_to_cluster.sh <solid_run> <user>@<host>:<datadir> [<email>]
#
# Note on using with ssh-agent:
#
# As this script performs a number of operations via ssh, it is possible
# to invoke it via ssh-agent. If the script should then detect that the
# ssh-agent is running and automatically invoke ssh-add, prompting for a
# password/phrase - subsequent ssh operations will then not require
# passwords to be supplied.
#
# This mode of operating with ssh-agent is preferred, as the ssh-agent
# process terminates with the script (avoiding the proliferation of orphaned
# ssh-agent processes on the local system).
#
# (Alternatively setting up unattended ssh login avoids the need for using
# ssh-agent.)
#
#####################################################################
# Script globals
#####################################################################
SCRIPT_NAME=`basename $0`
usage="Usage: [ssh-agent] ${SCRIPT_NAME} <solid_run> <user>@<host>:<datadir> [<email>]"
NOW=$(date +"%Y%m%d%H%M")
REMOTE_USER=
REMOTE_HOST=
REMOTE_DATADIR=
RSYNC_EXCLUDES="--exclude=color* --exclude=cycleplots --exclude=jobs* --exclude=traffic_lights"
RSYNC_OPTIONS="-av -e ssh --chmod=u-w,g-w,o-w $RSYNC_EXCLUDES"
RSYNC_LOG="${SCRIPT_NAME%.*}_${NOW}.log"
#
#####################################################################
# Functions
#####################################################################
#
# prompt_user()
#
# Usage: prompt_user [ --exit <status> ] "my message" [ cmd ]
#
# Prompt the user to agree to an action: prints the supplied message
# string with "[N/y]" appended, then waits for user input. Input of
# the form "y", "Y", "Yes" or "yes" are confirmation, otherwise the
# action is declined.
#
# If the action is confirmed then the functions returns 1. If an
# optional command "cmd" was supplied to the function then this is also
# executed.
#
# If the action is declined then the function returns 0, or if --exit
# was supplied then the script exits with the supplied <status>.
function prompt_user() {
    # Check if --exit was supplied
    exit_on_no=
    if [ "$1" == "--exit" ] ; then
	exit_on_no="true"
	shift
	exit_status=$1
	shift
    fi
    # Check if a command was specified
    cmd=
    if [ ! -z "$2" ] ; then
	cmd=$2
    fi
    # Prompt user for confirmation
    echo -n "${1} [N/y]: "
    read ok
    case $ok in
	y|Y|yes|Yes)
	    # User agreed
	    if [ ! -z "$cmd" ] ; then
		# Execute the command
		echo Executing $cmd
		eval $cmd
	    else
		return 1
	    fi
	    ;;
	*)
	    # User declined
	    if [ ! -z $exit_on_no ] ; then
		# Exit the script
		echo "Okay, stopped"
		exit $exit_status
	    else
		if [ ! -z "$cmd" ] ; then
		    # Command is not executed
		    echo "Okay, operation skipped"
		fi
		return 0
	    fi
	    ;;
    esac
}
#
# acknowledge()
#
# Usage: acknowledge "my message"
#
# Prompt the user by printing the supplied message with the text
# "(hit enter to continue)" appended, then wait for a newline before
# passing control back to the calling subprogram.
function acknowledge() {
    echo -n "${1} (hit enter to continue)"
    read ok
    return
}
#
# do_rsync()
#
# Usage: do_rsync [--dry-run] <solid_dir>
#
# Perform the requested rsync operation, using options taken from
# the global shell variables. --dry-run invokes rsync with the dry run
# option and pipes the output to less; otherwise the output is sent to
# a log file.
# Returns the exit status of the rsync command.
function do_rsync() {
    dry_run=
    if [ "$1" == "--dry-run" ] ; then
	dry_run="yes"
	shift
    fi
    solid_run=$1
    if [ ! -d "$solid_run" ] ; then
	return
    fi
    opts=$RSYNC_OPTIONS
    remote=${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DATADIR}
    if [ ! -z "$dry_run" ] ; then
	# Dry run
	acknowledge "Running rsync --dry-run: do 'q' to exit after reviewing"
	opts="--dry-run $opts"
	rsync_cmd="rsync $opts $solid_run $remote"
	$rsync_cmd  | less
	return $?
    else
	# Actual rsync
	rsync_cmd="rsync $opts $solid_run $remote"
	echo Executing $rsync_cmd
	echo Writing output to $RSYNC_LOG
	$rsync_cmd 2>&1 | tee $RSYNC_LOG 
	# Return the output status of the rsync command
	return $?
    fi
}
#
# compare_sizes()
#
# Usage: compare_sizes
#
# Get and compare the size of the source data on the local system with
# that of the copy on the remote system.
#
# Return 1 if they're the same and 0 if they differ
function compare_sizes() {
    # Get size on local machine
    local_size=`du --apparent-size -h $RSYNC_EXCLUDES -s $solid_run`
    local_size=`echo $local_size | cut -f1 -d" "`
    # Get size on remote system
    solid_run_dir=`basename $solid_run`
    du_cmd="du --apparent-size -h $RSYNC_EXCLUDES -s ${REMOTE_DATADIR}/$solid_run_dir"
    remote_size=`ssh ${REMOTE_USER}@${REMOTE_HOST} $du_cmd`
    remote_size=`echo $remote_size | cut -f1 -d" "`
    # Report
    echo Local : $local_size
    echo Remote: $remote_size
    # Compare them
    if [ "$local_size" != "$remote_size" ] ; then
	return 0
    else
	return 1
    fi
}
#
# send_email_notification()
#
# Usage: email_notification <solid_run_dir> [<status_msg>]
#
# Prompts user for an email address and sends the rsync log file to it
# If <status_msg> is specified then incorporate into the subject line
# for the email
#
# NB uses mutt
function send_email_notification() {
    if [ ! -z "$EMAIL_ADDRESS" ] ; then
	if [ ! -z "$2" ] ; then
	    status_msg=$2
	else
	    status_msg="completed"
	fi
	echo "Sending log to $EMAIL_ADDRESS"
	mutt -s "SOLiD rsync ${status_msg}: ${1}" -a $RSYNC_LOG -- $EMAIL_ADDRESS <<EOF
rsync of solid data completed for $1

Log file of rsync is attached
EOF
	
    else
	echo "No address supplied, no notification email sent"
    fi
}
#
# rsync_solid_to_cluster()
#
# Usage: rsync_solid_to_cluster <solid_run_dir>
#
# Wrap the whole rsync process in a shell function so it can easily
# be repeated.
function rsync_solid_to_cluster() {
    #
    # Collect arguments
    solid_run_dir=$1
    echo "Starting rsync for ${solid_run_dir}"
    #
    # Do dry run
    do_rsync --dry-run $solid_run_dir
    #
    # Check that this is okay
    prompt_user --exit 0 "Proceed with rsync?"
    #
    # Do rsync
    echo "Starting rsync (this may take some time)"
    do_rsync $solid_run_dir
    #
    # Check and report status
    status=$?
    echo -n "rsync completed: exit status = $status"
    if [ $status == 0 ] ;  then
	echo " [OK]"
	send_email_notification $solid_run_dir
    else
	echo " [ERROR]"
	echo "*** WARNING: RSYNC RETURNED NON-ZERO EXIT STATUS ***"
	echo "*** Check the rsync output in the log file       ***"
	echo "*** Stopping ***"
	send_email_notification $solid_run_dir "failed"
    fi
    #
    # Check sizes
    prompt_user "Check sizes of local and remote copies?"
    do_check=$?
    if [ $do_check == 1 ] ; then
	compare_sizes
	status=$?
	if [ $status != 1 ] ; then
	    echo "*** WARNING: SIZE OF LOCAL AND REMOTE COPIES DIFFERS ***"
	    echo "*** Check the remote copy and the rsync output       ***"
	    echo "*** Stopping ***"
	    exit 1
	else
	    echo "Local and remote sizes appear to match"
	fi
    else
	echo "Size check skipped"
    fi
}
#
#####################################################################
# Main script
#####################################################################
#
# Collect and process arguments
# NB strip any trailing '/' from the directory name
solid_dir=${1%/}
if [ ! -z "$2" ] ; then
    REMOTE_USER=`echo $2 | cut -d@ -f1`
    REMOTE_HOST=`echo $2 | cut -d@ -f2 | cut -d: -f1`
    REMOTE_DATADIR=`echo $2 | cut -d@ -f2 | cut -d: -f2`
fi
EMAIL_ADDRESS=$3
#
# Do checks
if [ -z "$solid_dir" ] ; then
    echo $usage
    exit 1
elif [ ! -d "$solid_dir" ] ; then
    echo "${solid_dir}: run not found"
    exit 1
fi
if [ -z "$REMOTE_USER" ] || [ -z "$REMOTE_HOST" ] || [ -z "$REMOTE_DATADIR" ]
then
    echo Missing destination information
    echo $usage
    exit 1
fi
#
# Collect SOLiD run dirs to transfer
solid_runs=
solid_run_base=`echo $solid_dir | sed "s/_BC$//g" | sed "s/_FRAG$//g" | sed "s/_PE$//g"`
extensions="_FRAG _FRAG_BC _FRAG_2 _FRAG_BC_2 _PE_BC _PE_BC_2"
for ext in $extensions ; do
    solid_run_dir=${solid_run_base}${ext}
    if [ "${solid_run_dir}" == "${solid_dir}" ] ; then
	solid_runs="${solid_runs} ${solid_run_dir}"
    elif [ -d "${solid_run_dir}" ] ; then
	prompt_user "Include directory ${solid_run_dir}?" 
	response=$?
	if [ $response == 1 ] ; then
	    solid_runs="${solid_runs} ${solid_run_dir}"
	fi
    fi
done
#
# Check: did we get any runs?
if [ -z "$solid_runs" ] ; then
    echo "Warning: non-canonical run name $solid_dir"
    solid_runs=$solid_dir
fi
#
# Get email address for notifications, if not provided on command line
if [ -z "$EMAIL_ADDRESS" ] ; then
    echo -n "Email address to send log file/notifications to? "
    read addr
    if [ ! -z "$addr" ] ; then
	EMAIL_ADDRESS=$addr
    else
	echo "No email address set"
    fi
fi
#
# Report settings
echo "---------------------------------------------------------------"
echo "Source:"
echo "SOLiD directories: $solid_runs"
echo "Destination:"
echo "Remote user      : $REMOTE_USER"
echo "Remote host      : $REMOTE_HOST"
echo "Remote directory : $REMOTE_DATADIR"
echo "Email address    : $EMAIL_ADDRESS"
echo "---------------------------------------------------------------"
#
# Check if ssh-agent is running
if [ ! -z "$SSH_AUTH_SOCK" ] && [ ! -z "$SSH_AGENT_PID" ] ; then
    echo "ssh-agent detected:"
    echo SSH_AUTH_SOCK: $SSH_AUTH_SOCK
    echo SSH_AGENT_PID: $SSH_AGENT_PID
    echo "Invoking ssh-add:"
    ssh-add
fi
#
# Run the rsync
for solid_run in $solid_runs ; do
    prompt_user "Proceed with rsync for ${solid_run}?"
    response=$?
    if [ $response == 1 ] ; then
	rsync_solid_to_cluster $solid_run $REMOTE_USER $REMOTE_HOST $REMOTE_DATADIR
    else
	echo "*** Skipped rsync for ${solid_run} ***"
    fi
done
#
# Done
echo "Finished"
exit 0
##
#
