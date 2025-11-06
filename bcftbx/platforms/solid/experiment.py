#!/usr/bin/env python3
#
#     platforms.solid.experiment.py: handle SOLiD sequencing experiments
#     Copyright (C) University of Manchester 2011-2024 Peter Briggs
#
########################################################################
#
# platforms.solid.experiment.py
#
#########################################################################

"""
Provides the following classes:

* Experiment: defines single SOLiD sequencing "experiment", which is
  essentially a collection of one or more related primary data sets
  from a SOLiD run;
* ExperimentList: groups together a collection of experiments which
  are typically part of the same SOLiD run.
* LinkNames: used to construct names for links to primary data
  according to a specified naming scheme



"""

#######################################################################
# Imports
#######################################################################

import os
import logging
from .data import RunDir
from .data import is_paired_end
from ...utils import AttributeDictionary
from ...utils import mkdir
from ...utils import mklink

# Module specific logger
logger = logging.getLogger(__name__)

#######################################################################
# Classes
#######################################################################


class Experiment:
    """
    Class defining an experiment from a SOLiD run.

    An 'experiment' is a collection of related data.

    Once an Experiment instance is created, the calling
    subprogram can set the attributes as appropriate,
    for example:

    >>> expt = Experiment()
    >>> expt.name = "PJB"

    """
    def __init__(self):
        self.name = None
        self.type = None
        self.sample = None
        self.library = None

    def dirname(self, top_dir=None):
        """
        Return directory name for the experiment

        The directory name is the supplied name plus the
        experiment type joined by an underscore, unless
        no type was specified (in which case it is just
        the experiment name).

        If 'top_dir' is also supplied then this will be
        prepended to the returned directory name.

        Arguments:
          top_dir (str): path to prepend to directory
            name (optional)

        Returns:
          String: name or path for the experiment.
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
        """
        Describe the experiment as a set of command line options
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
        """
        Return a copy of the experiment

        Returns a new Experiment instance which is a copy
        of this one.

        Returns:
          Experiment: copy of the experiment.
        """
        expt_copy = Experiment()
        expt_copy.name = self.name
        expt_copy.type = self.type
        expt_copy.sample = self.sample
        expt_copy.library = self.library
        return expt_copy


class ExperimentList:
    """
    Container for a collection of Experiments

    Experiments are created and added to the
    ExperimentList by calling the addExperiment method,
    which returns a new Experiment object.

    The calling subprogram then populates the
    Experiment properties as appropriate.

    Once all Experiments are defined the analysis
    directory can be constructed by calling the
    buildAnalysisDirs method, which creates
    directories and symbolic links to primary data
    according to the definition of each experiment.

    Arguments:
      solid_run_dir (str): (optional) the path to the
        source SOLiD run directory
      classes (dict): dictionary of class names to override the
        defaults with
    """
    def __init__(self, solid_run_dir=None, classes={}):
        self.experiments = []
        self.solid_run_dir = solid_run_dir
        self.solid_runs = []
        # Default classes to use for managing data
        self._cls = AttributeDictionary(
            RunDir=RunDir,
            Experiment=Experiment,
            LinkNames=LinkNames
        )
        # Override classes
        for cls in classes:
            if cls in self._cls:
                self._cls[cls] = classes[cls]
        # Load data from run dir
        self._get_run_data()

    def _get_run_data(self):
        """
        Get data about SOLiD runs

        Internal function to construct RunDir objects based
        on the supplied SOLiD run directory.
        """
        if self.solid_run_dir is not None:
            logger.debug("Acquiring run information")
            for solid_dir in (self.solid_run_dir,
                              self.solid_run_dir+"_2"):
                logger.debug("Examining %s" % solid_dir)
                run = self._cls.RunDir(solid_dir)
                if not run:
                    logger.debug("Unable to get run data for %s" %
                                 solid_dir)
                else:
                    self.solid_runs.append(run)
            if len(self.solid_runs) == 0:
                logger.warning("No run data found")

    def add_experiment(self, name):
        """
        Create a new Experiment and add to the list

        Arguments:
          name (str): the name of the new experiment

        Returns:
          Experiment: new Experiment object with name
            already set.
        """
        new_expt = self._cls.Experiment()
        new_expt.name = name
        self.experiments.append(new_expt)
        return new_expt

    def add_duplicate_experiment(self, expt):
        """
        Add duplicate of an existing Experiment

        Adds a new Experiment object to the list
        which duplicates an existing one (which
        doesn't have to be in the same list).

        Arguments:
          expt (Experiment): an existing Experiment
            object

        Returns:
          Experiment: copy of the original Experiment
            instance.
        """
        new_expt = expt.copy()
        self.experiments.append(new_expt)
        return new_expt

    def get_last_experiment(self):
        """
        Return the last Experiment in the list
        """
        try:
            return self.experiments[-1]
        except IndexError:
            return None

    def build_analysis_dirs(self, top_dir=None, dry_run=False,
                            link_type="relative", naming_scheme="partial"):
        """
        Construct analysis directories for each experiment

        For each defined experiment, create the required
        analysis directories and populate with links to the
        primary data files.

        Arguments:
          top_dir (str): if set then create the analysis
            directories as subdirs under this directory
            (otherwise operate in CWD)
          dry_run (bool): if True then only report the
            operations that would be performed (default:
            False i.e. also perform the operations)
          link_type (str): type of link to use when linking
             to primary data; must be one of either 'relative'
             or 'absolute'.
          naming_scheme (str): naming scheme to use for links
            to primary data; must be one of 'full' (same names
            as primary data files), 'partial' (default:
            cut-down version of the full name which excludes
            sample names), or 'minimal' (just the library
            name).
        """
        # Deal with top_dir
        if top_dir:
            if os.path.exists(top_dir):
                print("Directory %s already exists" % top_dir)
            else:
                if not dry_run:
                    # Create top directory
                    print("Creating %s" % top_dir)
                    mkdir(top_dir,mode=0o775)
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
                logger.warning("Directory %s already exists" % expt_dir)
            else:
                if not dry_run:
                    # Create directory
                    mkdir(expt_dir,mode=0o775)
                else:
                    # Report what would have been done
                    print("mkdir %s" % expt_dir)
            # Locate the primary data
            for run in self.solid_runs:
                paired_end = is_paired_end(run)
                libraries = run.fetch_libraries(expt.sample,
                                                expt.library)
                for library in libraries:
                    # Get names for links to primary data - F3
                    ln_csfasta, ln_qual = \
                        self._cls.LinkNames(naming_scheme).names(library)
                    print("\t\t%s" % ln_csfasta)
                    print("\t\t%s" % ln_qual)
                    # Make links to primary data
                    try:
                        self._link_to_file(
                            library.csfasta,
                            os.path.join(expt_dir, ln_csfasta),
                            relative=use_relative_links,
                            dry_run=dry_run)
                        self._link_to_file(
                            library.qual,
                            os.path.join(expt_dir, ln_qual),
                            relative=use_relative_links,
                            dry_run=dry_run)
                    except Exception as ex:
                        logger.error("Failed to link to some or all "
                                     "F3 primary data")
                        logger.error("Exception: %s" % ex)
                    # Get names for links to F5 reads (if paired-end run)
                    if paired_end:
                        ln_csfasta, ln_qual = \
                            LinkNames(naming_scheme).names(library,F5=True)
                        print("\t\t%s" % ln_csfasta)
                        print("\t\t%s" % ln_qual)
                        # Make links to F5 read data
                        try:
                            self._link_to_file(
                                library.csfasta_f5,
                                os.path.join(expt_dir, ln_csfasta),
                                relative=use_relative_links,
                                dry_run=dry_run)
                            self._link_to_file(
                                library.qual_f5,
                                os.path.join(expt_dir, ln_qual),
                                relative=use_relative_links,
                                dry_run=dry_run)
                        except Exception as ex:
                            logger.error("Failed to link to some or all "
                                         "F5 primary data")
                            logger.error("Exception: %s" % ex)
            # Make an empty ScriptCode directory
            scriptcode_dir = os.path.join(expt_dir,"ScriptCode")
            if os.path.exists(scriptcode_dir):
                logger.warning("Directory %s already exists" %
                               scriptcode_dir)
            else:
                if not dry_run:
                    # Create directory
                    mkdir(scriptcode_dir, mode=0o775)
                else:
                    # Report what would have been done
                    print("mkdir %s" % scriptcode_dir)
    
    def _link_to_file(self, source, target, relative=True,
                      dry_run=False):
        """
        Create symbolic link to a file
        
        Internal function to make symbolic links to primary data.
        Checks that the target links don't already exist, or if
        they do that the current source file is the same as that
        specified in the method call.

        Arguments:
          source (str): the file to be linked to
          target (str): the name of the link pointing to source
          relative (bool): if True then make a relative link (if
            possible); otherwise link to the target as given
            (default)
          dry_run (bool): if True then only report the actions
            that would be performed (default is False, also perform
            the actions)
        """
        # Check if target file already exists
        if os.path.exists(target):
            logger.warning("Target file %s already exists" % target)
            # Test if the sources match
            if os.readlink(target) != source:
                logger.error("Different sources for %s" % target)
            return
        if not dry_run:
            # Make symbolic links
            mklink(source, target, relative=relative)
        else:
            # Report what would have been done
            print("ln -s %s %s" % (source, target))

    def __getitem__(self,key):
        return self.experiments[key]

    def __len__(self):
        return len(self.experiments)


class LinkNames:
    """
    Class to construct names for links to primary data

    The LinkNames class encodes a set of naming
    schemes that are used to construct names for the 
    links in the analysis directories that point to the
    primary CFASTA and QUAL data files.

    The schemes are:

    * full: link name is the same as the source file, e.g.
    solid0123_20111014_FRAG_BC_AB_CD_EF_pool_F3_CD_PQ5.csfasta

    * partial: link name consists of the instrument name,
    datestamp and library name, e.g.
    solid0123_20111014_CD_PQ5.csfasta

    * minimal: link name consists of just the library name,
    e.g. CD_PQ5.csfasta

    For paired-end data, the 'partial' and 'minimal' names
    have '_F3' and '_F5' appended as appropriate (full names
    already have this distinction).

    Example usage:

    To get the link names using the minimal scheme for the
    F3 reads ('library' is a Library object):

    >>> csfasta_lnk, qual_lnk = LinkNames('minimal').names(library)

    To get names for the F5 reads using the partial scheme:

    >>> csfasta_lnk,qual_lnk = LinkNames('partial').names(library,F5=True)

    Argments:
      scheme (str): naming scheme, one of 'full', 'partial'
        or 'minimal'
    """
    def __init__(self, scheme):
        # Default
        self._names = self._full_names
        # Assign according to requested scheme
        if scheme == "minimal":
            self._names = self._minimal_names
        elif scheme == "partial":
            self._names = self._partial_names
        elif scheme == "full":
            self._names = self._full_names

    def names(self, library, F5=False):
        """
        Get names for links to primary data in library

        Returns a tuple of link names:

        (csfasta_link_name, qual_link_name)

        derived from the data in the library plus the
        naming scheme specified when the LinkNames
        object was created.
        
        Arguments:
          library (Library): library in a SOLiD run
          F5 (bool): if True then indicates that names
            should be returned for linking to the F5
            reads (default is False, link to F3 reads)
        """
        return self._names(library, F5)

    def _minimal_names(self,library, F5):
        """
        Internal: link names based on 'minimal' naming scheme
        """
        # Alternative naming schemes for primary data for links
        run = library.parent_sample.parent_run
        if not is_paired_end(run):
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

    def _partial_names(self,library,F5):
        """
        Internal: link names based on 'partial' naming scheme
        """
        run = library.parent_sample.parent_run
        name = '_'.join([run.run_info.instrument,
                         run.run_info.datestamp,
                         library.name])
        if not is_paired_end(run):
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

    def _full_names(self,library,F5):
        """
        Internal: link names based on 'full' naming scheme
        """
        run = library.parent_sample.parent_run
        if not is_paired_end(run):
            return (os.path.basename(library.csfasta),
                    os.path.basename(library.qual))
        else:
            if not F5:
                return (os.path.basename(library.csfasta),
                        os.path.basename(library.qual))
            else:
                return (os.path.basename(library.csfasta_f5),
                        os.path.basename(library.qual_f5))
