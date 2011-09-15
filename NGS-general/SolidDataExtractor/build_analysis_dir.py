#!/bin/env python
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
import SolidDataExtractor

#######################################################################
# Class definitions
#######################################################################

class ExperimentList:
    """Container for a collection of Experiments

    Experiments are created and added to the ExperimentList by calling
    the addExperiment method, which returns a new Experiment object.

    The calling subprogram then populates the Experiment properties as
    appropriate.

    Once all Experiments are defined the analysis directory can be
    constructed by calling the buildAnalysisDirs method, which creates
    directories and symbolic links to primary data according to the
    definition of each experiment.
    """

    def __init__(self,solid_run_dir=None):
        """Create a new ExperimentList instance.

        Arguments:
          solid_run_dir: (optional) the path of the source SOLiD run
            directory.
        """
        self.experiments = []
        self.solid_run_dir = solid_run_dir
        self.solid_runs = []
        self.__getSolidRunData()

    def __getSolidRunData(self):
        """Get data about SOLiD runs

        Internal function to construct SolidRun objects based on the
        supplied SOLiD run directory.
        """
        if self.solid_run_dir is not None:
            logging.debug("Acquiring run information")
            for solid_dir in (self.solid_run_dir,self.solid_run_dir+"_2"):
                logging.debug("Examining %s" % solid_dir)
                run = SolidDataExtractor.SolidRun(solid_dir)
                if not run:
                    logging.debug("Unable to get run data for %s" % solid_dir)
                else:
                    self.solid_runs.append(run)
            if len(self.solid_runs) == 0:
                logging.warning("No run data found")

    def addExperiment(self,name):
        """Create a new Experiment and add to the list

        Arguments:
          name: the name of the new experiment

        Returns:
          New Experiment object with name already set
        """
        new_expt = Experiment()
        new_expt.name = name
        self.experiments.append(new_expt)
        return new_expt

    def addDuplicateExperiment(self,expt):
        """Duplicate an existing Experiment and add to the list

        Arguments:
          expt: an existing Experiment object

        Returns:
          New Experiment object with the same data as the input
        """
        new_expt = expt.copy()
        self.experiments.append(new_expt)
        return new_expt

    def getLastExperiment(self):
        """Return the last Experiment added to the list
        """
        try:
            return self.experiments[-1]
        except IndexError:
            return None

    def buildAnalysisDirs(self,top_dir=None,dry_run=False):
        """Construct and populate analysis directories for the experiments

        For each defined experiment, create the required analysis directories
        and populate with links to the primary data files.

        Arguments:
          top_dir: if set then create the analysis directories as
            subdirs of the specified directory; otherwise operate in cwd
          dry_run: if True then only report the mkdir, ln etc operations that
            would be performed. Default is False (do perform the operations).
        """
        # Deal with top_dir
        if top_dir:
            if os.path.exists(top_dir):
                logging.warning("Top directory %s already exists" % top_dir)
            else:
                if not dry_run:
                    # Create top directory
                    mkdir(top_dir)
                else:
                    # Report what would have been done
                    print "mkdir %s" % top_dir
        # For each experiment, make and populate directory
        for expt in self.experiments:
            expt_dir = expt.dirname(top_dir)
            logging.debug("Experiment dir: %s" % expt_dir)
            # Make directory
            if os.path.exists(expt_dir):
                logging.warning("Directory %s already exists" % expt_dir)
            else:
                if not dry_run:
                    # Create directory
                    mkdir(expt_dir)
                else:
                    # Report what would have been done
                    print "mkdir %s" % expt_dir
            # Locate the primary data
            for run in self.solid_runs:
                libraries = run.fetchLibraries(expt.sample,expt.library)
                for library in libraries:
                    # Look up primary data
                    ln_csfasta = getLinkName(library.csfasta,library)
                    ln_qual = getLinkName(library.qual,library)
                    logging.debug("Primary data:")
                    logging.debug("\t%s" % ln_csfasta)
                    logging.debug("\t%s" % ln_qual)
                    # Make links to primary data
                    self.__linkToFile(library.csfasta,os.path.join(expt_dir,ln_csfasta),dry_run=dry_run)
                    self.__linkToFile(library.qual,os.path.join(expt_dir,ln_qual),dry_run=dry_run)
    
    def __linkToFile(self,source,target,dry_run=False):
        """Create symbolic link to a file
        
        Internal function to make symbolic links to primary data. Checks that the
        target links don't already exist, or if they do that the current source
        file is the same as that specified in the method call.

        Arguments:
          source: the file to be linked to
          target: the name of the link pointing to source
          dry_run: if True then only report the actions that would be performed
            (default is False, perform the actions)
        """
        # Check if target file already exists
        if os.path.exists(target):
            logging.warning("Target file %s already exists" % target)
            # Test if the sources match
            if os.readlink(target) != source:
                logging.error("Different sources for %s" % target)
            return
        if not dry_run:
            # Make symbolic links
            mklink(source,target)
        else:
            # Report what would have been done
            print "ln -s %s %s" % (source,target)

    def __getitem__(self,key):
        return self.experiments[key]

    def __len__(self):
        return len(self.experiments)

class Experiment:
    """Class defining an experiment from a SOLiD run.

    An 'experiment' is a collection of related data.
    """
    def __init__(self):
        """Create a new Experiment instance.
        """
        self.name = None
        self.type = None
        self.sample = None
        self.library = None

    def dirname(self,top_dir=None):
        """Return directory name for experiment

        The directory name is the supplied name plus the experiment
        type joined by an underscore, unless no type was specified (in
        which case it is just the experiment name).

        If top_dir is also supplied then this will be prepended to the
        returned directory name.
        """
        if self.type:
            dirname = '_'.join((self.name,self.type))
        else:
            dirname = self.name
        if top_dir:
            return os.path.join(top_dir,dirname)
        else:
            return dirname

    def describe(self):
        """Describe the experiment as a set of command line options
        """
        options = ["--name=%s" % self.name]
        if self.type:
            options.append("--type=%s" % self.type)
        if self.sample:
            sample = self.sample
        else:
            sample = '*'
        if self.library:
            library = self.library
        else:
            library = '*'
        options.append("--source=%s/%s" % (sample,library))
        return ' '.join(options)

    def copy(self):
        """Return a new Experiment instance which is a copy of this one.
        """
        expt_copy = Experiment()
        expt_copy.name = self.name
        expt_copy.type = self.type
        expt_copy.sample = self.sample
        expt_copy.library = self.library
        return expt_copy

#######################################################################
# Module functions
#######################################################################

def getLinkName(filen,library):
    """Return the 'analysis' file name based on a source file name.
    
    The analysis file name is constructed as

    <instrument>_<datestamp>_<sample>_<library>.csfasta

    or

    <instrument>_<datestamp>_<sample>_<library>_QV.qual
    
    Arguments:
      filen: name of the source file
      library: SolidLibrary object representing the parent library (nb
         requires that the parent_sample of the library is set)

    Returns:
    Name for the analysis file.
    """
    # Construct new name
    sample = library.parent_sample
    link_filen_elements = [sample.parent_run.run_info.instrument,
                           sample.parent_run.run_info.datestamp,
                           sample.name,library.name]
    ext = os.path.splitext(filen)[1]
    if ext == ".qual":
        link_filen_elements.append("QV")
    link_filen = '_'.join(link_filen_elements) + ext
    return link_filen

# Filesystem wrappers

def mkdir(dirn):
    """Make a directory"""
    ##print "Making %s" % dirn
    if not os.path.isdir(dirn):
        os.mkdir(dirn)
        os.chmod(dirn,0775)

def mklink(target,link_name):
    """Make a symbolic link"""
    ##print "Linking to %s from %s" % (target,link_name)
    os.symlink(target,link_name)
    os.chmod(link_name,0664)

#######################################################################
# Main program
#######################################################################

if __name__ == "__main__":
    print "%s [OPTIONS] EXPERIMENT [EXPERIMENT ...] <solid_run_dir>" % \
        os.path.basename(sys.argv[0])
    print ""
    print "Build analysis directory structure for one or more 'experiments'"
    print "and populate with links to the primary data in <solid_run_dir>."
    print ""
    print "Options:"
    print "    --dry-run: report the operations that would be performed"
    print "    --debug: turn on debugging output"
    print "    --top-dir=<dir>: create analysis directories as subdirs of <dir>;"
    print "      otherwise create them in cwd."
    print ""
    print "Defining experiments:"
    print ""
    print "Each experiment is defined with a group of options (must be supplied"
    print "in this order for each):"
    print ""
    print "    --name=<name> [--type=<expt_type>] --source=<sample>/<library>"
    print "                                      [--source=... ]"
    print ""
    print "    <name> is an identifier (typically the user's initials) used"
    print "        for the analysis directory e.g. 'PB'"
    print "    <expt_type> is e.g. 'reseq', 'ChIP-seq', 'RNAseq', 'miRNA'..."
    print "    <sample>/<library> specify the names for primary data files"
    print "        e.g. 'PB_JB_pool/PB*'"
    print ""
    print "    Example:"
    print "        --name=PB --type=ChIP-seq --source=PB_JB_pool/PB*"
    print ""
    print "    Both <sample> and <library> can include a trailing wildcard"
    print "    character (i.e. *) to match multiple names. */* will match all"
    print "    primary data files. Multiple --sources can be declared for"
    print "    each experiment."
    print ""
    print "For each experiment defined on the command line, a subdirectory"
    print "called '<name>_<expt_type>' (e.g. 'PB_ChIP-seq' - if no <expt_type>"
    print "was supplied then just the name is used) will be made, and links to"
    print "each of the primary data files."

    # Initialise
    logging.basicConfig(format="%(levelname)s %(message)s")
    dry_run = False
    top_dir = None

    # Process command line
    if len(sys.argv) < 2:
        # Insuffient arguments
        sys.exit(1)

    # Solid run directory
    solid_run_dir = sys.argv[-1]
    if not os.path.isdir(solid_run_dir):
        logging.error("Solid run directory '%s' not found" % solid_run_dir)
        sys.exit(1)

    # Set up experiment list
    expts = ExperimentList(solid_run_dir=solid_run_dir)

    # Process command line arguments
    for arg in sys.argv[1:-1]:
        # Process command line arguments
        if arg.startswith('--name='):
            expt_name = arg.split('=')[1]
            expt = expts.addExperiment(expt_name)
        elif arg.startswith('--type='):
            expt = expts.getLastExperiment()
            if expt is None:
                print "No experiment defined for --type!"
                sys.exit(1)
            if not expt.type:
                expt.type = arg.split('=')[1]
            else:
                print "Type already defined for experiment!"
                sys.exit(1)
        elif arg.startswith('--source='):
            expt = expts.getLastExperiment()
            if expt is None:
                print "No experiment defined for --source!"
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
        elif arg == '--debug':
            logging.getLogger().setLevel(logging.DEBUG)
        elif arg.startswith('--top-dir='):
            top_dir = arg.split('=')[1]
        else:
            # Unrecognised argument
            print "Unrecognised argument: %s" % arg
            sys.exit(1)
            
    # Check there's something to do
    if not solid_run_dir:
        print "No SOLiD run directory specified, nothing to do"
        sys.exit(1)
    if not len(expts):
        print "No experiments defined, nothing to do"
        sys.exit(1)
    
    # Report
    print "%d experiments defined:" % len(expts)
    for expt in expts:
        print "\tName   : %s" % expt.name
        print "\tType   : %s" % expt.type
        print "\tSample : %s" % expt.sample
        print "\tLibrary: %s" % expt.library
        print "\tOptions: %s" % expt.describe()
        print ""

    # Check we have run data
    if not len(expts.solid_runs):
        print "No run data found!"
        sys.exit(1)

    # Build the analysis directory structure
    expts.buildAnalysisDirs(top_dir=top_dir,dry_run=dry_run)
            
