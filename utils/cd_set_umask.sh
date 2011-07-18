#!/bin/sh
#
# cd_set_umask.sh
#
# Switch umask when moving in or out of specific directory or its
# children
#
# Source this script to switch your umask from the default (i.e.
# 0002 = read-write for owner, read-only for group/world) to
# 0022 = read-write for owner and group, read-only for world) in
# when cd'ing to a special directory (e.g. /foo/bar/ or one of its
# subdirectories.
#
# When you cd to a different directory then the umask reverts to
# the default.
#
# To set up at login, add the following to the end of e.g. ~/.profile:
#
# . cd_set_umask.sh
# alias cd='cd_set_umask /foo/bar 0002'
#
# Caveat: as this works by creating an alias for the cd command,
# there are likely to be issues if you use other ways to navigate the
# directory structure (e.g. popd, pushd)
#
CD_SET_UMASK_DEFAULT=`umask`
#
function cd_set_umask {
    # Usage:
    # cd_set_umask <special_dir> <special_umask> <default_umask> <dir>
    #
    # Arguments:
    # <special_dir>   = directory in which to use the <special_umask>
    #                   (also applies to subdirs of <special_dir>
    # <special_umask> = umask to use in <special_dir> and its children
    # <dir>           = directory to change to
    cd $3
    SPECIAL_DIR=$1
    SPECIAL_UMASK=$2
    in_special_dir=`pwd | grep ^${SPECIAL_DIR} | wc -w`
    current_umask=`umask`
    if [ $in_special_dir == 1 ] ; then
	# Within the "special" directory
	# Reset umask, if it's different from the one to use in
	# the "special" directory
	if [ $SPECIAL_UMASK != "$current_umask" ] ; then
	    umask $SPECIAL_UMASK
	fi
    else
	# Not in the "special" directory
	# Reset the umask, if it's currently different to the default
	if [ $CD_SET_UMASK_DEFAULT != "$current_umask" ] ; then
	    umask $CD_SET_UMASK_DEFAULT
	fi
    fi
}
#