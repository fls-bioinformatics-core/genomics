#######################################################################
# Tests for solid.experiment.py module
#######################################################################

import unittest
#import io
import tempfile
import shutil
from bcftbx.platforms.solid.experiment import *
from bcftbx.platforms.solid.data import RunDir
from .test_data import TestUtils

class TestExperiment(unittest.TestCase):
    """
    Tests for the Experiment class.
    """
    def test_experiment(self):
        """
        solid.experiment.Experiment: basic properties
        """
        expt = Experiment()
        self.assertEqual(expt.name, None)
        self.assertEqual(expt.type, None)
        self.assertEqual(expt.sample, None)
        self.assertEqual(expt.library, None)
        ##sample = self.solid_run.samples[0]
        ##print(sample)
        ##project = sample.projects[0]
        ##print(project)
        ##expt.name = project.name
        ##expt.type = "RNA-seq"
        ##expt.sample = project.get_sample().name
        ##expt.library = project.get_library_name_pattern()
        expt.name = "CD"
        expt.type = "RNA-seq"
        expt.sample = "AB_CD_EF_pool"
        expt.library = "CD_*"
        self.assertEqual(expt.name, "CD")
        self.assertEqual(expt.type, "RNA-seq")
        self.assertEqual(expt.sample, "AB_CD_EF_pool")
        self.assertEqual(expt.library, "CD_*")

    def test_experiment_dirname(self):
        """
        solid.experiment.Experiment: directory name
        """
        expt = Experiment()
        # Name but no type
        expt.name = "CD"
        expt.type = None
        expt.sample = "AB_CD_EF_pool"
        expt.library = "CD_*"
        self.assertEqual(expt.dirname(), "CD")
        # Add type
        expt.type = "RNA-seq"
        self.assertEqual(expt.dirname(), "CD_RNA-seq")

    def test_experiment_describe(self):
        """
        solid.experiment.Experiment: describe experiment
        """
        expt = Experiment()
        # Name only
        expt.name = "CD"
        self.assertEqual(expt.describe(),
                         "--name=CD --source=*/*")
        # Add type
        expt.type = "RNA-seq"
        self.assertEqual(expt.describe(),
                         "--name=CD --type=RNA-seq --source=*/*")
        # Add sample
        expt.sample = "AB_CD_EF_pool"
        self.assertEqual(expt.describe(),
                         "--name=CD --type=RNA-seq "
                         "--source=AB_CD_EF_pool/*")
        # Add library
        expt.library = "CD_*"
        self.assertEqual(expt.describe(),
                         "--name=CD --type=RNA-seq "
                         "--source=AB_CD_EF_pool/CD_*")

    def test_experiment_copy(self):
        """
        solid.experiment.Experiment: copy experiment
        """
        expt = Experiment()
        expt.name = "CD"
        expt.type = "RNA-seq"
        expt.sample = "AB_CD_EF_pool"
        expt.library = "CD_*"
        expt2 = expt.copy()
        self.assertEqual(expt2.name, "CD")
        self.assertEqual(expt2.type, "RNA-seq")
        self.assertEqual(expt2.sample, "AB_CD_EF_pool")
        self.assertEqual(expt2.library, "CD_*")


class TestExperimentList(unittest.TestCase):
    """
    Tests for the ExperimentList class.
    """
    def setUp(self):
        # Set up a mock SOLiD directory structure
        self.solid_test_dir = \
            TestUtils().make_solid_dir('solid0123_20130426_FRAG_BC')
        # Create a RunDir object for tests
        self.solid_run = RunDir(self.solid_test_dir)
        # Top dir
        self.top_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.solid_test_dir)
        shutil.rmtree(self.top_dir)

    def test_experimentlist(self):
        """
        solid.experiment.ExperimentList: load from run dir
        """
        expt_list = ExperimentList(solid_run_dir=self.solid_test_dir)
        self.assertEqual(expt_list.solid_run_dir, self.solid_test_dir)
        self.assertEqual(len(expt_list.solid_runs), 1)
        self.assertEqual(expt_list.experiments, [])

    def test_experimentlist_no_run_dir(self):
        """
        solid.experiment.ExperimentList: no run dir
        """
        expt_list = ExperimentList()
        self.assertEqual(expt_list.solid_run_dir, None)
        self.assertEqual(expt_list.solid_runs, [])
        self.assertEqual(expt_list.experiments, [])

    def test_experimentlist_add_experiment(self):
        """
        solid.experiment.ExperimentList: add experiment
        """
        expt_list = ExperimentList()
        self.assertEqual(expt_list.experiments, [])
        # Add first experiment
        expt1 = expt_list.add_experiment("CD")
        self.assertEqual(expt_list.experiments, [expt1])
        self.assertEqual(expt1.name, "CD")
        # Add second experiment
        expt2 = expt_list.add_experiment("AB")
        self.assertEqual(expt_list.experiments, [expt1, expt2])
        self.assertEqual(expt1.name, "CD")
        self.assertEqual(expt2.name, "AB")

    def test_experimentlist_add_duplicate_experiment(self):
        """
        solid.experiment.ExperimentList: add duplicate experiment
        """
        expt_list = ExperimentList()
        self.assertEqual(expt_list.experiments, [])
        # Add initial experiments
        expt1 = expt_list.add_experiment("CD")
        expt2 = expt_list.add_experiment("AB")
        self.assertEqual(expt_list.experiments, [expt1, expt2])
        # Add duplicate of experiment 1
        expt3 = expt_list.add_duplicate_experiment(expt1)
        self.assertEqual(expt3.name, "CD")
        self.assertEqual(expt_list.experiments, [expt1, expt2, expt3])

    def test_experimentlist_get_last_experiment(self):
        """
        solid.experiment.ExperimentList: get last experiment
        """
        expt_list = ExperimentList()
        self.assertEqual(expt_list.experiments, [])
        # Add first experiment
        expt1 = expt_list.add_experiment("CD")
        self.assertEqual(expt_list.get_last_experiment(), expt1)
        # Add second experiment
        expt2 = expt_list.add_experiment("AB")
        self.assertEqual(expt_list.get_last_experiment(), expt2)

    def test_experimentlist_build_analysis_dirs(self):
        """
        solid.experiment.ExperimentList: build analysis directories
        """
        expt_list = ExperimentList(solid_run_dir=self.solid_test_dir)
        self.assertEqual(expt_list.experiments, [])
        # Add first experiment
        expt1= expt_list.add_experiment("CD")
        expt1.type = "RNA-seq"
        expt1.sample = "AB_CD_EF_pool"
        expt1.library = "CD_*"
        # Add second experiment
        expt2 = expt_list.add_experiment("AB")
        expt2.type = "ChIP-seq"
        expt2.sample = "AB_CD_EF_pool"
        expt2.library = "AB_*"
        # Build analysis directories
        expt_list.build_analysis_dirs(top_dir=self.top_dir)
        print(os.listdir(self.top_dir))
        # Check expected files and directories
        expected = ["CD_RNA-seq/",
                    "CD_RNA-seq/ScriptCode/",
                    "CD_RNA-seq/solid0123_20130426_CD_PQ5.csfasta",
                    "CD_RNA-seq/solid0123_20130426_CD_PQ5_QV.qual",
                    "CD_RNA-seq/solid0123_20130426_CD_ST4.csfasta",
                    "CD_RNA-seq/solid0123_20130426_CD_ST4_QV.qual",
                    "CD_RNA-seq/solid0123_20130426_CD_UV5.csfasta",
                    "CD_RNA-seq/solid0123_20130426_CD_UV5_QV.qual",
                    "AB_ChIP-seq/ScriptCode/",
                    "AB_ChIP-seq/solid0123_20130426_AB_A1M1.csfasta",
                    "AB_ChIP-seq/solid0123_20130426_AB_A1M1_QV.qual",
                    "AB_ChIP-seq/solid0123_20130426_AB_A1M2.csfasta",
                    "AB_ChIP-seq/solid0123_20130426_AB_A1M2_QV.qual",
                    "AB_ChIP-seq/solid0123_20130426_AB_A1M1_input.csfasta",
                    "AB_ChIP-seq/solid0123_20130426_AB_A1M1_input_QV.qual",
                    "AB_ChIP-seq/solid0123_20130426_AB_A1M2_input.csfasta",
                    "AB_ChIP-seq/solid0123_20130426_AB_A1M2_input_QV.qual",]
        for f in expected:
            self.assertTrue(os.path.exists(os.path.join(self.top_dir,f)),
                            f"Missing '{f}'")


class TestLinkNames(unittest.TestCase):
    """
    Tests for the LinkNames class.
    """
    def setUp(self):
        # Set up a mock SOLiD directory structure
        self.solid_test_dir = \
            TestUtils().make_solid_dir('solid0123_20130426_FRAG_BC')
        # Create a RunDir object for tests
        self.solid_run = RunDir(self.solid_test_dir)
        # Get a library from the run
        self.library = self.solid_run.samples[0].libraries[0]

    def tearDown(self):
        shutil.rmtree(self.solid_test_dir)

    def test_linknames_full(self):
        """
        solid.experiment.LinkNames: 'full' name scheme
        """
        self.assertEqual(
            LinkNames("full").names(self.library),
            ("solid0123_20130426_FRAG_BC_AB_CD_EF_pool_F3_AB_A1M1.csfasta",
             "solid0123_20130426_FRAG_BC_AB_CD_EF_pool_F3_QV_AB_A1M1.qual"))

    def test_linknames_partial(self):
        """
        solid.experiment.LinkNames: 'partial' name scheme
        """
        self.assertEqual(
            LinkNames("partial").names(self.library),
            ("solid0123_20130426_AB_A1M1.csfasta",
             "solid0123_20130426_AB_A1M1_QV.qual"))

    def test_linknames_minimal(self):
        """
        solid.experiment.LinkNames: 'minimal' name scheme
        """
        self.assertEqual(
            LinkNames("minimal").names(self.library),
            ("AB_A1M1.csfasta",
             "AB_A1M1.qual"))
