#!/bin/env python
#
#     symlink_checker.py: check and update symbolic links
#     Copyright (C) University of Manchester 2012 Peter Briggs
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

__version__ = "0.0.1"

#######################################################################
# Import modules that this module depends on
#######################################################################

import os
import re
import logging
import optparse

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
    p.add_option("--broken",action="store_true",dest="broken",default=False,
                 help="report broken symlinks")
    p.add_option("--find",action="store",dest="regex_pattern",default=None,
                 help="report links where the destination matches the supplied REGEX_PATTERN")
    p.add_option("--replace",action="store",dest="new_string",default=None,
                 help="update links found by --find options, by substituting REGEX_PATTERN "
                 "with NEW_STRING")
    options,args = p.parse_args()

    # Check arguments and options
    if len(args) != 1:
        p.error("Takes a single directory as input")
    elif not os.path.isdir(args[0]):
        p.error("'%s': not a directory" % args[0])
    if options.regex_pattern is not None:
        regex = re.compile(options.regex_pattern)

    # Walk the directory structure looking for links
    for d in os.walk(args[0]):
        dirpath, dirnames, filenames = d
        logging.debug("%s" % dirpath)
        for f in filenames:
            filepath = os.path.join(dirpath,f)
            if os.path.islink(filepath):
                # Extract link destination and generate absolute path
                realpath = os.readlink(filepath)
                if not os.path.isabs(realpath):
                    fullpath = os.path.abspath(os.path.join(dirpath,realpath))
                else:
                    fullpath = realpath
                logging.debug("\t%s -> %s" % (filepath,realpath))
                if options.broken:
                    # Check if link is broken
                    if not os.path.exists(fullpath):
                        logging.warning("broken link: %s -> %s" % (filepath,realpath))
                if options.regex_pattern is not None:
                    # Check if link matches pattern
                    if regex.search(realpath):
                        if options.new_string is None:
                            # Just report
                            print "%s -> %s" % (filepath,realpath)
                        else:
                            # Update link
                            realpath = regex.sub(options.new_string,realpath)
                            print "Updated: %s -> %s" % (filepath,realpath)
                            os.unlink(filepath)
                            os.symlink(realpath,filepath)
                
