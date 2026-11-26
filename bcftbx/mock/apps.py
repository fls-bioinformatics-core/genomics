#!/usr/bin/env python3
#
#     mock.apps.py: mock applications for testing
#     Copyright (C) University of Manchester 2026 Peter Briggs
#
########################################################################
#
# mock.illumina.py
#
#########################################################################

"""
Provides classes for mocking external applications and software,
to be used in testing.

There is a function for mocking the STAR aligner:

- mock_star: driver function for a "mock" STAR executable
"""


import argparse


def mock_star(argv,unmapped_output=False):
    """
    Driver function for a "mock" STAR executable

    The mock executable should be a file with the
    following content:

    ::

        #!/bin/bash
        export PYTHONPATH=%s:$PYTHONPATH
        python -c "import sys ; from bcftbx.mock.apps import mock_star ; mock_star(sys.argv[1:],unmapped_output=%s)" $@

    When executed it produces  a single output
    (ReadsPerGene.out.tab file).

    Arguments:
      argv (list): command line to be used as input
      unmapped_output (bool): if True then produce
        mock "unmapped" output
    """
    p = argparse.ArgumentParser(argv)
    p.add_argument('--runMode',action="store")
    p.add_argument('--genomeLoad',action="store")
    p.add_argument('--genomeDir',action="store")
    p.add_argument('--readFilesIn',action="store",nargs='+')
    p.add_argument('--quantMode',action="store")
    p.add_argument('--outSAMtype',action="store",nargs=2)
    p.add_argument('--outSAMstrandField',action="store")
    p.add_argument('--outFileNamePrefix',action="store",dest='prefix')
    p.add_argument('--runThreadN',action="store")
    args = p.parse_args(argv)
    with open("%sReadsPerGene.out.tab" % args.prefix,'wt') as fp:
        if not unmapped_output:
            fp.write(u"""N_unmapped	2026581	2026581	2026581
N_multimapping	4020538	4020538	4020538
N_noFeature	8533504	24725707	8782932
N_ambiguous	618069	13658	192220
ENSMUSG00000102592.1	0	0	0
ENSMUSG00000088333.2	0	0	0
ENSMUSG00000103265.1	4	0	4
ENSMUSG00000103922.1	23	23	0
ENSMUSG00000033845.13	437	0	437
ENSMUSG00000102275.1	19	0	19
ENSMUSG00000025903.14	669	2	667
ENSMUSG00000104217.1	0	0	0
ENSMUSG00000033813.15	805	0	805
ENSMUSG00000062588.4	11	11	0
ENSMUSG00000103280.1	9	9	0
ENSMUSG00000002459.17	3	3	0
ENSMUSG00000064363.1	74259	393	73866
ENSMUSG00000064364.1	0	0	0
ENSMUSG00000064365.1	0	0	0
ENSMUSG00000064366.1	0	0	0
ENSMUSG00000064367.1	148640	7892	152477
ENSMUSG00000064368.1	44003	42532	13212
ENSMUSG00000064369.1	6	275	6
ENSMUSG00000064370.1	122199	199	123042
""")
        else:
            fp.write(u"""N_unmapped	1	1	1
N_multimapping	0	0	0
N_noFeature	0	0	0
N_ambiguous	0	0	0
ENSG00000223972.5	0	0	0
ENSG00000227232.5	0	0	0
ENSG00000278267.1	0	0	0
ENSG00000243485.3	0	0	0
ENSG00000274890.1	0	0	0
ENSG00000237613.2	0	0	0
ENSG00000268020.3	0	0	0
ENSG00000240361.1	0	0	0
ENSG00000186092.4	0	0	0
ENSG00000238009.6	0	0	0
""")