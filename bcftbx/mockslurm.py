#     mockslurm.py: mock Slurm functionality for testing
#     Copyright (C) University of Manchester 2025-2026 Peter Briggs
#
#######################################################################


"""
Legacy module providing utility classes and functions for simulating
Slurm functionality.
"""


#######################################################################
# Classes
#######################################################################

from .mock.slurm import MockSlurm

#######################################################################
# Functions
#######################################################################

from .mock.slurm import _make_mock_slurm_exe
from .mock.slurm import setup_mock_slurm