#######################################################################
# Tests
#######################################################################

import unittest
import io
from bcftbx.cli.xrorthologs import ProbeSetLookup
from bcftbx.cli.xrorthologs import IndexedFile
from bcftbx.cli.xrorthologs import combine_data_main

class TestProbeSetLookup(unittest.TestCase):
    """Test the ProbeSetLookup class
    """

    def setUp(self):
        # Example look up data
        self.fp1 = io.StringIO(u"""ps_1	gid_1	gid_2	ps_2
1053_at	5982	19718	1417503_at,1457638_x_at,1457669_x_at
117_at	3310	NA	NA
121_at	7849	18510	1418208_at,1446561_at
1255_g_at	2978	14913	1421061_at
1294_at	7318	74153	1426970_a_at,1426971_at,1437317_at
203281_s_at	7318	74153	1426970_a_at,1426971_at,1437317_at
""")
        self.fp2 = io.StringIO(u"""ps_1	gid_1	gid_2	ps_2
1053_at	1417503_at,1457638_x_at,1457669_x_at
117_at	NA
121_at	1418208_at,1446561_at
1255_g_at	1421061_at
1294_at	1426970_a_at,1426971_at,1437317_at
203281_s_at	1426970_a_at,1426971_at,1437317_at
""")

    def test_lookup(self):
        """Test forward lookup
        """
        lookup = ProbeSetLookup(lookup_data_fp=self.fp1)
        self.assertEqual(lookup.lookup('1255_g_at'),['1421061_at'])
        self.assertEqual(lookup.lookup('1294_at'),['1426970_a_at',
                                                   '1426971_at',
                                                   '1437317_at'])

    def test_reverse_lookup(self):
        """Test reverse lookup
        """
        lookup = ProbeSetLookup(lookup_data_fp=self.fp1)
        self.assertEqual(lookup.reverse_lookup('1421061_at'),['1255_g_at'])
        self.assertEqual(lookup.reverse_lookup('1437317_at'),['1294_at','203281_s_at'])

    def test_null_value(self):
        """Test checking for null value
        """
        lookup = ProbeSetLookup(lookup_data_fp=self.fp1)
        self.assertEqual(lookup.reverse_lookup('117_at'),[])

    def test_lookup_different_columns(self):
        """Test using different columns from input file
        """
        lookup = ProbeSetLookup(lookup_data_fp=self.fp2,cols=(0,1))
        self.assertEqual(lookup.lookup('1255_g_at'),['1421061_at'])
        self.assertEqual(lookup.lookup('1294_at'),['1426970_a_at',
                                                   '1426971_at',
                                                   '1437317_at'])

class TestIndexedFile(unittest.TestCase):
    """Test the IndexedFile class
    """
    def setUp(self):
        # Example data
        self.fp = io.StringIO(u"""1007_s_at	U48705	chr6:30856165-30867931 (+) // 95.63 // p21.33	discoidin domain receptor tyrosine kinase 1	DDR1	900.8253051	1002.945639	0.898179	-1.11336
1053_at	M87338	chr7:73646002-73668732 (-) // 70.86 // q11.23	"replication factor C (activator 1) 2, 40kDa"	RFC2	953.0037594	1100.132756	0.866288	-1.15435
117_at	X51757	chr1:161494448-161496380 (+) // 99.59 // q23.3 /// chr1:161576080-161578007 (+) // 98.03 // q23.3	heat shock 70kDa protein 6 (HSP70B')	HSPA6	37.34984439	43.5182996	0.858256	-1.16515
121_at	X69699	chr2:113974939-114036488 (-) // 98.3 // q13	paired box 8	PAX8	293.4040238233.8182798	1.25484	1.25484
""")

    def test_indexed_file(self):
        """Test IndexedFile methods
        """
        indexed_file = IndexedFile(fp=self.fp)
        self.assertEqual(indexed_file.keys(),['1007_s_at',
                                              '1053_at',
                                              '117_at',
                                              '121_at'])
        self.assertEqual(indexed_file.fetch('117_at'),"""117_at	X51757	chr1:161494448-161496380 (+) // 99.59 // q23.3 /// chr1:161576080-161578007 (+) // 98.03 // q23.3	heat shock 70kDa protein 6 (HSP70B')	HSPA6	37.34984439	43.5182996	0.858256	-1.16515""")

class TestCombineData(unittest.TestCase):
    def setUp(self):
        # Example data
        self.species1 = u"""Probe_Set_ID	Public_ID
1053_at	M87338
117_at	X51757
121_at	X69699
1255_g_at	L36861
"""
        self.species2 = u"""Probe_Set_ID	Public_ID
1417503_at	NM_020022
1457638_x_at	AV039064
1457669_x_at	AV096765
1418208_at	NM_011040
1446561_at	BB497767
1421061_at	NM_008189
1426970_a_at	AK004894
1426971_at	AK004894
1437317_at	BB735820
"""
        self.lookup_data = u"""ps_1	gid_1	gid_2	ps_2
1053_at	5982	19718	1417503_at,1457638_x_at,1457669_x_at
117_at	3310	NA	NA
121_at	7849	18510	1418208_at,1446561_at
1255_g_at	2978	14913	1421061_at
1294_at	7318	74153	1426970_a_at,1426971_at,1437317_at
"""
        self.expected_output = u"""Probe_Set_ID	Public_ID	Probe_Set_ID_1	Public_ID_1	Probe_Set_ID_2	Public_ID_2	Probe_Set_ID_3	Public_ID_3
1053_at	M87338	1417503_at	NM_020022	1457638_x_at	AV039064	1457669_x_at	AV096765
117_at	X51757
121_at	X69699	1418208_at	NM_011040	1446561_at	BB497767
1255_g_at	L36861	1421061_at	NM_008189
"""

    def test_combine_data(self):
        """Test combine_data function
        """
        # Input data
        data1 = IndexedFile(fp=io.StringIO(self.species1),first_line_is_header=True)
        data2 = IndexedFile(fp=io.StringIO(self.species2),first_line_is_header=True)
        lookup = ProbeSetLookup(lookup_data_fp=io.StringIO(self.lookup_data))
        # Output "file"
        output_fp = io.StringIO()
        # Run data combination
        combine_data_main(data1,data2,lookup.lookup,output_fp)
        # Check output
        self.assertEqual(output_fp.getvalue(),self.expected_output)
