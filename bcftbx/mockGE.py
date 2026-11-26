#     mockGE.py: mock Grid Engine functionality for testing
#     Copyright (C) University of Manchester 2018-2020 Peter Briggs
#
#######################################################################


"""
Legacy module providing utility classes and functions for simulating
Grid Engine (GE) functionality.
"""


#######################################################################
# Classes
#######################################################################

from .mock.gridengine import MockGE

#######################################################################
# Functions
#######################################################################

from .mock.gridengine import _make_mock_ge_exe as _make_mock_GE_exe
from .mock.gridengine import setup_mock_ge as setup_mock_GE