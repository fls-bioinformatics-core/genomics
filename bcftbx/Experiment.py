#!/usr/bin/env python
#
#     Experiment.py: classes for defining SOLiD sequencing experiments
#     Copyright (C) University of Manchester 2011-2019 Peter Briggs
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
import utils

#######################################################################
# Class definitions
#######################################################################

class Experiment(object):
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

class ExperimentList(object):
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

    def buildAnalysisDirs(self,top_dir=None,dry_run=False,link_type="relative",
                          naming_scheme="partial"):
        """Construct and populate analysis directories for the experiments

        For each defined experiment, create the required analysis directories
        and populate with links to the primary data files.

        Arguments:
          top_dir: if set then create the analysis directories as
            subdirs of the specified directory; otherwise operate in cwd
          dry_run: if True then only report the mkdir, ln etc operations that
            would be performed. Default is False (do perform the operations).
          link_type: type of link to use when linking to primary data, one of
            'relative' or 'absolute'.
          naming_scheme: naming scheme to use for links to primary data, one of
            'full' (same names as primary data files), 'partial' (cut-down version
            of the full name which excludes sample names - the default), or
            'minimal' (just the library name).
        """
        # Deal with top_dir
        if top_dir:
            if os.path.exists(top_dir):
                print("Directory %s already exists" % top_dir)
            else:
                if not dry_run:
                    # Create top directory
                    print("Creating %s" % top_dir)
                    utils.mkdir(top_dir,mode=0775)
                else:
                    # Report what would have been done
                    print("mkdir %s" % top_dir)
        # Type of link
        if link_type == 'absolute':
            use_relative_links = False
        else:
            use_relative_links = True
        # For each experiment, make and populate directory
        for expt in self.experiments:
            print("Experiment: %s %s %s/%s" % (expt.name,
                                               expt.type,
                                               expt.sample,
                                               expt.library))
            expt_dir = expt.dirname(top_dir)
            print("\tDir: %s" % expt_dir)
            # Make directory
            if os.path.exists(expt_dir):
                logging.warning("Directory %s already exists" % expt_dir)
            else:
                if not dry_run:
                    # Create directory
                    utils.mkdir(expt_dir,mode=0775)
                else:
                    # Report what would have been done
                    print("mkdir %s" % expt_dir)
            # Locate the primary data
            for run in self.solid_runs:
                paired_end = SolidData.is_paired_end(run)
                libraries = run.fetchLibraries(expt.sample,expt.library)
                for library in libraries:
                    # Get names for links to primary data - F3
                    ln_csfasta,ln_qual = LinkNames(naming_scheme).names(library)
                    print("\t\t%s" % ln_csfasta)
                    print("\t\t%s" % ln_qual)
                    # Make links to primary data
                    try:
                        self.__linkToFile(library.csfasta,os.path.join(expt_dir,ln_csfasta),
                                          relative=use_relative_links,dry_run=dry_run)
                        self.__linkToFile(library.qual,os.path.join(expt_dir,ln_qual),
                                          relative=use_relative_links,dry_run=dry_run)
                    except Exception, ex:
                        logging.error("Failed to link to some or all F3 primary data")
                        logging.error("Exception: %s" % ex)
                    # Get names for links to F5 reads (if paired-end run)
                    if paired_end:
                        ln_csfasta,ln_qual = LinkNames(naming_scheme).names(library,F5=True)
                        print("\t\t%s" % ln_csfasta)
                        print("\t\t%s" % ln_qual)
                        # Make links to F5 read data
                        try:
                            self.__linkToFile(library.csfasta_f5,os.path.join(expt_dir,ln_csfasta),
                                              relative=use_relative_links,dry_run=dry_run)
                            self.__linkToFile(library.qual_f5,os.path.join(expt_dir,ln_qual),
                                              relative=use_relative_links,dry_run=dry_run)
                        except Exception, ex:
                            logging.error("Failed to link to some or all F5 primary data")
                            logging.error("Exception: %s" % ex)
            # Make an empty ScriptCode directory
            scriptcode_dir = os.path.join(expt_dir,"ScriptCode")
            if os.path.exists(scriptcode_dir):
                logging.warning("Directory %s already exists" % scriptcode_dir)
            else:
                if not dry_run:
                    # Create directory
                    utils.mkdir(scriptcode_dir,mode=0775)
                else:
                    # Report what would have been done
                    print("mkdir %s" % scriptcode_dir)
    
    def __linkToFile(self,source,target,relative=True,dry_run=False):
        """Create symbolic link to a file
        
        Internal function to make symbolic links to primary data. Checks that the
        target links don't already exist, or if they do that the current source
        file is the same as that specified in the method call.

        Arguments:
          source: the file to be linked to
          target: the name of the link pointing to source
          relative: if True then make a relative link (if possible); otherwise
            link to the target as given (default)
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
            utils.mklink(source,target,relative=relative)
        else:
            # Report what would have been done
            print("ln -s %s %s" % (source,target))

    def __getitem__(self,key):
        return self.experiments[key]

    def __len__(self):
        return len(self.experiments)

class LinkNames(object):
    """Class to construct names for links to primary data files

    The LinkNames class encodes a set of naming schemes that are used to
    construct names for the links in the analysis directories that point
    to the primary CFASTA and QUAL data files.

    The schemes are:

      full:    link name is the same as the source file, e.g.
               solid0123_20111014_FRAG_BC_AB_CD_EF_pool_F3_CD_PQ5.csfasta

      partial: link name consists of the instrument name, datestamp and
               library name, e.g.
               solid0123_20111014_CD_PQ5.csfasta

      minimal: link name consists of just the library name, e.g.
               CD_PQ5.csfasta

    For paired-end data, the 'partial' and 'minimal' names have '_F3' and
    '_F5' appended as appropriate (full names already have this distinction).

    Example usage:

    To get the link names using the minimal scheme for the F3 reads ('library'
    is a SolidLibrary object):

    >>> csfasta_lnk,qual_lnk = LinkNames('minimal').names(library)

    To get names for the F5 reads using the partial scheme:

    >>> csfasta_lnk,qual_lnk = LinkNames('partial').names(library,F5=True)
    """
    
    def __init__(self,scheme):
        """Create a new LinkNames instance

        Argments:
          scheme: naming scheme, one of 'full', 'partial' or
            'minimal'
        """
        # Default
        self.__names = self.__full_names
        # Assign according to requested scheme
        if scheme == "minimal":
            self.__names = self.__minimal_names
        elif scheme == "partial":
            self.__names = self.__partial_names
        elif scheme == "full":
            self.__names = self.__full_names

    def names(self,library,F5=False):
        """Get names for links to the primary data in a library

        Returns a tuple of link names:

        (csfasta_link_name,qual_link_name)

        derived from the data in the library plus the naming scheme
        specified when the LinkNames object was created.
        
        Arguments:
          library: SolidLibrary object
          F5: if True then indicates that names should be returned
            for linking to the F5 reads (default is F3 reads)
        """
        return self.__names(library,F5)

    def __minimal_names(self,library,F5):
        """Internal: link names based on 'minimal' naming scheme
        """
        # Alternative naming schemes for primary data for links
        run = library.parent_sample.parent_run
        if not SolidData.is_paired_end(run):
            # Library names alone
            return ("%s.csfasta" % library.name,
                    "%s.qual" % library.name)
        else:
            # Add F3/F5 to distinguish the samples
            if not F5:
                return ("%s_F3.csfasta" % library.name,
                        "%s_F3.qual" % library.name)
            else:
                return ("%s_F5.csfasta" % library.name,
                        "%s_F5.qual" % library.name)

    def __partial_names(self,library,F5):
        """Internal: link names based on 'partial' naming scheme
        """
        run = library.parent_sample.parent_run
        name = '_'.join([run.run_info.instrument,
                         run.run_info.datestamp,
                         library.name])
        if not SolidData.is_paired_end(run):
            return ("%s.csfasta" % name,
                    "%s_QV.qual" % name)
        else:
            # Add F3/F5 to distinguish the samples
            if not F5:
                return ("%s_F3.csfasta" % name,
                        "%s_F3_QV.qual" % name)
            else:
                return ("%s_F5.csfasta" % name,
                        "%s_F5_QV.qual" % name)

    def __full_names(self,library,F5):
        """Internal: link names based on 'full' naming scheme
        """
        run = library.parent_sample.parent_run
        if not SolidData.is_paired_end(run):
            return (os.path.basename(library.csfasta),
                    os.path.basename(library.qual))
        else:
            if not F5:
                return (os.path.basename(library.csfasta),
                        os.path.basename(library.qual))
            else:
                return (os.path.basename(library.csfasta_f5),
                        os.path.basename(library.qual_f5))

#######################################################################
# Module functions
#######################################################################

# None defined
