#######################################################################
# Tests for solid.data.py module
#######################################################################

from bcftbx.platforms.solid.data import *
import unittest
import io
import tempfile
import shutil


class TestUtils:
    """Utilities to help with setting up/running tests etc

    Provides methods for creating mock SOLiD directory structure populated
    with example files.

    make_solid_dir: constructs a mock SOLiD run directory, including the
    run definition and barcode statistics files

    make_solid_dir_paired_end: constructs a mock SOLiD run directory for a
    paired-end run

    make_run_definition_file: constructs a mock run definition file

    make_run_definition_file_paired_end: constructs mock run definition file for
    a paired-end run

    make_barcode_statistics_file: constructs a mock barcode statistics file
    """

    def make_run_definition_file(self,filename=None):
        """Create example run definition file.

        If a name is explicitly specified then the file will be created
        with that name; otherwise a temporary file name will be generated.

        Returns the name for the run definition file.
        """
        # Default run name
        run_name = "solid0123_20130426_FRAG_BC_2"
        run_definition_text = \
u"""version	userId	runType	isMultiplexing	runName	runDesc	mask	protocol
v0.0	user	FRAGMENT	TRUE	%s		1_spot_mask_sf	SOLiD4 Multiplex
primerSet	baseLength
BC	5
F3	50
sampleName	sampleDesc	spotAssignments	primarySetting	library	application	secondaryAnalysis	multiplexingSeries	barcodes
AB_CD_EF_pool		1	default primary	CD_UV5	SingleTag	mm9	BC Kit Module 1-16	"7"
AB_CD_EF_pool		1	default primary	CD_PQ5	SingleTag	mm9	BC Kit Module 1-16	"6"
AB_CD_EF_pool		1	default primary	CD_ST4	SingleTag	mm9	BC Kit Module 1-16	"5"
AB_CD_EF_pool		1	default primary	EF11	SingleTag	dm5	BC Kit Module 1-16	"8"
AB_CD_EF_pool		1	default primary	EF12	SingleTag	dm5	BC Kit Module 1-16	"9"
AB_CD_EF_pool		1	default primary	EF13	SingleTag	dm5	BC Kit Module 1-16	"10"
AB_CD_EF_pool		1	default primary	EF14	SingleTag	dm5	BC Kit Module 1-16	"11"
AB_CD_EF_pool		1	default primary	EF15	SingleTag	dm5	BC Kit Module 1-16	"12"
AB_CD_EF_pool		1	default primary	AB_A1M1	SingleTag	hg18	BC Kit Module 1-16	"3"
AB_CD_EF_pool		1	default primary	AB_A1M2	SingleTag	hg18	BC Kit Module 1-16	"4"
AB_CD_EF_pool		1	default primary	AB_A1M1_input	SingleTag	hg18	BC Kit Module 1-16	"1"
AB_CD_EF_pool		1	default primary	AB_A1M2_input	SingleTag	hg18	BC Kit Module 1-16	"2"
"""
        if filename is None:
            # mkstemp returns a tuple
            tmpfile = tempfile.mkstemp()
            filename = tmpfile[1]
        elif filename.endswith("_run_definition.txt"):
            # Reset the run name by stripping '_run_definition.txt'
            run_name = os.path.basename(filename[:(len(filename)-len("_run_definition.txt"))])
        fp = io.open(filename,'wt')
        fp.write(run_definition_text % run_name)
        fp.close()
        return filename

    def make_barcode_statistics_file(self,filename=None):
        """Create example barcode statistics file.

        If a name is explicitly specified then the file will be created
        with that name; otherwise a temporary file name will be generated.

        Returns the name for the barcode statistics file.
        """
        barcode_statistics_text = \
u"""#? missing-barcode-reads=0
#? missing-F3-reads=0
##Library	Barcode	0 Mismatches	1 Mismatch	Total
AB_A1M1	3	32034098	3010512	35044610
AB_A1M1	Subtotals	32034098	3010512	35044610
EF14	11	33802784	2697225	36500009
EF14	Subtotals	33802784	2697225	36500009
CD_UV5	7	34132646	2304212	36436858
CD_UV5	Subtotals	34132646	2304212	36436858
EF12	9	35492369	2789254	38281623
EF12	Subtotals	35492369	2789254	38281623
EF13	10	30460845	2818591	33279436
EF13	Subtotals	30460845	2818591	33279436
EF15	12	36824658	2939962	39764620
EF15	Subtotals	36824658	2939962	39764620
AB_A1M2	4	35897351	2904080	38801431
AB_A1M2	Subtotals	35897351	2904080	38801431
EF11	8	24853173	2186475	27039648
EF11	Subtotals	24853173	2186475	27039648
CD_ST4	5	44673850	4675548	49349398
CD_ST4	Subtotals	44673850	4675548	49349398
CD_PQ5	6	40817315	4882499	45699814
CD_PQ5	Subtotals	40817315	4882499	45699814
AB_A1M1_input	2	33385249	2446268	35831517
AB_A1M1_input	Subtotals	33385249	2446268	35831517
AB_A1M2_input	1	27425404	2814422	30239826
AB_A1M2_input	Subtotals	27425404	2814422	30239826
unassigned	03020	98926	1021138	1120064
unassigned	12213	10872	611071	621943
unassigned	20131	9880	696765	706645
unassigned	31302	8180	654309	662489
unassigned	unresolved	NA	NA	8162042
unassigned	Subtotals	127858	2983283	11273183
All Beads	Totals	409927600	39452331	457541973
"""
        if filename is None:
            # mkstemp returns a tuple
            tmpfile = tempfile.mkstemp()
            filename = tmpfile[1]
        fp = io.open(filename,'wt')
        fp.write(barcode_statistics_text)
        fp.close()
        return filename

    def make_solid_dir(self,solid_run_name):
        """Create a mock SOLiD run directory structure.

        Creates a temporary directory and builds a mock SOLiD run directory
        called 'solid_run_name' inside that.
        
        Returns the full path to the mock SOLiD run directory.
        """
        
        # Put everything in a temporary directory
        top_level = tempfile.mkdtemp()
        # Top-level
        dirname = os.path.join(top_level,solid_run_name)
        os.mkdir(dirname)
        self.make_run_definition_file(dirname+'/'+solid_run_name+'_run_definition.txt')
        #
        # Subdirectories:
        #
        ### solidXXX/plots
        os.makedirs(dirname+'/plots')
        #
        ### solidXXX/AB_CD_EF_pool
        os.makedirs(dirname+'/AB_CD_EF_pool/results.F1B1')
        os.symlink('results.F1B1',dirname+'/AB_CD_EF_pool/results')
        #
        ### solidXXX/AB_CD_EF_pool/results.F1B1/
        os.makedirs(dirname+'/AB_CD_EF_pool/results.F1B1/libraries')
        os.makedirs(dirname+
                    '/AB_CD_EF_pool/results.F1B1/primary.20131234567890')
        os.makedirs(dirname+
                    '/AB_CD_EF_pool/results.F1B1/primary.20132345678901')
        #
        ## solidXXX/AB_CD_EF_pool/results.F1B1/libraries/
        self.make_barcode_statistics_file(
            dirname+
            '/AB_CD_EF_pool/results.F1B1/libraries/'+
            'BarcodeStatistics.20130123456789012.txt')
        for d in ('CD_UV5','CD_PQ5','CD_ST4',
                  'EF11','EF12','EF13','EF14','EF15',
                  'AB_A1M1','AB_A1M2','AB_A1M1_input','AB_A1M2_input'):
            os.makedirs(dirname+'/AB_CD_EF_pool/results.F1B1/libraries/'+d)
            os.makedirs(dirname+'/AB_CD_EF_pool/results.F1B1/libraries/'+d+
                        '/intermediate')
            os.makedirs(dirname+'/AB_CD_EF_pool/results.F1B1/libraries/'+d+
                        '/primary.201301234567890')
            os.makedirs(dirname+'/AB_CD_EF_pool/results.F1B1/libraries/'+d+
                        '/primary.201301234567890/reads')
            os.makedirs(dirname+'/AB_CD_EF_pool/results.F1B1/libraries/'+d+
                        '/primary.201301234567890/reports')
            os.makedirs(dirname+'/AB_CD_EF_pool/results.F1B1/libraries/'+d+
                        '/primary.201312345678901')
            os.makedirs(dirname+'/AB_CD_EF_pool/results.F1B1/libraries/'+d+
                        '/primary.201312345678901/reads')
            os.makedirs(dirname+'/AB_CD_EF_pool/results.F1B1/libraries/'+d+
                        '/primary.201312345678901/reject')
            os.makedirs(dirname+'/AB_CD_EF_pool/results.F1B1/libraries/'+d+
                        '/primary.201312345678901/reports')
            os.makedirs(dirname+'/AB_CD_EF_pool/results.F1B1/libraries/'+d+
                        '/secondary.F3.20130012345678')
            os.makedirs(dirname+'/AB_CD_EF_pool/results.F1B1/libraries/'+d+
                        '/temp')
            #
            # solidXXX/AB_CD_EF_pool/results.F1B1/libraries/X/primary.x/reads/
            self.make_csfasta(dirname+'/AB_CD_EF_pool/results.F1B1/libraries/'+d+
                              '/primary.201312345678901/reads/'+
                              solid_run_name+'_AB_CD_EF_pool_F3_'+d+'.csfasta')
            self.make_qual(dirname+'/AB_CD_EF_pool/results.F1B1/libraries/'+d+
                           '/primary.201312345678901/reads/'+
                           solid_run_name+'_AB_CD_EF_pool_F3_QV_'+d+'.qual')
            self.touch(dirname+'/AB_CD_EF_pool/results.F1B1/libraries/'+d+
                        '/primary.201312345678901/reads/'+
                       solid_run_name+'_AB_CD_EF_pool_F3.stats')
        # Return the temporary directory with the mock SOLiD run 
        return dirname

    def make_run_definition_file_paired_end(self,filename=None):
        """Create example run definition file for paired-end run.

        If a name is explicitly specified then the file will be created
        with that name; otherwise a temporary file name will be generated.

        Returns the name for the run definition file.
        """
        # Default run name
        run_name = "solid123_20130426_PE_BC"
        run_definition_text = \
u"""version	userId	runType	isMultiplexing	runName	runDesc	mask	protocol
v1.3	lab_user	PAIRED-END	TRUE	%s		1_spot_mask_sf	SOLiD4 Multiplex
primerSet	baseLength
BC	10
F5-BC	35
F3	50
sampleName	sampleDesc	spotAssignments	primarySetting	library	application	secondaryAnalysis	multiplexingSeries	barcodes
AB_CD_pool		1	default primary	AB_SEQ26	SingleTag	sacCer2	BC Kit Module 1-96	"17"
AB_CD_pool		1	default primary	AB_SEQ27	SingleTag	sacCer2	BC Kit Module 1-96	"18"
AB_CD_pool		1	default primary	AB_SEQ28	SingleTag	sacCer2	BC Kit Module 1-96	"19"
AB_CD_pool		1	default primary	AB_SEQ29	SingleTag	sacCer2	BC Kit Module 1-96	"20"
AB_CD_pool		1	default primary	AB_SEQ30	SingleTag	sacCer2	BC Kit Module 1-96	"21"
AB_CD_pool		1	default primary	AB_SEQ31	SingleTag	sacCer2	BC Kit Module 1-96	"22"
AB_CD_pool		1	default primary	AB_SEQ32	SingleTag	sacCer2	BC Kit Module 1-96	"23"
AB_CD_pool		1	default primary	AB_SEQ33	SingleTag	sacCer2	BC Kit Module 1-96	"24"
AB_CD_pool		1	default primary	CD_SP6033	SingleTag	none	BC Kit Module 1-96	"1"
AB_CD_pool		1	default primary	CD_SP6257	SingleTag	none	BC Kit Module 1-96	"3"
AB_CD_pool		1	default primary	CD_SP6261	SingleTag	none	BC Kit Module 1-96	"2"
"""   
        if filename is None:
            # mkstemp returns a tuple
            tmpfile = tempfile.mkstemp()
            filename = tmpfile[1]
        elif filename.endswith("_run_definition.txt"):
            # Reset the run name by stripping '_run_definition.txt'
            run_name = os.path.basename(filename[:(len(filename)-len("_run_definition.txt"))])
        fp = io.open(filename,'wt')
        fp.write(run_definition_text % run_name)
        fp.close()
        return filename

    def make_barcode_statistics_file_paired_end(self,filename=None):
        """Create example barcode statistics file for paired-end run.

        If a name is explicitly specified then the file will be created
        with that name; otherwise a temporary file name will be generated.

        Returns the name for the barcode statistics file.
        """
        barcode_statistics_text = \
u"""#? missing-barcode-reads=0
#? missing-F3-reads=0
##Library	Barcode	0 Mismatches	1 Mismatch	Total
AB_SEQ26	19	32034098	3010512	35044610
AB_SEQ26	Subtotals	32034098	3010512	35044610
AB_SEQ27	18	33802784	2697225	36500009
AB_SEQ27	Subtotals	33802784	2697225	36500009
AB_SEQ28	21	34132646	2304212	36436858
AB_SEQ28	Subtotals	34132646	2304212	36436858
AB_SEQ29	20	35492369	2789254	38281623
AB_SEQ29	Subtotals	35492369	2789254	38281623
AB_SEQ30	22	30460845	2818591	33279436
AB_SEQ30	Subtotals	30460845	2818591	33279436
AB_SEQ31	3	36824658	2939962	39764620
AB_SEQ31	Subtotals	36824658	2939962	39764620
AB_SEQ32	1	35897351	2904080	38801431
AB_SEQ32	Subtotals	35897351	2904080	38801431
AB_SEQ33	2	24853173	2186475	27039648
AB_SEQ33	Subtotals	24853173	2186475	27039648
CD_SP6033	23	44673850	4675548	49349398
CD_SP6033	Subtotals	44673850	4675548	49349398
CD_SP6257	17	40817315	4882499	45699814
CD_SP6257	Subtotals	40817315	4882499	45699814
CD_SP6261	24	33385249	2446268	35831517
CD_SP6261	Subtotals	33385249	2446268	35831517
unassigned	03020	98926	1021138	1120064
unassigned	12213	10872	611071	621943
unassigned	20131	9880	696765	706645
unassigned	31302	8180	654309	662489
unassigned	unresolved	NA	NA	8162042
unassigned	Subtotals	127858	2983283	11273183
All Beads	Totals	409927600	39452331	457541973
"""
        if filename is None:
            # mkstemp returns a tuple
            tmpfile = tempfile.mkstemp()
            filename = tmpfile[1]
        fp = io.open(filename,'wt')
        fp.write(barcode_statistics_text)
        fp.close()
        return filename

    def make_solid_dir_paired_end(self,solid_run_name):
        """Create a mock SOLiD run directory structure for paired-end run.

        Creates a temporary directory and builds a mock SOLiD run directory
        called 'solid_run_name' inside that.
        
        Returns the full path to the mock SOLiD run directory.
        """
        
        # Put everything in a temporary directory
        top_level = tempfile.mkdtemp()
        # Top-level
        dirname = os.path.join(top_level,solid_run_name)
        os.mkdir(dirname)
        self.make_run_definition_file_paired_end(
            dirname+'/'+solid_run_name+'_run_definition.txt')
        #
        # Subdirectories:
        #
        ### solidXXX/plots
        os.makedirs(dirname+'/plots')
        #
        ### solidXXX/AB_CD_pool
        os.makedirs(dirname+'/AB_CD_pool/results.F1B1')
        os.symlink('results.F1B1',dirname+'/AB_CD_pool/results')
        #
        ### solidXXX/AB_CD_pool/results.F1B1/
        os.makedirs(dirname+'/AB_CD_pool/results.F1B1/libraries')
        os.makedirs(dirname+
                    '/AB_CD_pool/results.F1B1/primary.20131234567890')
        os.makedirs(dirname+
                    '/AB_CD_pool/results.F1B1/primary.20132345678901')
        #
        ## solidXXX/AB_CD_pool/results.F1B1/libraries/
        self.make_barcode_statistics_file_paired_end(
            dirname+
            '/AB_CD_pool/results.F1B1/libraries/'+
            'BarcodeStatistics.20130123456789012.txt')
        for d in ('AB_SEQ26','AB_SEQ27','AB_SEQ28','AB_SEQ29',
                  'AB_SEQ30','AB_SEQ31','AB_SEQ32','AB_SEQ33',
                  'CD_SP6033','CD_SP6257','CD_SP6261'):
            os.makedirs(dirname+'/AB_CD_pool/results.F1B1/libraries/'+d)
            os.makedirs(dirname+'/AB_CD_pool/results.F1B1/libraries/'+d+
                        '/intermediate')
            # Primary with no rejects (shouldn't be used)
            os.makedirs(dirname+'/AB_CD_pool/results.F1B1/libraries/'+d+
                        '/primary.201301234567890')
            os.makedirs(dirname+'/AB_CD_pool/results.F1B1/libraries/'+d+
                        '/primary.201301234567890/reads')
            os.makedirs(dirname+'/AB_CD_pool/results.F1B1/libraries/'+d+
                        '/primary.201301234567890/reports')
            # Primary with reads, rejects and reports for F5 reads
            os.makedirs(dirname+'/AB_CD_pool/results.F1B1/libraries/'+d+
                        '/primary.201312345678901')
            os.makedirs(dirname+'/AB_CD_pool/results.F1B1/libraries/'+d+
                        '/primary.201312345678901/reads')
            os.makedirs(dirname+'/AB_CD_pool/results.F1B1/libraries/'+d+
                        '/primary.201312345678901/reject')
            os.makedirs(dirname+'/AB_CD_pool/results.F1B1/libraries/'+d+
                        '/primary.201312345678901/reports')
            # Primary with reads, rejects and reports for forward reads
            os.makedirs(dirname+'/AB_CD_pool/results.F1B1/libraries/'+d+
                        '/primary.201322345678901')
            os.makedirs(dirname+'/AB_CD_pool/results.F1B1/libraries/'+d+
                        '/primary.201322345678901/reads')
            os.makedirs(dirname+'/AB_CD_pool/results.F1B1/libraries/'+d+
                        '/primary.201322345678901/reject')
            os.makedirs(dirname+'/AB_CD_pool/results.F1B1/libraries/'+d+
                        '/primary.201322345678901/reports')
            # Secondaries (shouldn't be used)
            os.makedirs(dirname+'/AB_CD_pool/results.F1B1/libraries/'+d+
                        '/secondary.F5-BC.20130012345678')
            os.makedirs(dirname+'/AB_CD_pool/results.F1B1/libraries/'+d+
                        '/secondary.F5-BC.20130123456789')
            os.makedirs(dirname+'/AB_CD_pool/results.F1B1/libraries/'+d+
                        '/temp')
            #
            # Populate F5 read dirs
            # solidXXX/AB_CD_pool/results.F1B1/libraries/X/primary.x/reads/
            self.make_csfasta(dirname+'/AB_CD_pool/results.F1B1/libraries/'+d+
                              '/primary.201312345678901/reads/'+
                              solid_run_name+'_AB_CD_pool_F5-BC_'+d+'.csfasta')
            self.make_qual(dirname+'/AB_CD_pool/results.F1B1/libraries/'+d+
                           '/primary.201312345678901/reads/'+
                           solid_run_name+'_AB_CD_pool_F5-BC_QV_'+d+'.qual')
            self.touch(dirname+'/AB_CD_pool/results.F1B1/libraries/'+d+
                        '/primary.201312345678901/reads/'+
                       solid_run_name+'_AB_CD_pool_F5-BC.stats')
            #
            # Populate forward read dirs
            # solidXXX/AB_CD_pool/results.F1B1/libraries/X/primary.x/reads/
            self.make_csfasta(dirname+'/AB_CD_pool/results.F1B1/libraries/'+d+
                              '/primary.201322345678901/reads/'+
                              solid_run_name+'_AB_CD_pool_F3_'+d+'.csfasta')
            self.make_qual(dirname+'/AB_CD_pool/results.F1B1/libraries/'+d+
                           '/primary.201322345678901/reads/'+
                           solid_run_name+'_AB_CD_pool_F3_QV_'+d+'.qual')
            self.touch(dirname+'/AB_CD_pool/results.F1B1/libraries/'+d+
                        '/primary.201322345678901/reads/'+
                       solid_run_name+'_AB_CD_pool_F3.stats')
        # Return the temporary directory with the mock SOLiD run 
        return dirname

    def touch(self,filename):
        """Make a new (empty) file
        """
        if not os.path.exists(filename):
            io.open(filename, 'wt').close()

    def make_csfasta(self,filename):
        """Make a mock csfasta file
        """
        fp = io.open(filename,'wt')
        fp.write(u">1_14_622_F3\nT221.0033033232320030021103233332300123110201010031\n>1_14_1098_F3\nT033.3010033212202122212231302012120001123133212220\n")
        fp.close()

    def make_qual(self,filename):
        """Make a mock qual file
        """
        fp = io.open(filename,'wt')
        fp.write(u">1_14_622_F3\n33 33 32 -1 29 32 32 11 33 29 26 26 28 32 4 18 24 4 33 23 28 28 28 28 29 15 30 12 30 4 24 32 17 27 8 18 30 7 19 9 18 21 4 32 4 19 5 10 24 4 \n>1_14_1098_F3\n33 33 33 -1 33 33 33 30 33 31 28 31 30 31 29 32 33 31 33 33 27 32 24 33 31 32 31 30 32 24 32 24 31 33 31 33 24 33 10 22 30 25 4 17 22 27 22 28 31 19 \n")
        fp.close()


class TestRunInfo(unittest.TestCase):
    """
    Unit tests for RunInfo class.
    """
    def test_flow_cell_one(self):
        """
        solid.data.RunInfo: flow cell one
        """
        instrument = 'solid0123'
        datestamp  = '20130426'
        fragment   = 'FRAG'
        barcode    = 'BC'
        run_name   = instrument+'_'+datestamp+'_'+fragment+'_'+barcode
        info = RunInfo(run_name)
        self.assertEqual(run_name,info.name)
        self.assertEqual(run_name,info.id)
        self.assertEqual(instrument,info.instrument)
        self.assertEqual(datestamp,info.datestamp)
        self.assertEqual(1,info.flow_cell)
        self.assertFalse(info.is_paired_end)
        self.assertTrue(info.is_fragment_library)
        self.assertTrue(info.is_barcoded_sample)
        self.assertEqual('26/04/13',info.date)
        self.assertEqual(str(info),run_name)

    def test_flow_cell_two(self):
        """
        solid.data.RunInfo: flow cell two
        """
        instrument = 'solid0123'
        datestamp  = '20130426'
        fragment   = 'FRAG'
        barcode    =  'BC'
        run_id     =  instrument+'_'+datestamp+'_'+fragment+'_'+barcode
        run_name   =  run_id+'_2'
        info = RunInfo(run_name)
        self.assertEqual(run_name,info.name)
        self.assertEqual(run_id,info.id)
        self.assertEqual(instrument,info.instrument)
        self.assertEqual(datestamp,info.datestamp)
        self.assertEqual(2,info.flow_cell)
        self.assertFalse(info.is_paired_end)
        self.assertTrue(info.is_fragment_library)
        self.assertTrue(info.is_barcoded_sample)
        self.assertEqual('26/04/13',info.date)
        self.assertEqual(str(info),run_name)

    def test_paired_end(self):
        """
        solid.data.RunInfo: paired end
        """
        instrument = 'solid0123'
        datestamp  = '20130426'
        paired_end = 'PE'
        barcode    = 'BC'
        run_name   = instrument+'_'+datestamp+'_'+paired_end+'_'+barcode
        info = RunInfo(run_name)
        self.assertEqual(run_name,info.name)
        self.assertEqual(run_name,info.id)
        self.assertEqual(instrument,info.instrument)
        self.assertEqual(datestamp,info.datestamp)
        self.assertEqual(1,info.flow_cell)
        self.assertTrue(info.is_paired_end)
        self.assertFalse(info.is_fragment_library)
        self.assertTrue(info.is_barcoded_sample)
        self.assertEqual('26/04/13',info.date)
        self.assertEqual(str(info),run_name)

    def test_bad_run_names(self):
        """
        solid.data.RunInfo: handle 'bad' names
        """
        info = RunInfo('bad_name')
        self.assertEqual('bad_name',info.name)
        info = RunInfo('badname')
        self.assertEqual('badname',info.name)


class TestLibrary(unittest.TestCase):
    """
    Unit tests for Library class.
    """
    def test_solid_library(self):
        """
        solid.data.Library: basic properties
        """
        sample_name = 'PJB_pool'
        library_name = 'PJB_NY17'
        sample = Sample(sample_name)
        library = Library(library_name,sample)
        self.assertEqual(library_name,library.name)
        self.assertEqual('PJB',library.initials)
        self.assertEqual('PJB_NY',library.prefix)
        self.assertEqual('17',library.index_as_string)
        self.assertEqual(17,library.index)
        self.assertFalse(library.is_barcoded)
        self.assertEqual(None,library.csfasta)
        self.assertEqual(None,library.qual)
        self.assertEqual(sample,library.parent_sample)
        self.assertEqual(library_name,str(library))

    def test_solid_library_with_files(self):
        """
        solid.data.Library: with files
        """
        sample_name = 'PJB_pool'
        library_name = 'PJB_NY17'
        sample = Sample(sample_name)
        library = Library(library_name,sample)
        library.csfasta = '/path/to/solid_PJB.csfasta'
        library.qual = '/path/to/solid_PJB_QV.qual'
        self.assertEqual('/path/to/solid_PJB.csfasta',library.csfasta)
        self.assertEqual('/path/to/solid_PJB_QV.qual',library.qual)
        self.assertEqual(library_name,str(library))

    def test_solid_library_with_no_sample(self):
        """
        solid.data.Library: no samples
        """
        library_name = 'PJB_NY17'
        library = Library(library_name)
        self.assertEqual(None,library.parent_sample)

    def test_solid_library_indexes(self):
        """
        solid.data.Library: handle indexes
        """
        # No index
        library_name = 'PJB_NY'
        library = Library(library_name)
        self.assertEqual('',library.index_as_string)
        self.assertEqual(None,library.index)
        # Leading zero
        library_name = 'PJB_NY_01'
        library = Library(library_name)
        self.assertEqual('01',library.index_as_string)
        self.assertEqual(1,library.index)
        # Trailing zero
        library_name = 'PJB_NY_10'
        library = Library(library_name)
        self.assertEqual('10',library.index_as_string)
        self.assertEqual(10,library.index)


class TestSample(unittest.TestCase):
    """
    Unit tests for Sample class.
    """
    def test_solid_sample(self):
        """
        solid.data.Sample: basic properties
        """
        sample_name = 'PJB_pool'
        sample = Sample(sample_name)
        self.assertEqual(sample_name,sample.name)
        self.assertEqual(None,sample.parent_run)
        self.assertEqual(None,sample.barcode_stats)
        self.assertEqual(None,sample.libraries_dir)
        self.assertEqual(0,len(sample.libraries))
        self.assertEqual(0,len(sample.projects))

    def test_solid_sample_add_library(self):
        """
        solid.data.Sample: add libraries
        """
        sample_name = 'PJB_pool'
        sample = Sample(sample_name)
        self.assertEqual(0,len(sample.libraries))
        # Add first library
        library = sample.add_library('PJB_NY_17')
        self.assertTrue(isinstance(library, Library))
        self.assertEqual(1,len(sample.libraries))
        self.assertEqual(library,sample.get_library('PJB_NY_17'))
        # Add second library
        library2 = sample.add_library('PJB_NY_18')
        self.assertTrue(isinstance(library2, Library))
        self.assertEqual(2,len(sample.libraries))
        self.assertEqual(library2,sample.get_library('PJB_NY_18'))
        # Add same library again
        self.assertEqual(library2,sample.add_library('PJB_NY_18'))
        self.assertEqual(2,len(sample.libraries))
        # Fetch non-existent library
        self.assertEqual(None,sample.get_library('PJB_NY_19'))

    def test_solid_sample_get_project(self):
        """
        solid.data.Sample: get project
        """
        sample_name = 'PJB_pool'
        sample = Sample(sample_name)
        self.assertEqual(0,len(sample.projects))
        # Add libraries
        library = sample.add_library('PJB_NY_17')
        library = sample.add_library('PJB_NY_18')
        # Fetch project
        self.assertEqual(1,len(sample.projects))
        project = sample.get_project('PJB')
        self.assertTrue(isinstance(project, Project))
        # Fetch non-existant project
        self.assertEqual(None,sample.get_project('BJP'))


class TestProject(unittest.TestCase):
    """
    Unit tests for Project class
    """
    def setUp(self):
        # Construct a sample object and populate
        # with libraries
        self.library_names = ['PJB_NY_17',
                              'PJB_NY_18',
                              'PJB_NY_19']
        self.sample = Sample('PJB_pool')
        for name in self.library_names:
            self.sample.add_library(name)
        self.project = self.sample.projects[0]

    def test_libraries(self):
        """
        solid.data.Project: check library data
        """
        # Correct number of libraries
        self.assertEqual(len(self.library_names),
                         len(self.project.libraries))
        # Check each library
        for i in range(len(self.library_names)):
            self.assertTrue(isinstance(self.project.libraries[i], Library))
            self.assertEqual(self.library_names[i],
                             self.project.libraries[i].name)

    def test_get_sample(self):
        """
        solid.data.Project: retrieve of parent sample
        """
        # Check for project with parent sample defined
        self.assertEqual(self.sample, self.project.get_sample())
        # Check for project with no parent sample
        self.assertEqual(None, Project('No_sample').get_sample())

    def test_get_run(self):
        """
        solid.data.Project: retrieve parent run
        """
        self.assertEqual(None, self.project.get_run())

    def test_is_barcoded(self):
        """
        solid.data.Project: check if all libraries are barcoded
        """
        # Check test project
        self.assertFalse(self.project.is_barcoded())
        # Alter libraries in project so all have barcode flag set
        for lib in self.project.libraries:
            lib.is_barcoded = True
        self.assertTrue(self.project.is_barcoded())
        # Check with empty project (i.e. no libraries)
        self.assertFalse(Project('No_libraries').is_barcoded())

    def test_get_library_name_pattern(self):
        """
        solid.data.Project: generate pattern for library names
        """
        self.assertEqual('PJB_NY_1*',
                         self.project.get_library_name_pattern())

    def test_get_project_name(self):
        """
        solid.data.Project: check assigned project name
        """
        self.assertEqual('PJB_pool', self.project.get_project_name())

    def test_pretty_print_libraries(self):
        """
        solid.data.Project: pretty print libraries
        """
        self.assertEqual('PJB_NY_17-19',self.project.pretty_print_libraries())


class TestRunDefinition(unittest.TestCase):
    """
    Unit tests for RunDefinition class.
    """
    def setUp(self):
        self.tmp_defn_file = TestUtils().make_run_definition_file()
        self.run_defn = RunDefinition(self.tmp_defn_file)

    def tearDown(self):
        os.remove(self.tmp_defn_file)

    def test_run_definition(self):
        """
        solid.data.RunDefinition: basic properties
        """
        self.assertTrue(isinstance(self.run_defn, RunDefinition))
        self.assertTrue(self.run_defn)

    def test_run_definition_n_samples(self):
        """
        solid.data.RunDefinition: basic properties
        """
        self.assertEqual(12,self.run_defn.n_samples())

    def test_run_definition_attributes(self):
        """
        solid.data.RunDefinition: check attributes
        """
        self.assertEqual(self.run_defn.version,'v0.0')
        self.assertEqual(self.run_defn.userId,'user')
        self.assertEqual(self.run_defn.runType,'FRAGMENT')
        self.assertEqual(self.run_defn.isMultiplexing,'TRUE')
        self.assertEqual(self.run_defn.runName,'solid0123_20130426_FRAG_BC_2')
        self.assertEqual(self.run_defn.runDesc,'')
        self.assertEqual(self.run_defn.mask,'1_spot_mask_sf')
        self.assertEqual(self.run_defn.protocol,'SOLiD4 Multiplex')

    def test_run_definition_fields(self):
        """
        solid.data.RunDefinition: check fields
        """
        self.assertEqual(['sampleName',
                          'sampleDesc',
                          'spotAssignments',
                          'primarySetting',
                          'library',
                          'application',
                          'secondaryAnalysis',
                          'multiplexingSeries',
                          'barcodes'],
                         self.run_defn.fields())

    def test_run_definition_get_data_item(self):
        """
        solid.data.RunDefinition: get data items
        """
        # Check first line
        self.assertEqual('AB_CD_EF_pool',
                         self.run_defn.get_data_item('sampleName',0))
        self.assertEqual('CD_UV5',self.
                         run_defn.get_data_item('library',0))
        self.assertEqual('mm9',
                         self.run_defn.get_data_item('secondaryAnalysis',0))
        # Check line in middle
        self.assertEqual('AB_CD_EF_pool',
                         self.run_defn.get_data_item('sampleName',4))
        self.assertEqual('EF12',
                         self.run_defn.get_data_item('library',4))
        self.assertEqual('dm5',
                         self.run_defn.get_data_item('secondaryAnalysis',4))
        # Check non-existent line
        self.assertRaises(IndexError,
                          self.run_defn.get_data_item,'sampleName',12)
        # Check non-existent field
        self.assertEqual(None,
                         self.run_defn.get_data_item('tertiaryAnalysis',0))
        self.assertEqual(None,
                         self.run_defn.get_data_item('tertiaryAnalysis',12))

    def test_nonexistent_run_definition_file(self):
        """
        solid.data.RunDefinition: missing run definition file
        """
        run_defn = RunDefinition("i_dont_exist")
        self.assertFalse(run_defn)


class TestBarcodeStatistics(unittest.TestCase):
    """
    Unit tests for BarcodeStatistics class.
    """

    def setUp(self):
        self.tmp_stats_file = TestUtils().make_barcode_statistics_file()
        self.stats = BarcodeStatistics(self.tmp_stats_file)

    def tearDown(self):
        os.remove(self.tmp_stats_file)

    def test_barcode_statistics(self):
        """
        solid.data.BarcodeStatistics: basic properties
        """
        self.assertTrue(isinstance(self.stats, BarcodeStatistics))
        self.assertTrue(self.stats)

    def test_barcode_statistics_n_rows(self):
        """
        solid.data.BarcodeStatistics: number of rows
        """
        self.assertEqual(31,self.stats.n_rows())

    def test_barcode_statistics_header(self):
        """
        solid.data.BarcodeStatistics: header
        """
        self.assertEqual(['Library',
                          'Barcode',
                          '0 Mismatches',
                          '1 Mismatch',
                          'Total'],
                         self.stats.header)

    def test_barcode_statistics_get_data_by_name(self):
        """
        solid.data.BarcodeStatistics: get data by name
        """
        # Check "All Beads" line
        self.assertEqual(['All Beads',
                          'Totals',
                          '409927600',
                          '39452331',
                          '457541973'],
                         self.stats.get_data_by_name('All Beads'))
        # Check non-existent line
        self.assertEqual(None,self.stats.get_data_by_name('All beads'))

    def test_barcode_statistics_total_reads(self):
        """
        solid.data.BarcodeStatistics: total number of reads
        """
        # Total number for this example is 446268790
        self.assertEqual(446268790,self.stats.total_reads())

    def test_barcode_statistics_nonexistent_barcode_stats_file(self):
        """
        solid.data.BarcodeStatistics: missing barcode statistics
        """
        stats = BarcodeStatistics("i_dont_exist")
        self.assertFalse(stats)


class TestRunDir(unittest.TestCase):
    """
    Unit tests for RunDir class.
    """
    def setUp(self):
        # Set up a mock SOLiD directory structure
        self.solid_test_dir = \
            TestUtils().make_solid_dir('solid0123_20130426_FRAG_BC')
        # Create a RunDir object for tests
        self.solid_run = RunDir(self.solid_test_dir)

    def tearDown(self):
        shutil.rmtree(self.solid_test_dir)

    def test_run(self):
        """
        solid.data.RunDir: basic check
        """
        self.assertTrue(self.solid_run)

    def test_run_libraries_are_assigned(self):
        """
        solid.data.RunDir: check libraries are assigned
        """
        for sample in self.solid_run.samples:
            for library in sample.libraries:
                # Check names were assigned to data files
                self.assertNotEqual(None,library.csfasta)
                self.assertTrue(os.path.isfile(library.csfasta))
                self.assertNotEqual(None,library.qual)
                self.assertTrue(os.path.isfile(library.qual))
                # F5 reads should not be assigned
                self.assertEqual(None,library.csfasta_f5)
                self.assertEqual(None,library.qual_f5)

    def test_run_library_files_in_same_location(self):
        """
        solid.data.RunDir: check libraries locations are correct
        """
        for sample in self.solid_run.samples:
            for library in sample.libraries:
                # Check they're in the same location as each other
                self.assertEqual(os.path.dirname(library.csfasta),
                                 os.path.dirname(library.qual))

    def test_run_library_parent_dir_has_reject(self):
        """
        solid.data.RunDir: check library parent dir has 'reject' subdir
        """
        for sample in self.solid_run.samples:
            for library in sample.libraries:
                # Check that the parent dir also has "reject" dir
                self.assertTrue(os.path.isdir(
                        os.path.join(os.path.dirname(library.csfasta),
                                     '..','reject')))

    def test_run_fetch_libraries(self):
        """
        solid.data.RunDir: retrieve libraries
        """
        # Defaults should retrieve everything
        libraries = self.solid_run.fetch_libraries()
        self.assertEqual(len(libraries),12)
        for lib in libraries:
            self.assertEqual(libraries.count(lib),1)
        # "Bad" sample name shouldn't retrieve anything
        libraries = self.solid_run.fetch_libraries(
            sample_name='XY_PQ_VW_pool',library_name='*')
        self.assertEqual(len(libraries),0)
        # Specify exact sample and library names
        libraries = self.solid_run.fetch_libraries(
            sample_name='AB_CD_EF_pool',library_name='AB_A1M1')
        self.assertEqual(len(libraries),1)
        self.assertEqual(libraries[0].name,'AB_A1M1')
        # Specify wildcard library name
        libraries = self.solid_run.fetch_libraries(
            sample_name='AB_CD_EF_pool',library_name='AB_*')
        self.assertEqual(len(libraries),4)
        for lib in libraries:
            self.assertTrue(str(lib.name).startswith('AB_'))
            self.assertEqual(libraries.count(lib),1)
        # Specify wildcard sample and library name
        libraries = self.solid_run.fetch_libraries(
            sample_name='*',library_name='AB_*')
        self.assertEqual(len(libraries),4)
        for lib in libraries:
            self.assertTrue(str(lib.name).startswith('AB_'))
            self.assertEqual(libraries.count(lib),1)

    def test_run_slide_layout(self):
        """
        solid.data.RunDir: check slide layout information
        """
        self.assertEqual(self.solid_run.slide_layout(),"Whole slide")

    def test_run_nonexistent_solid_run_dir(self):
        """
        solid.data.RunDir: missing SOLiD run directory
        """
        solid_run = RunDir("/i/dont/exist/solid0123_20131013_FRAG_BC")
        self.assertFalse(solid_run)


class TestRunDirPairedEnd(unittest.TestCase):
    """
    Unit tests for RunDir class for paired-end run data.
    """
    def setUp(self):
        # Set up a mock SOLiD directory structure
        self.solid_test_dir = \
            TestUtils().make_solid_dir_paired_end('solid0123_20130426_PE_BC')
        # Create a RunDir object for tests
        self.solid_run = RunDir(self.solid_test_dir)

    def tearDown(self):
        shutil.rmtree(self.solid_test_dir)

    def test_paired_end_run(self):
        """
        solid.data.RunDir: paired end run
        """
        self.assertTrue(self.solid_run)

    def test_paired_end_run_libraries_are_assigned(self):
        """
        solid.data.RunDir: libraries are assigned for paired end run
        """
        for sample in self.solid_run.samples:
            for library in sample.libraries:
                # Check names were assigned to data files
                self.assertNotEqual(None,library.csfasta)
                self.assertTrue(os.path.isfile(library.csfasta))
                self.assertNotEqual(None,library.qual)
                self.assertTrue(os.path.isfile(library.qual))
                # Check read names contain "_F3_"
                self.assertTrue(library.csfasta.rfind("_F3_") > -1)
                self.assertTrue(library.qual.rfind("_F3_") > -1)
                # F5 reads
                self.assertNotEqual(None,library.csfasta_f5)
                self.assertTrue(os.path.isfile(library.csfasta_f5))
                self.assertNotEqual(None,library.qual_f5)
                self.assertTrue(os.path.isfile(library.qual_f5))
                # Check F5 read names contain "_F5-BC_"
                self.assertTrue(library.csfasta_f5.rfind("_F5-BC_") > -1)
                self.assertTrue(library.qual_f5.rfind("_F5-BC_") > -1)

    def test_paired_end_run_library_files_in_same_location(self):
        """
        solid.data.RunDir: library files in same location for paired end run
        """
        for sample in self.solid_run.samples:
            for library in sample.libraries:
                # Check they're in the same location as each other
                self.assertEqual(os.path.dirname(library.csfasta),
                                 os.path.dirname(library.qual))
                self.assertEqual(os.path.dirname(library.csfasta_f5),
                                 os.path.dirname(library.qual_f5))

    def test_paired_end_run_library_parent_dir_has_reject(self):
        """
        solid.data.RunDir: library parent dir has "reject" dir for paired end run
        """
        for sample in self.solid_run.samples:
            for library in sample.libraries:
                # Check that the parent dirs also has "reject" dir
                self.assertTrue(os.path.isdir(
                        os.path.join(os.path.dirname(library.csfasta),
                                     '..','reject')))
                self.assertTrue(os.path.isdir(
                        os.path.join(os.path.dirname(library.csfasta_f5),
                                     '..','reject')))

    def test_paired_end_run_fetch_libraries(self):
        """
        solid.data.RunDir: retrieve libraries for paired end run
        """
        # Defaults should retrieve everything
        libraries = self.solid_run.fetch_libraries()
        self.assertEqual(len(libraries),11)
        for lib in libraries:
            self.assertEqual(libraries.count(lib),1)
        # "Bad" sample name shouldn't retrieve anything
        libraries = self.solid_run.fetch_libraries(
            sample_name='XY_PQ_VW_pool',library_name='*')
        self.assertEqual(len(libraries),0)
        # Specify exact sample and library names
        libraries = self.solid_run.fetch_libraries(
            sample_name='AB_CD_pool',library_name='AB_SEQ26')
        self.assertEqual(len(libraries),1)
        self.assertEqual(libraries[0].name,'AB_SEQ26')
        # Specify wildcard library name
        libraries = self.solid_run.fetch_libraries(sample_name='AB_CD_pool',
                                                   library_name='AB_*')
        self.assertEqual(len(libraries),8)
        for lib in libraries:
            self.assertTrue(str(lib.name).startswith('AB_'))
            self.assertEqual(libraries.count(lib),1)
        # Specify wildcard sample and library name
        libraries = self.solid_run.fetch_libraries(sample_name='*',
                                                   library_name='AB_*')
        self.assertEqual(len(libraries),8)
        for lib in libraries:
            self.assertTrue(str(lib.name).startswith('AB_'))
            self.assertEqual(libraries.count(lib),1)


class TestRunDirDifferentDirName(unittest.TestCase):
    """
    Unit tests for RunDir class when directory name doesn't match run name.
    """
    def setUp(self):
        # Set up a mock SOLiD directory structure
        self.solid_test_dir = TestUtils().make_solid_dir('solid0123_20130426_FRAG_BC')
        # Rename to something else
        os.rename(self.solid_test_dir,self.solid_test_dir+"_different")
        self.solid_test_dir = self.solid_test_dir+"_different"

    def tearDown(self):
        shutil.rmtree(self.solid_test_dir)

    def test_solid_run_different_dir_name(self):
        """
        solid.data.RunDir: directory name doesn't match run name
        """
        # Create a RunDir
        self.solid_run = RunDir(self.solid_test_dir)
        self.assertTrue(self.solid_run)
        # Check the run name
        self.assertEqual(self.solid_run.run_name,'solid0123_20130426_FRAG_BC')


class TestRunDirVerify(unittest.TestCase):
    """
    Unit tests for RunDir.verify method
    """
    def setUp(self):
        # Set up a mock SOLiD directory structure
        self.solid_test_dir = TestUtils().make_solid_dir('solid0123_20130426_FRAG_BC')

    def tearDown(self):
        shutil.rmtree(self.solid_test_dir)

    def test_run_verify(self):
        """
        solid.data.RunDir: test 'verify'
        """
        self.assertTrue(RunDir(self.solid_test_dir).verify())

    def test_run_verify_missing_csfasta(self):
        """
        solid.data.RunDir: test 'verify' (missing .csfasta file)
        """
        # Remove some files
        solid_run = RunDir(self.solid_test_dir)
        os.remove(solid_run.samples[0].libraries[0].csfasta)
        # Test
        self.assertFalse(RunDir(self.solid_test_dir).verify())

    def test_run_verify_missing_qual(self):
        """
        solid.data.RunDir: test 'verify' (missing .qual file)
        """
        # Remove some files
        solid_run = RunDir(self.solid_test_dir)
        os.remove(solid_run.samples[0].libraries[0].qual)
        # Test
        self.assertFalse(RunDir(self.solid_test_dir).verify())


class TestRunDirVerifyPairedEnd(unittest.TestCase):
    """
    Unit tests for RunDir.verify method for paired-end data
    """
    def setUp(self):
        # Set up a mock SOLiD directory structure
        self.solid_test_dir = \
            TestUtils().make_solid_dir_paired_end('solid0123_20130426_PE_BC')

    def tearDown(self):
        shutil.rmtree(self.solid_test_dir)

    def test_run_verify(self):
        """
        solid.data.RunDir: test 'verify' with paired end data
        """
        self.assertTrue(RunDir(self.solid_test_dir).verify())

    def test_run_verify_missing_csfasta(self):
        """
        solid.data.RunDir: test 'verify' with paired end data (missing .csfasta)
        """
        # Remove some files
        solid_run = RunDir(self.solid_test_dir)
        os.remove(solid_run.samples[0].libraries[0].csfasta)
        # Test
        self.assertFalse(RunDir(self.solid_test_dir).verify())

    def test_run_verify_missing_qual(self):
        """
        solid.data.RunDir: test 'verify' with paired end data (missing .qual)
        """
        # Remove some files
        solid_run = RunDir(self.solid_test_dir)
        os.remove(solid_run.samples[0].libraries[0].qual)
        # Test
        self.assertFalse(RunDir(self.solid_test_dir).verify())


class TestRunDirNoRunDefinition(unittest.TestCase):
    """
    Unit tests for RunDir class when directory doesn't have RunDefinition
    file.
    """
    def setUp(self):
        # Set up a mock SOLiD directory structure
        self.solid_test_dir = TestUtils().make_solid_dir('solid0123_20130426_FRAG_BC')
        # Remove RunDefinition file
        os.remove(os.path.join(
            self.solid_test_dir,
            'solid0123_20130426_FRAG_BC_run_definition.txt'))

    def tearDown(self):
        shutil.rmtree(self.solid_test_dir)

    def test_run_with_no_run_definition(self):
        """
        solid.data.RunDir: missing run definition file
        """
        # Create a RunDir
        self.solid_run = RunDir(self.solid_test_dir)
        self.assertTrue(self.solid_run)
        # Check the run name
        self.assertEqual(self.solid_run.run_name,
                         'solid0123_20130426_FRAG_BC')
        # Check the paired-ended-ness
        self.assertFalse(self.solid_run.is_paired_end)


class TestRunDirNotASolidRunDir(unittest.TestCase):
    def setUp(self):
        # Set up a non-SOLiD directory structure
        self.test_dir = tempfile.mkdtemp()
        dirname = os.path.join(self.test_dir,'test')
        os.mkdir(dirname)
        os.makedirs(dirname+'/AB/results')
        os.makedirs(dirname+'/CD')
        os.makedirs(dirname+'/random/stuff')

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_run_not_a_solid_run_dir(self):
        """
        solid.data.RunDir: try to load a non-SOLiD run directory
        """
        # Create a RunDir
        self.solid_run = RunDir(self.test_dir)
        self.assertFalse(self.solid_run)


class TestFunctions(unittest.TestCase):
    """
    Unit tests for module functions.
    """
    def test_is_paired_end(self):
        """
        is_paired_end: check returns correct values
        """
        # Test with non-paired end mock SOLiD directory
        self.solid_test_dir = TestUtils().make_solid_dir(
            'solid0123_20130426_FRAG_BC')
        self.solid_run = RunDir(self.solid_test_dir)
        self.assertFalse(is_paired_end(self.solid_run))
        shutil.rmtree(self.solid_test_dir)
        # Test with paired end mock SOLiD directory
        self.solid_test_dir = TestUtils().make_solid_dir_paired_end(
            'solid0123_20130426_PE_BC')
        self.solid_run = RunDir(self.solid_test_dir)
        self.assertTrue(is_paired_end(self.solid_run))
        shutil.rmtree(self.solid_test_dir)

    def test_extract_library_timestamp(self):
        """
        extract_library_timestamp: check timestamp is extracted
        """
        self.assertEqual(extract_library_timestamp("/path/to/data/solid0123_20120712_FRAG_BC/AB_CD_EF_POOL/results.F1B1/libraries/AB2/primary.20120705075541493"),'20120705075541493')
        self.assertEqual(extract_library_timestamp("/path/to/data/solid0123_20120712_FRAG_BC/AB_CD_EF_POOL/results.F1B1/libraries/AB2/primary.20120705075541493/"),'20120705075541493')
        self.assertEqual(extract_library_timestamp("/path/to/data/solid0123_20120712_FRAG_BC/AB_CD_EF_POOL/results.F1B1/libraries/AB2/primary.20120705075541493/reads"),'20120705075541493')
        self.assertEqual(extract_library_timestamp("/path/to/data/solid0123_20120712_FRAG_BC/AB_CD_EF_POOL/results.F1B1/libraries/AB2"),None)

    def test_slide_layout(self):
        """
        slide_layout: check slide layout descriptions
        """
        self.assertEqual("Whole slide",slide_layout(1))
        self.assertEqual("Quads",slide_layout(4))
        self.assertEqual("Octets",slide_layout(8))
        # Example of "bad" numbers of sample
        self.assertEqual(None,slide_layout(7))
        self.assertEqual(None,slide_layout("porkchops"))
