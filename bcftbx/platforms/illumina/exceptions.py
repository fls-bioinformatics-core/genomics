#!/usr/bin/env python3
#
#     platforms.illumina.exceptions.py: custom Illumina-related exceptions
#     Copyright (C) University of Manchester 2011-2025 Peter Briggs
#
########################################################################
#
# platforms.illumina.exceptions.py
#
#########################################################################

"""
"""

#######################################################################
# Imports
#######################################################################

#######################################################################
# Classes
#######################################################################

class IlluminaError(Exception):
    """Base class for errors with Illumina-related code"""


class IlluminaPlatformError(IlluminaError):
    """Exception for errors due to platform issues"""
