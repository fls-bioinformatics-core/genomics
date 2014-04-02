#!/bin/env python
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

__version__ = "1.1.0"

#######################################################################
# Import modules that this module depends on
#######################################################################

import os
import re
import logging
import optparse
import bcf_utils

#######################################################################
# Main program
#######################################################################

if __name__ == "__main__":

    # Logging
    logging.basicConfig(format="%(levelname)s: %(message)s")

    # Command line processing
    p = optparse.OptionParser(usage="%prog OPTIONS DIR",
                              version="%prog "+__version__,
                              description="Recursively check and optionally update symlinks "
                              "found under directory DIR")
    p.add_option("--absolute",action="store_true",dest="absolute",default=False,
                 help="report absolute symlinks")
    p.add_option("--broken",action="store_true",dest="broken",default=False,
                 help="report broken symlinks")
    p.add_option("--find",action="store",dest="regex_pattern",default=None,
                 help="report links where the destination matches the supplied REGEX_PATTERN")
    p.add_option("--replace",action="store",dest="new_path",default=None,
                 help="update links found by --find options, by substituting REGEX_PATTERN "
                 "with NEW_PATH")
    options,args = p.parse_args()

    # Check arguments and options
    if len(args) != 1:
        p.error("Takes a single directory as input")
    elif not os.path.isdir(args[0]):
        p.error("'%s': not a directory" % args[0])
    if options.regex_pattern is not None:
        regex = re.compile(options.regex_pattern)

    # Examine links in the directory structure
    for l in bcf_utils.links(args[0]):
        link = bcf_utils.Symlink(l)
        logging.debug("%s -> %s" % (link,link.target))
        if options.broken and link.is_broken:
            # Broken link
            logging.warning("Broken link:\t%s -> %s" % (link,link.target))
        elif options.absolute and link.is_absolute:
            # Absolute link
            logging.warning("Absolute link:\t%s -> %s" % (link,link.target))
        if options.regex_pattern is not None:
            # Check if target matches pattern
            if regex.search(link.target):
                print "Matched pattern:\t%s -> %s" % (link,link.target)
                if options.new_path is not None:
                    # Update target
                    new_target = regex.sub(options.new_path,link.target)
                    link.update_target(new_target)
                    print "Updated:\t%s -> %s" % (link,link.target)

                
