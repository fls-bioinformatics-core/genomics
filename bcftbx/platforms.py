#!/bin/env python
#
#     platforms.py: utilities and data to identify sequencer platforms
#     Copyright (C) University of Manchester 2013 Peter Briggs
#
########################################################################
#
# platforms.py
#
#########################################################################

"""platforms.py

Utilities and data to identify NGS sequencer platforms

"""

# Dictionary of sequencer platforms
from utils import OrderedDictionary
PLATFORMS = OrderedDictionary()
PLATFORMS['solid4'] = "SOLiD 4"
PLATFORMS['solid5500'] = "SOLiD 5500"
PLATFORMS['illumina-ga2x'] = "Illumina GAIIx"
PLATFORMS['hiseq'] = "Illumina HiSEQ"
PLATFORMS['miseq'] = "Illumina MiSEQ"
PLATFORMS['other'] = "Unknown/external"

# Dictionary matching sequencing platforms to regexp patterns
# for specific instruments
SEQUENCERS = {
    '^.*_ILLUMINA-73D9FA_.*$': 'illumina-ga2x',
    '^.*_SN7001250_.*$': 'hiseq',
    '^.*_SN700511R_.*$': 'hiseq',
    '^.*_M00879_.*$': 'miseq',
    '^solid0127_.*$': 'solid4',
    }

def list_platforms():
    """Return list of known platform names

    """
    return [x for x in PLATFORMS]

def get_sequencer_platform(sequencer_name):
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
    import os
    import re
    name = os.path.split(sequencer_name)[-1]
    for pattern in SEQUENCERS:
        if re.compile(pattern).match(name):
            return SEQUENCERS[pattern]
    return None
