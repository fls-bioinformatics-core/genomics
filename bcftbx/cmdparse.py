########################################################################
#
# cmdparse.py
#
#########################################################################

"""
Legacy module retained for backwards compatibility.

All classes and functions previously provided by the ``cmdparse`` module
have been relocated to the ``utils.parser`` module (which should be
used in preference to this one).
"""

from .utils.parser import CommandParser
from .utils.parser import add_nprocessors_option
from .utils.parser import add_runner_option
from .utils.parser import add_no_save_option
from .utils.parser import add_dry_run_option
from .utils.parser import add_debug_option
from .utils.parser import add_arg