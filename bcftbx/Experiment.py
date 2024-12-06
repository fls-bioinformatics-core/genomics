#!/usr/bin/env python
#
#     Experiment.py: classes for defining SOLiD sequencing experiments
#     Copyright (C) University of Manchester 2011-2024 Peter Briggs
#
########################################################################
#
# Experiment.py
#
#########################################################################

"""
Legacy module for handling SOLiD experiments (groups of primary data
sets from a SOLiD sequencing run).

The functionality of the module has been moved to the
'platforms.solid.experiment' module, which supersedes this one. This
module is now deprecated and will be removed in a future release.

The legacy classes have been reimplemented as wrappers to the classes
in the newer module, to preserve backwards compatibility.

"""

#######################################################################
# Import modules that this module depends on
#######################################################################

from .SolidData import SolidRun
from .platforms.solid import experiment as expt

#######################################################################
# Class definitions
#######################################################################

class Experiment(expt.Experiment):
    """Class defining an experiment from a SOLiD run.

    An 'experiment' is a collection of related data.
    """
    def __init__(self):
        expt.Experiment.__init__(self)


class ExperimentList(expt.ExperimentList):
    """
    Container for a collection of Experiments
    """
    def __init__(self,solid_run_dir=None):
        expt.ExperimentList.__init__(self,
                                     solid_run_dir=solid_run_dir,
                                     classes=dict(RunDir=SolidRun,
                                                  Experiment=Experiment,
                                                  LinkNames=LinkNames))

    def addExperiment(self,name):
        """
        Create a new Experiment and add to the list
        """
        return expt.ExperimentList.add_experiment(self, name)

    def addDuplicateExperiment(self,expt):
        """
        Duplicate an existing Experiment and add to the list
        """
        return expt.ExperimentList.add_duplicate_experiment(self, expt)

    def getLastExperiment(self):
        """
        Return the last Experiment added to the list
        """
        return expt.ExperimentList.get_last_experiment(self)

    def buildAnalysisDirs(self,top_dir=None,dry_run=False,link_type="relative",
                          naming_scheme="partial"):
        """
        Construct and populate analysis directories for the experiments
        """
        return expt.ExperimentList.build_analysis_dirs(
            self,
            top_dir=top_dir,
            dry_run=dry_run,
            link_type=link_type,
            naming_scheme=naming_scheme)


class LinkNames:
    """
    Class to construct names for links to primary data files
    """
    def __init__(self,scheme):
        expt.LinkNames.__init__(self, scheme)

#######################################################################
# Module functions
#######################################################################

# None defined
