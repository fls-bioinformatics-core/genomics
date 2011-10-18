#!/bin/env python
#
#     Experiment.py: classes for defining SOLiD sequencing experiments
#     Copyright (C) University of Manchester 2011 Peter Briggs
#
########################################################################
#
# Experiment.py
#
#########################################################################

"""Experiment.py

The Experiment module provides two classes: the Experiment class defines
a single experiment (essentially a collection of one or more related
primary data sets) from a SOLiD run; the ExperimentList class is a
collection of experiments which are typically part of the same SOLiD run.
"""

#######################################################################
# Import modules that this module depends on
#######################################################################

import os
import logging
import SolidData

# Put ../QC-pipeline onto Python search path for modules
import sys
QC_DIR =  os.path.abspath(
    os.path.normpath(
        os.path.join(os.path.dirname(sys.argv[0]),'..','QC-pipeline')))
sys.path.append(QC_DIR)
try:
    import run_qc_pipeline
except ImportError, ex:
    print "Error importing modules: %s" % ex

#######################################################################
# Class definitions
#######################################################################

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
                run = SolidData.SolidRun(solid_dir)
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

    def runPipeline(self,script,top_dir=None):
        """Run a pipeline script on the experiment directories

        Create a SolidPipelineRunner and add the data files from each experiment,
        then run the specified script.

        Arguments:
          script: script file to run (can be full or relative path)
          top_dir: (optional) if set then look for the analysis directories as
            subdirs of the specified directory; otherwise operate in cwd
        """
        pipeline = run_qc_pipeline.SolidPipelineRunner(script)
        for expt in self.experiments:
            pipeline.addDir(os.path.abspath(expt.dirname(top_dir)))
        pipeline.run()
        print "%s" % pipeline.report()
    
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
    logging.debug("Making %s" % dirn)
    if not os.path.isdir(dirn):
        os.mkdir(dirn)
        chmod(dirn,0775)

def mklink(target,link_name):
    """Make a symbolic link"""
    logging.debug("Linking to %s from %s" % (target,link_name))
    os.symlink(target,link_name)
    chmod(link_name,0664)

def chmod(target,mode):
    """Change mode of file or directory"""
    logging.debug("Changing mode of %s to %s" % (target,mode))
    try:
        os.chmod(target,mode)
    except OSError, ex:
        logging.warning("Failed to change permissions on %s to %s: %s" % (target,mode,ex))
