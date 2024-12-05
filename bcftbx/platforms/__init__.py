#!/usr/bin/env python
#
#     platforms.py: utilities and data to identify sequencer platforms
#     Copyright (C) University of Manchester 2013-2024 Peter Briggs
#
########################################################################
#
# platforms
#
#########################################################################

"""
Utilities and data to identify NGS sequencer platforms
"""

# Dictionary of sequencer platforms
from ..utils import OrderedDictionary
PLATFORMS = OrderedDictionary()
PLATFORMS['solid4'] = "SOLiD 4"
PLATFORMS['solid5500'] = "SOLiD 5500"
PLATFORMS['illumina-ga2x'] = "Illumina GAIIx"
PLATFORMS['hiseq4000'] = "Illumina HISeq 4000"
PLATFORMS['hiseq'] = "Illumina HISeq"
PLATFORMS['miseq'] = "Illumina MISeq"
PLATFORMS['miniseq'] = "MiniSeq"
PLATFORMS['nextseq'] = "Illumina NextSeq"
PLATFORMS['novaseq6000'] = "NovaSeq 6000"
PLATFORMS['iseq'] = "Illumina iSeq"
PLATFORMS['illumina'] = "Unknown/Illumina"
PLATFORMS['other'] = "Unknown/external"

# Expected run completion files for different platforms
RUN_COMPLETION_FILES = {
    'default': ("RTAComplete.txt",),
    'solid4': tuple(),
    'solid5500': tuple(),
    'hiseq4000': ("RTAComplete.txt",
                  "SequencingComplete.txt"),
    'nextseq': ("CopyComplete.txt",
                "RTAComplete.txt",),
    'novaseq6000': ("CopyComplete.txt",
                    "RTAComplete.txt",
                    "SequenceComplete.txt"),
}

# Dictionary matching sequencing platforms to regexp patterns
# for specific instruments
SEQUENCERS = {
    '^.*_ILLUMINA-73D9FA_.*$': 'illumina-ga2x',
    '^.*_SN7001250_.*$': 'hiseq',
    '^.*_SN700511R_.*$': 'hiseq',
    '^.*_K00311_.*$': 'hiseq4000',
    '^.*_M00879_.*$': 'miseq',
    '^.*_NB500968_.*$': 'nextseq',
    '^.*_MN00218_.*$': 'miniseq',
    '^solid0127_.*$': 'solid4',
    }

def list_platforms():
    """Return list of known platform names

    """
    return [x for x in PLATFORMS]

def get_run_completion_files(platform):
    """
    Return a list of files indication run completion

    Given a platform name, return a list of the files
    that are used to indicate when the run is complete.

    Arguments:
      platform (str): name of the sequencing platform
        (e.g. 'novaseq6000')

    Returns:
      Tuple: list of run completion files for the
        specified platform.
    """
    try:
        return RUN_COMPLETION_FILES[platform]
    except KeyError:
        return RUN_COMPLETION_FILES['default']

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
