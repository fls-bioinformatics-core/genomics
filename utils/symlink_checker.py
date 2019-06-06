#!/usr/bin/env python
#
#     symlink_checker.py: check and update symbolic links
#     Copyright (C) University of Manchester 2012-2014 Peter Briggs
#
########################################################################
#
# symlink_checker.py
#
#########################################################################

"""symlink_checker

Utility for checking and updating symbolic links.
"""

#######################################################################
# Module metadata
#######################################################################

__version__ = "1.2.0"

#######################################################################
# Import modules that this module depends on
#######################################################################

import sys
import os
import re
import logging
import argparse
# Put .. onto Python search path for modules
SHARE_DIR = os.path.abspath(
    os.path.normpath(
        os.path.join(os.path.dirname(sys.argv[0]),'..')))
sys.path.append(SHARE_DIR)
import bcftbx.utils

#######################################################################
# Main program
#######################################################################

if __name__ == "__main__":

    # Logging
    logging.basicConfig(format="%(levelname)s: %(message)s")

    # Command line processing
    p = argparse.ArgumentParser(version="%(prog)s "+__version__,
                                description="Recursively check and "
                                "optionally update symlinks "
                                "found under directory DIR")
    p.add_argument("--absolute",action="store_true",dest="absolute",
                   default=False,
                   help="report absolute symlinks")
    p.add_argument("--broken",action="store_true",dest="broken",
                   default=False,
                   help="report broken symlinks")
    p.add_argument("--find",action="store",dest="regex_pattern",
                   default=None,
                   help="report links where the destination matches the "
                   "supplied REGEX_PATTERN")
    p.add_argument("--replace",action="store",dest="new_path",
                   default=None,
                   help="update links found by --find options, by "
                   "substituting REGEX_PATTERN with NEW_PATH")
    p.add_argument('dirn',metavar="DIR",
                   help="directory under which to check symlinks")
    args = p.parse_args()

    # Check arguments and options
    if not os.path.isdir(args.dirn):
        p.error("'%s': not a directory" % args[0])
    if args.regex_pattern is not None:
        regex = re.compile(args.regex_pattern)

    # Examine links in the directory structure
    for l in bcftbx.utils.links(args[0]):
        link = bcftbx.utils.Symlink(l)
        logging.debug("%s -> %s" % (link,link.target))
        if args.broken and link.is_broken:
            # Broken link
            logging.warning("Broken link:\t%s -> %s" % (link,link.target))
        elif args.absolute and link.is_absolute:
            # Absolute link
            logging.warning("Absolute link:\t%s -> %s" % (link,link.target))
        if args.regex_pattern is not None:
            # Check if target matches pattern
            if regex.search(link.target):
                print "Matched pattern:\t%s -> %s" % (link,link.target)
                if args.new_path is not None:
                    # Update target
                    new_target = regex.sub(args.new_path,link.target)
                    link.update_target(new_target)
                    print "Updated:\t%s -> %s" % (link,link.target)

                
