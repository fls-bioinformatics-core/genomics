#!/usr/bin/env python3
#
#     users.py: get information on users and groups
#     Copyright (C) University of Manchester 2026 Peter Briggs


"""
Get information on users and groups on the system:

* get_current_user: get name of the current user
* get_user_from_uid: get user name from ID
* get_uid_from_user: get user ID from name
* get_group_from_gid: get group name from ID
* get_gid_from_group: get group ID from name
"""


import os
import pwd
import grp


def get_current_user():
    """Return name of the current user

    Looks up user name for the current user.

    Returns:
      String: current user name or None if no matching
        name can be found.
    """
    try:
        return pwd.getpwuid(os.getuid()).pw_name
    except (KeyError, ValueError, OverflowError):
        return None


def get_user_from_uid(uid):
    """
    Return user name from UID

    Looks up user name matching the supplied UID.

    Arguments:
      uid (int): user ID

    Returns:
      String: user name or None.
    """
    try:
        return pwd.getpwuid(int(uid)).pw_name
    except (KeyError,ValueError,OverflowError):
        return None


def get_uid_from_user(user):
    """
    Return UID from user name

    Looks up UID matching the supplied user name;
    returns None if no matching name can be found.

    Arguments:
      user (str): user name

    Returns:
      Integer: matching UID or None.
    """
    try:
        return pwd.getpwnam(str(user)).pw_uid
    except KeyError:
        return None


def get_group_from_gid(gid):
    """
    Return group name from GID

    Looks up group name matching the supplied GID;
    returns None if no matching name can be found.

    Argument:
       gid (int): group ID (GID)

    Returns:
      String: group name or None.
    """
    try:
        return grp.getgrgid(int(gid)).gr_name
    except (KeyError,ValueError,OverflowError):
        return None


def get_gid_from_group(group):
    """
    Return GID from group name

    Looks up GID matching the supplied group name;
    returns None if no matching name can be found.

    Arguments:
      group (str): group name to look up

    Returns:
      Integer: GID or None.
    """
    try:
        return grp.getgrnam(group).gr_gid
    except KeyError as ex:
        return None