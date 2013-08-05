#!/bin/env python
#
#     rsync_seq_data.py: wrapper for rsync for sequencing data
#     Copyright (C) University of Manchester 2013 Peter Briggs
#
########################################################################
#
# rsync_seq_data.py
#
#########################################################################

"""rsync_seq_data.py

Wrapper for rsync for moving sequencing into the data storage area.

"""

#######################################################################
# Modules metadata
#######################################################################

__version__ = "0.0.4"

# Dictionary matching sequencing platforms to regexp patterns
# for specific instruments
PLATFORMS = {
    '^.*_ILLUMINA-73D9FA_.*$': 'illumina-ga2x',
    '^.*_SN7001250_.*$': 'hiseq',
    '^.*_SN700511R_.*$': 'hiseq',
    '^.*_M00879_.*$': 'miseq',
    '^solid0127_.*$': 'solid4',
    }

#######################################################################
# Import modules that this module depends on
#######################################################################

import os
import sys
import re
import time
import logging
import optparse
import subprocess

#######################################################################
# Functions
#######################################################################

def get_platform_from_name(sequencer_name):
    """Attempt to determine platform from sequencer name

    Checks the supplied sequencer name against the patterns in
    PLATFORMS and returns the first match (or None if no match
    is found).

    Arguments:
      sequencer_name: sequencer name (can include a leading
        directory path)

    Returns:
      Matching sequencer platform, or None.
    """
    name = os.path.split(sequencer_name)[-1]
    for pattern in PLATFORMS:
        if re.compile(pattern).match(name):
            return PLATFORMS[pattern]
    return None

def run_rsync(source,target,dry_run=False,mirror=False,chmod=None,
              log=None,err=None,excludes=None):
    """Wrapper for running the rsync command

    Create and execute an rsync command line to recursive copy/sync
    one directory (the 'source') into another (the 'target').

    The target can be a local directory or on a remote system (in which
    case it should be qualified with a user and hostname i.e.
    'user@hostname:target').

    Arguments:
      source: the directory being copied/sync'ed
      target: the directory the source will be copied into
      dry_run: run rsync using --dry-run option i.e. no files will
        be copied/sync'ed, just reported
      mirror: if True then run rsync in 'mirror' mode i.e. with
        --delete-after option (to remove files from the target
        that have also been removed from the source)
      chmod: optional, mode specification to be applied to the copied
        files e.g. chmod='u+rwX,g+rwX,o-w
      log: optional, name of a log file to record stdout from rsync;
        if None then write to stdout.
      err: optional, name of a log file to record stderr from rsync;
        if None then write to stderr.
      excludes: optional, a list of rsync filter patterns specifying
        files and directories to be excluded from the rsync

    Returns:
      The exit code from rsync (should be 0 if there were no errors).

    """
    # Build rsync command line
    rsync_cmd = ['rsync','-av']
    if dry_run:
        rsync_cmd.append('--dry-run')
    if mirror:
        rsync_cmd.append('--delete-after')
    if re.compile(r'^([^@]*@)?[^:]*:').match(target):
        # Remote destination, requires ssh
        rsync_cmd.extend(['-e','ssh'])
    if chmod is not None:
        rsync_cmd.append('--chmod=%s' % chmod)
    if excludes is not None:
        for exclude in excludes:
            rsync_cmd.append('--exclude=%s' % exclude)
    rsync_cmd.extend([source,target])
    print "Rsync command: %s" % ' '.join(rsync_cmd)
    if log is None:
        fpout = sys.stdout
    else:
        print "Writing stdout to %s" % log
        fpout = open(log,'w')
    if err is None:
        if log is not None:
            fperr = subprocess.STDOUT
        else:
            fperr = sys.stderr
    else:
        fperr = open(err,'w')
        print "Writing stderr to %s" % err
    # Execute rsync command and wait for finish
    try:
        p = subprocess.Popen(rsync_cmd,stdout=fpout,stderr=fperr)
        returncode = p.wait()
    except KeyboardInterrupt,ex:
        # Handle keyboard interrupt while rsync is running
        print "KeyboardInterrupt: stopping rsync process"
        p.kill()
        returncode = -1
    return returncode

#######################################################################
# Main program
#######################################################################

if __name__ == '__main__':
    p = optparse.OptionParser(usage="%prog [OPTIONS] DIR BASE_DIR",
                              version="%prog "+__version__,
                              description="Wrapper to rsync sequencing data: DIR will "
                              "be rsync'ed to a subdirectory of BASE_DIR constructed "
                              "from the year and platform i.e. BASE_DIR/YEAR/PLATFORM/. "
                              "YEAR will be the current year (over-ride using the "
                              "--year option), PLATFORM will be inferred from the "
                              "DIR name (over-ride using the --platform option). "
                              "The output from rsync is written to a file "
                              "rsync.DIR.log.")
    p.add_option('--platform',action="store",dest="platform",default=None,
                 help="explicitly specify the sequencer type")
    p.add_option('--year',action="store",dest="year",default=None,
                 help="explicitly specify the year (otherwise current year is assumed)")
    p.add_option('--dry-run',action="store_true",dest="dry_run",default=False,
                 help="run rsync with --dry-run option")
    p.add_option('--chmod',action='store',dest="chmod",default=None,
                 help="change file permissions using --chmod option of rsync (e.g "
                 "'u-w,g-w,o-w')")
    p.add_option('--exclude',action='append',dest="exclude_pattern",default=[],
                 help="specify a pattern which will exclude any matching files or "
                 "directories from the rsync")
    p.add_option('--mirror',action='store_true',dest="mirror",default=False,
                 help="mirror the source directory at the destination (update files "
                 "that have changed and remove any that have been deleted i.e. "
                 "rsync --delete-after)")
    p.add_option('--no-log',action='store_true',dest="no_log",default=False,
                 help="write rsync output directly stdout, don't create a log file")
    options,args = p.parse_args()
    if len(args) != 2:
        p.error("input is a source directory and a destination")
    # Locate source directory (and strip any trailing slash)
    data_dir = os.path.abspath(args[0].rstrip(os.sep))
    if not os.path.isdir(data_dir):
        logging.error("%s: doesn't exist or is not a directory" % data_dir)
        sys.exit(1)
    # Determine platform
    if options.platform is None:
        platform = get_platform_from_name(data_dir)
        if platform is None:
            logging.error("Can't determine platform: use --platform option?")
            sys.exit(1)
    else:
        platform = options.platform
    # Work out the destination
    if options.year is None:
        year = time.strftime("%Y")
    else:
        year = options.year
    destination = os.path.join(args[1],year,platform)
    # Log file
    if not options.no_log:
        log_file = "rsync.%s.log" % os.path.split(data_dir)[-1]
    else:
        log_file = None
    # Report settings
    print "Data dir   : %s" % data_dir
    print "Platform   : %s" % platform
    print "Destination: %s" % destination
    print "Log file   : %s" % log_file
    print "Mirror mode: %s" % options.mirror
    # Run rsync
    status = run_rsync(data_dir,destination,dry_run=options.dry_run,
                       log=log_file,chmod=options.chmod,mirror=options.mirror,
                       excludes=options.exclude_pattern)
    print "Rsync returncode: %s" % status
    if status != 0:
        logging.error("Rsync failure")
    sys.exit(status)
    
