#!/bin/sh
#
# cd_set_umask_ngsdata.sh
#
# Switch umask when moving in or out of specific directory or its
# children (specifically, /fs/nas7/ngsdata)
#
# Source this script to switch your umask from the default (i.e.
# 0002 = read-write for owner, read-only for group/world) to
# 0022 = read-write for owner and group, read-only for world) in
# when cd'ing to /fs/nas7/ngs_data or one of its subdirectories.
#
# When you cd to a different directory then the umask reverts to
# the default.
#
# To set up at login, add the following to the end of e.g. ~/.profile:
#
# if [ -f /fs/nas7/ngsdata/software/bioinf-scripts/NGS-general/cd_set_umask_ngsdata.sh ] ; then
#     . /fs/nas7/ngsdata/software/bioinf-scripts/NGS-general/cd_set_umask_ngsdata.sh
# fi
#
# The script works by creating an alias for the cd command, so there
# are likely to be issues if you use other ways to navigate the
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
    ##echo set_umask: cd to $3
    cd $3
    SPECIAL_DIR=$1
    SPECIAL_UMASK=$2
    in_special_dir=`pwd | grep ^${SPECIAL_DIR} | wc -w`
    current_umask=`umask`
    ##echo $current_umask
    if [ $in_special_dir == 1 ] ; then
	##echo In subdir of $SPECIAL_DIR
	if [ $SPECIAL_UMASK != "$current_umask" ] ; then
	    ##echo Setting umask to $SPECIAL_UMASK
	    umask $SPECIAL_UMASK
	##else
	##    echo Umask already set to $SPECIAL_UMASK
	fi
    else
	##echo Not in subdir of $SPECIAL_DIR
	if [ $CD_SET_UMASK_DEFAULT != "$current_umask" ] ; then
	    ##echo Setting umask to $CD_SET_UMASK_DEFAULT
	    umask $CD_SET_UMASK_DEFAULT
	##else
	##    echo Umask already set to $CD_SET_UMASK_DEFAULT
	fi
    fi
}
#
alias cd='cd_set_umask /fs/nas7/ngsdata 0002'