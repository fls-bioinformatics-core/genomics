#!/usr/bin/env python
#
#     build_analysis_dir.py: build directory with links to primary data
#     Copyright (C) University of Manchester 2011 Peter Briggs
#
########################################################################
#
# build_analysis_dir.py
#
#########################################################################

"""build_analysis_dir.py
"""

#######################################################################
# Import modules that this module depends on
#######################################################################

import sys,os
import logging
logging.basicConfig(format="%(levelname)s %(message)s")

# Put .. onto Python search path for modules
SHARE_DIR = os.path.abspath(
    os.path.normpath(
        os.path.join(os.path.dirname(sys.argv[0]),'..')))
sys.path.append(SHARE_DIR)
import bcftbx.SolidData as SolidData
import bcftbx.Experiment as Experiment
import bcftbx.JobRunner as JobRunner
import bcftbx.Pipeline as Pipeline

#######################################################################
# Class definitions
#######################################################################

# No classes defined

#######################################################################
# Module functions
#######################################################################

# No functions defined

#######################################################################
# Main program
#######################################################################

if __name__ == "__main__":

    # Initialise
    dry_run = False
    top_dir = None
    pipeline_script = None
    link_naming_scheme = "partial"
    link_type = "absolute"

    # Process command line
    if len(sys.argv) < 2:
        # Insuffient arguments
        print("%s [OPTIONS] EXPERIMENT [EXPERIMENT ...] <solid_run_dir>" %
              os.path.basename(sys.argv[0]))
        print("")
        print("Build analysis directory structure for one or more 'experiments'")
        print("and populate with links to the primary data in <solid_run_dir>.")
        print("")
        print("Options:")
        print("    --dry-run: report the operations that would be performed")
        print("    --debug: turn on debugging output")
        print("    --top-dir=<dir>: create analysis directories as subdirs of <dir>;")
        print("      otherwise create them in cwd.")
        print("    --naming-scheme=<scheme>: specify naming scheme for links to")
        print("      primary data (one of 'minimal' - library names only, 'partial' -")
        print("      includes instrument name, datestamp and library name (default)")
        print("      or 'full' - same as source data file")
        print("    --link=<type>: type of links to create to primary data files,")
        print("      either 'absolute' (default) or 'relative'")
        print("    --run-pipeline=<script>: after creating analysis directories, run")
        print("      the specified <script> on SOLiD data file pairs in each")
        print("")
        print("Defining experiments:")
        print("")
        print("Each experiment is defined with a group of options (must be supplied")
        print("in this order for each):")
        print("")
        print("    --name=<name> [--type=<expt_type>] --source=<sample>/<library>")
        print("                                      [--source=... ]")
        print("")
        print("    <name> is an identifier (typically the user's initials) used")
        print("        for the analysis directory e.g. 'PB'")
        print("    <expt_type> is e.g. 'reseq', 'ChIP-seq', 'RNAseq', 'miRNA'...")
        print("    <sample>/<library> specify the names for primary data files")
        print("        e.g. 'PB_JB_pool/PB*'")
        print("")
        print("    Example:")
        print("        --name=PB --type=ChIP-seq --source=PB_JB_pool/PB*")
        print("")
        print("    Both <sample> and <library> can include a trailing wildcard")
        print("    character (i.e. *) to match multiple names. */* will match all")
        print("    primary data files. Multiple --sources can be declared for")
        print("    each experiment.")
        print("")
        print("For each experiment defined on the command line, a subdirectory")
        print("called '<name>_<expt_type>' (e.g. 'PB_ChIP-seq' - if no <expt_type>")
        print("was supplied then just the name is used) will be made, and links to")
        print("each of the primary data files.")
        sys.exit(1)

    # Solid run directory
    solid_run_dir = sys.argv[-1]
    if not os.path.isdir(solid_run_dir):
        logging.error("Solid run directory '%s' not found" % solid_run_dir)
        sys.exit(1)

    # Set up experiment list
    expts = Experiment.ExperimentList(solid_run_dir=solid_run_dir)

    # Process command line arguments
    for arg in sys.argv[1:-1]:
        # Process command line arguments
        if arg.startswith('--name='):
            expt_name = arg.split('=')[1]
            expt = expts.addExperiment(expt_name)
        elif arg.startswith('--type='):
            expt = expts.getLastExperiment()
            if expt is None:
                logging.error("No experiment defined for --type argument")
                sys.exit(1)
            if not expt.type:
                expt.type = arg.split('=')[1]
            else:
                logging.error("Type already defined for experiment")
                sys.exit(1)
        elif arg.startswith('--source='):
            expt = expts.getLastExperiment()
            if expt is None:
                logging.error("No experiment defined for --source argument")
                sys.exit(1)
            if expt.sample:
                # Duplicate the previous experiment
                expt = expts.addDuplicateExperiment(expt)
            # Extract sample and library
            source = arg.split('=')[1]
            try:
                i = source.index('/')
                expt.sample = source.split('/')[0]
                expt.library = source.split('/')[1]
            except ValueError:
                expt.sample = source
        elif arg == '--dry-run':
            dry_run = True
        elif arg.startswith('--naming-scheme='):
            link_naming_scheme = arg.split('=')[1]
        elif arg == '--debug':
            logging.getLogger().setLevel(logging.DEBUG)
        elif arg.startswith('--top-dir='):
            top_dir = arg.split('=')[1]
        elif arg.startswith('--link='):
            link_type = arg.split('=')[1]
        elif arg.startswith('--run-pipeline='):
            pipeline_script = arg.split('=')[1]
        else:
            # Unrecognised argument
            logging.error("Unrecognised argument: %s" % arg)
            sys.exit(1)
            
    # Check there's something to do
    if not solid_run_dir:
        logging.error("No SOLiD run directory specified")
        sys.exit(1)
    if not len(expts):
        logging.error("No experiments defined")
        sys.exit(1)

    # Verify link type
    if link_type not in ('relative','absolute'):
        logging.error("Unrecognised link type: '%s'" % link_type)
        sys.exit(1)
    
    # Report
    if dry_run:
        print("%d experiments defined:" % len(expts))
        for expt in expts:
            print("\tName   : %s" % expt.name)
            print("\tType   : %s" % expt.type)
            print("\tSample : %s" % expt.sample)
            print("\tLibrary: %s" % expt.library)
            print("\tOptions: %s" % expt.describe())
            print("")

    # Check we have run data
    if not len(expts.solid_runs):
        logging.error("No run data found!")
        sys.exit(1)

    # Build the analysis directory structure
    expts.buildAnalysisDirs(top_dir=top_dir,dry_run=dry_run,
                            link_type=link_type,
                            naming_scheme=link_naming_scheme)
            
    # Run the pipeline script
    if pipeline_script:
        runner = JobRunner.GEJobRunner()
        pipeline = Pipeline.SolidPipelineRunner(runner,pipeline_script)
        for expt in expts:
            pipeline.addDir(os.path.abspath(expt.dirname(top_dir)))
        pipeline.run()
        print("%s" % pipeline.report())

