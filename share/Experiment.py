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

    def buildAnalysisDirs(self,top_dir=None,dry_run=False,use_library_names=False):
        """Construct and populate analysis directories for the experiments

        For each defined experiment, create the required analysis directories
        and populate with links to the primary data files.

        Arguments:
          top_dir: if set then create the analysis directories as
            subdirs of the specified directory; otherwise operate in cwd
          dry_run: if True then only report the mkdir, ln etc operations that
            would be performed. Default is False (do perform the operations).
          use_library_names: if True then use the name of the library as the
            base for the links to csfasta and qual files; otherwise use the
            full instrument/datestamp/sample/library name combination (default).
        """
        # Deal with top_dir
        if top_dir:
            if os.path.exists(top_dir):
                print "Directory %s already exists" % top_dir
            else:
                if not dry_run:
                    # Create top directory
                    print "Creating %s" % top_dir
                    mkdir(top_dir)
                else:
                    # Report what would have been done
                    print "mkdir %s" % top_dir
        # For each experiment, make and populate directory
        for expt in self.experiments:
            print "Experiment: %s %s %s/%s" % (expt.name,expt.type,expt.sample,expt.library)
            expt_dir = expt.dirname(top_dir)
            print "\tDir: %s" % expt_dir
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
                paired_end = SolidData.is_paired_end(run)
                libraries = run.fetchLibraries(expt.sample,expt.library)
                for library in libraries:
                    # Look up primary data
                    if use_library_names:
                        ln_csfasta = "%s.csfasta" % library.name
                        ln_qual = "%s.qual" % library.name
                    else:
                        ln_csfasta = getLinkName(library.csfasta,library)
                        ln_qual = getLinkName(library.qual,library)
                    print "\t\t%s" % ln_csfasta
                    print "\t\t%s" % ln_qual
                    # Make links to primary data
                    self.__linkToFile(library.csfasta,os.path.join(expt_dir,ln_csfasta),
                                      dry_run=dry_run)
                    self.__linkToFile(library.qual,os.path.join(expt_dir,ln_qual),
                                      dry_run=dry_run)
                    # Reverse reads for paired-end run
                    if paired_end:
                        if use_library_names:
                            ln_csfasta = "%s_F5.csfasta" % library.name
                            ln_qual = "%s_F5.qual" % library.name
                        else:
                            ln_csfasta = getLinkName(library.csfasta_reverse,library,reverse=True)
                            ln_qual = getLinkName(library.qual_reverse,library,reverse=True)
                        print "\t\t%s" % ln_csfasta
                        print "\t\t%s" % ln_qual
                        # Make links to reverse read data
                        self.__linkToFile(library.csfasta_reverse,os.path.join(expt_dir,ln_csfasta),
                                          dry_run=dry_run)
                        self.__linkToFile(library.qual_reverse,os.path.join(expt_dir,ln_qual),
                                          dry_run=dry_run)
                        
    
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
            mklink(source,target,relative=True)
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

def getLinkName(filen,library,reverse=False):
    """Return the 'analysis' file name based on a source file name.
    
    The analysis file name is constructed as

    <instrument>_<datestamp>_<sample>_<library>.csfasta

    or

    <instrument>_<datestamp>_<sample>_<library>_QV.qual
    
    For reverse reads (indicated by the 'reverse' argument), there
    will be an additional '_F5' added to the name, e.g.:

    <instrument>_<datestamp>_<sample>_<library>_F5.csfasta

    Arguments:
      filen: name of the source file
      library: SolidLibrary object representing the parent library (nb
         requires that the parent_sample of the library is set)
      reverse: if True then indicates that this is a reverse read
         (default is False)

    Returns:
    Name for the analysis file.
    """
    # Construct new name
    sample = library.parent_sample
    link_filen_elements = [sample.parent_run.run_info.instrument,
                           sample.parent_run.run_info.datestamp,
                           sample.name,library.name]
    if reverse:
        link_filen_elements.append('F5')
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

def mklink(target,link_name,relative=False):
    """Make a symbolic link

    Arguments:
      target: the file or directory to link to
      link_name: name of the link
      relative: if True then make a relative link (if possible);
        otherwise link to the target as given (default)"""
    logging.debug("Linking to %s from %s" % (target,link_name))
    target_path = target
    if relative:
        # Try to construct relative link to target
        target_abs_path = os.path.abspath(target)
        link_abs_path = os.path.abspath(link_name)
        common_prefix = commonprefix(target_abs_path,link_abs_path)
        if common_prefix:
            # Use relpath to generate the relative path from the link
            # to the target
            target_path = os.path.relpath(target_abs_path,os.path.dirname(link_abs_path))
    os.symlink(target_path,link_name)
    chmod(link_name,0664)

def commonprefix(path1,path2):
    """Determine common prefix path for path1 and path2

    Can't use os.path.commonprefix as it checks characters not
    path components, so essentially it doesn't work as required.
    """
    path1_components = str(path1).split(os.sep)
    path2_components = str(path2).split(os.sep)
    common_components = []
    ncomponents = min(len(path1_components),len(path2_components))
    for i in range(ncomponents):
        if path1_components[i] == path2_components[i]:
            common_components.append(path1_components[i])
        else:
            break
    commonprefix = "%s" % os.sep.join(common_components)
    return commonprefix

def chmod(target,mode):
    """Change mode of file or directory"""
    logging.debug("Changing mode of %s to %s" % (target,mode))
    try:
        os.chmod(target,mode)
    except OSError, ex:
        logging.warning("Failed to change permissions on %s to %s: %s" % (target,mode,ex))
