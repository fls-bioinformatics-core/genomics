########################################################################
# Tests for best_exons.py
#########################################################################

from builtins import str
import unittest
import io
from best_exons import Exon
from best_exons import ExonList
from best_exons import best_exons
from best_exons import tsv_line
from best_exons import ordinal

class TestExon(unittest.TestCase):
    """Tests for the Exon class
    """
    def test_exon_no_data(self):
        exon = Exon("PSR19025918.hg.1","A1BG")
        self.assertEqual(exon.name,"PSR19025918.hg.1")
        self.assertEqual(exon.gene_symbol,"A1BG")
        self.assertEqual(exon.log2_fold_change,None)
        self.assertEqual(exon.p_value,None)
        self.assertEqual(str(exon),
                         "PSR19025918.hg.1:A1BG:log2FoldChange=None;p-value=None")

    def test_exon_with_data(self):
        log2_fold_change = -0.056323333
        p_value = 0.5347865
        exon = Exon("PSR19025918.hg.1","A1BG",
                    log2_fold_change=log2_fold_change,
                    p_value=p_value)
        self.assertEqual(exon.name,"PSR19025918.hg.1")
        self.assertEqual(exon.gene_symbol,"A1BG")
        self.assertEqual(exon.log2_fold_change,log2_fold_change)
        self.assertEqual(exon.p_value,p_value)
        self.assertEqual(str(exon),
                         "PSR19025918.hg.1:A1BG:log2FoldChange=%s;p-value=%s" %
                         (float(log2_fold_change),float(p_value)))

class TestExonList(unittest.TestCase):
    """Tests for the ExonList class
    """
    def test_exon_list(self):
        exon_list = ExonList("A1BG")
        self.assertEqual(exon_list.gene_symbol,"A1BG")
        self.assertEqual(len(exon_list),0)
        exon_list.add_exon(Exon("PSR19025918.hg.1","A1BG"))
        exon_list.add_exon(Exon("PSR19025921.hg.1","A1BG"))
        self.assertEqual(len(exon_list),2)

    def test_exon_list_iteration(self):
        exon_list = ExonList("A1BG")
        self.assertEqual(exon_list.gene_symbol,"A1BG")
        self.assertEqual(len(exon_list),0)
        exon_list.add_exon(Exon("PSR19025918.hg.1","A1BG"))
        exon_list.add_exon(Exon("PSR19025921.hg.1","A1BG"))
        exon_list.add_exon(Exon("PSR19025922.hg.1","A1BG"))
        for exon,name in zip(exon_list,
                             ("PSR19025918.hg.1",
                              "PSR19025921.hg.1",
                              "PSR19025922.hg.1")):
            self.assertEqual(name,exon.name)

    def test_exon_list_sort_on_log2_fold_change(self):
        exon_list = ExonList("A1BG")
        exon_list.add_exon(Exon("PSR19025918.hg.1","A1BG",log2_fold_change=-0.056323333))
        exon_list.add_exon(Exon("PSR19025921.hg.1","A1BG",log2_fold_change=0.075113333))
        exon_list.add_exon(Exon("PSR19025922.hg.1","A1BG",log2_fold_change=0.037316667))
        exon_list.add_exon(Exon("PSR19025925.hg.1","A1BG",log2_fold_change=-0.10211))
        exon_list.add_exon(Exon("PSR19025926.hg.1","A1BG",log2_fold_change=0.059556667))
        exon_list.add_exon(Exon("PSR19025927.hg.1","A1BG",log2_fold_change=0.119746667))
        exon_list.add_exon(Exon("PSR19025928.hg.1","A1BG",log2_fold_change=-0.090296667))
        exon_list.add_exon(Exon("PSR19025929.hg.1","A1BG",log2_fold_change=-0.02433))
        exon_list.add_exon(Exon("PSR19025930.hg.1","A1BG",log2_fold_change=0.02569))
        exon_list.sort('log2_fold_change')
        last_log2_fold_change = None
        for exon in exon_list.exons:
            if last_log2_fold_change is not None:
                self.assertTrue(last_log2_fold_change >= exon.log2_fold_change)
            last_log2_fold_change = exon.log2_fold_change

    def test_exon_list_sort_on_p_value(self):
        exon_list = ExonList("A1BG")
        exon_list.add_exon(Exon("PSR19025918.hg.1","A1BG",p_value=0.5347865))
        exon_list.add_exon(Exon("PSR19025921.hg.1","A1BG",p_value=0.5820691))
        exon_list.add_exon(Exon("PSR19025922.hg.1","A1BG",p_value=0.7582407))
        exon_list.add_exon(Exon("PSR19025925.hg.1","A1BG",p_value=0.4111732))
        exon_list.add_exon(Exon("PSR19025926.hg.1","A1BG",p_value=0.6550312))
        exon_list.add_exon(Exon("PSR19025927.hg.1","A1BG",p_value=0.5002532))
        exon_list.add_exon(Exon("PSR19025928.hg.1","A1BG",p_value=0.3521274))
        exon_list.add_exon(Exon("PSR19025929.hg.1","A1BG",p_value=0.7716908))
        exon_list.add_exon(Exon("PSR19025930.hg.1","A1BG",p_value=0.7720515))
        exon_list.sort('p_value')
        last_p_value = None
        for exon in exon_list.exons:
            if last_p_value is not None:
                self.assertTrue(last_p_value <= exon.p_value)
            last_p_value = exon.p_value

    def test_get_best_exon_from_log2_fold_change(self):
        # First example
        exon_list = ExonList("A1BG")
        exon_list.add_exon(Exon("PSR19025918.hg.1","A1BG",log2_fold_change=-0.056323333))
        exon_list.add_exon(Exon("PSR19025921.hg.1","A1BG",log2_fold_change=0.075113333))
        exon_list.add_exon(Exon("PSR19025922.hg.1","A1BG",log2_fold_change=0.037316667))
        exon_list.add_exon(Exon("PSR19025925.hg.1","A1BG",log2_fold_change=-0.10211))
        exon_list.add_exon(Exon("PSR19025926.hg.1","A1BG",log2_fold_change=0.059556667))
        exon_list.add_exon(Exon("PSR19025927.hg.1","A1BG",log2_fold_change=0.119746667))
        exon_list.add_exon(Exon("PSR19025928.hg.1","A1BG",log2_fold_change=-0.090296667))
        exon_list.add_exon(Exon("PSR19025929.hg.1","A1BG",log2_fold_change=-0.02433))
        exon_list.add_exon(Exon("PSR19025930.hg.1","A1BG",log2_fold_change=0.02569))
        best_exon = exon_list.best_exon('log2_fold_change')
        self.assertEqual(best_exon.name,"PSR19025927.hg.1")
        # Second example
        exon_list = ExonList("A1BG")
        exon_list.add_exon(Exon("PSR19025918.hg.1","A1BG",log2_fold_change=-0.056323333))
        exon_list.add_exon(Exon("PSR19025921.hg.1","A1BG",log2_fold_change=0.075113333))
        exon_list.add_exon(Exon("PSR19025922.hg.1","A1BG",log2_fold_change=0.037316667))
        exon_list.add_exon(Exon("PSR19025925.hg.1","A1BG",log2_fold_change=-0.10211))
        exon_list.add_exon(Exon("PSR19025926.hg.1","A1BG",log2_fold_change=0.059556667))
        exon_list.add_exon(Exon("PSR19025928.hg.1","A1BG",log2_fold_change=-0.090296667))
        exon_list.add_exon(Exon("PSR19025929.hg.1","A1BG",log2_fold_change=-0.02433))
        exon_list.add_exon(Exon("PSR19025930.hg.1","A1BG",log2_fold_change=0.02569))
        best_exon = exon_list.best_exon('log2_fold_change')
        self.assertEqual(best_exon.name,"PSR19025925.hg.1")

    def test_get_best_exon_from_p_value(self):
        exon_list = ExonList("A1BG")
        exon_list.add_exon(Exon("PSR19025918.hg.1","A1BG",p_value=0.5347865))
        exon_list.add_exon(Exon("PSR19025921.hg.1","A1BG",p_value=0.5820691))
        exon_list.add_exon(Exon("PSR19025922.hg.1","A1BG",p_value=0.7582407))
        exon_list.add_exon(Exon("PSR19025925.hg.1","A1BG",p_value=0.4111732))
        exon_list.add_exon(Exon("PSR19025926.hg.1","A1BG",p_value=0.6550312))
        exon_list.add_exon(Exon("PSR19025927.hg.1","A1BG",p_value=0.5002532))
        exon_list.add_exon(Exon("PSR19025928.hg.1","A1BG",p_value=0.3521274))
        exon_list.add_exon(Exon("PSR19025929.hg.1","A1BG",p_value=0.7716908))
        exon_list.add_exon(Exon("PSR19025930.hg.1","A1BG",p_value=0.7720515))
        best_exon = exon_list.best_exon('p_value')
        self.assertEqual(best_exon.name,"PSR19025928.hg.1")

    def test_get_best_exons_from_log2_fold_change(self):
        # First example
        exon_list = ExonList("A1BG")
        exon_list.add_exon(Exon("PSR19025918.hg.1","A1BG",log2_fold_change=-0.056323333))
        exon_list.add_exon(Exon("PSR19025921.hg.1","A1BG",log2_fold_change=0.075113333))
        exon_list.add_exon(Exon("PSR19025922.hg.1","A1BG",log2_fold_change=0.037316667))
        exon_list.add_exon(Exon("PSR19025925.hg.1","A1BG",log2_fold_change=-0.10211))
        exon_list.add_exon(Exon("PSR19025929.hg.1","A1BG",log2_fold_change=-0.02433))
        best_exons = exon_list.best_exons('log2_fold_change')
        self.assertEqual(len(best_exons),3)
        for exon,name in zip(best_exons,("PSR19025925.hg.1",
                                         "PSR19025918.hg.1",
                                         "PSR19025929.hg.1")):
            self.assertEqual(name,exon.name)
        # Second example
        exon_list = ExonList("A1BG")
        exon_list.add_exon(Exon("PSR19025926.hg.1","A1BG",log2_fold_change=0.059556667))
        exon_list.add_exon(Exon("PSR19025927.hg.1","A1BG",log2_fold_change=0.119746667))
        exon_list.add_exon(Exon("PSR19025928.hg.1","A1BG",log2_fold_change=-0.090296667))
        exon_list.add_exon(Exon("PSR19025929.hg.1","A1BG",log2_fold_change=-0.02433))
        exon_list.add_exon(Exon("PSR19025930.hg.1","A1BG",log2_fold_change=0.02569))
        best_exons = exon_list.best_exons('log2_fold_change')
        self.assertEqual(len(best_exons),3)
        for exon,name in zip(best_exons,("PSR19025927.hg.1",
                                         "PSR19025926.hg.1",
                                         "PSR19025930.hg.1")):
            self.assertEqual(name,exon.name)

    def test_get_best_exons_from_p_value(self):
        exon_list = ExonList("A1BG")
        exon_list.add_exon(Exon("PSR19025918.hg.1","A1BG",p_value=0.5347865))
        exon_list.add_exon(Exon("PSR19025921.hg.1","A1BG",p_value=0.5820691))
        exon_list.add_exon(Exon("PSR19025922.hg.1","A1BG",p_value=0.7582407))
        exon_list.add_exon(Exon("PSR19025925.hg.1","A1BG",p_value=0.4111732))
        exon_list.add_exon(Exon("PSR19025929.hg.1","A1BG",p_value=0.7716908))
        best_exons = exon_list.best_exons('p_value')
        self.assertEqual(len(best_exons),3)
        for exon,name in zip(best_exons,("PSR19025925.hg.1",
                                         "PSR19025918.hg.1",
                                         "PSR19025921.hg.1")):
            self.assertEqual(name,exon.name)

    def test_get_best_exons_small_list(self):
        exon_list = ExonList("A1BG")
        exon_list.add_exon(Exon("PSR19025918.hg.1","A1BG",log2_fold_change=-0.056323333))
        exon_list.add_exon(Exon("PSR19025921.hg.1","A1BG",log2_fold_change=0.075113333))
        best_exons = exon_list.best_exons('log2_fold_change')
        self.assertEqual(len(best_exons),2)
        for exon,name in zip(best_exons,("PSR19025921.hg.1",
                                         "PSR19025918.hg.1")):
            self.assertEqual(name,exon.name)

    def test_average_numerical_data(self):
        exon_list = ExonList("A1BG")
        exon_list.add_exon(Exon("PSR19025918.hg.1","A1BG",log2_fold_change=-0.056323333,
                                data=[8.0,8.5,9.0]))
        exon_list.add_exon(Exon("PSR19025921.hg.1","A1BG",log2_fold_change=0.075113333,
                                data=[7.0,7.0,7.5]))
        exon_list.add_exon(Exon("PSR19025922.hg.1","A1BG",log2_fold_change=0.037316667,
                                data=[7.0,7.5,7.0]))
        exon_list.add_exon(Exon("PSR19025925.hg.1","A1BG",log2_fold_change=-0.10211,
                                data=[7.0,7.5,7.5]))
        exon_list.add_exon(Exon("PSR19025929.hg.1","A1BG",log2_fold_change=-0.02433,
                                data=[5.0,6.0,6.5]))
        averaged_data = exon_list.average()
        for average,expected in zip(averaged_data,(6.8,
                                                   7.3,
                                                   7.5,)):
            self.assertEqual(average,expected)

    def test_average_mixed_data(self):
        exon_list = ExonList("A1BG")
        exon_list.add_exon(Exon("PSR19025918.hg.1","A1BG",log2_fold_change=-0.056323333,
                                data=["PSR19025918.hg.1","A1BG",8.0,8.5,9.0]))
        exon_list.add_exon(Exon("PSR19025921.hg.1","A1BG",log2_fold_change=0.075113333,
                                data=["PSR19025921.hg.1","A1BG",7.0,7.0,7.5]))
        exon_list.add_exon(Exon("PSR19025922.hg.1","A1BG",log2_fold_change=0.037316667,
                                data=["PSR19025922.hg.1","A1BG",7.0,7.5,7.0]))
        exon_list.add_exon(Exon("PSR19025925.hg.1","A1BG",log2_fold_change=-0.10211,
                                data=["PSR19025925.hg.1","A1BG",7.0,7.5,7.5]))
        exon_list.add_exon(Exon("PSR19025929.hg.1","A1BG",log2_fold_change=-0.02433,
                                data=["PSR19025929.hg.1","A1BG",5.0,6.0,6.5]))
        averaged_data = exon_list.average()
        for average,expected in zip(averaged_data,(None,
                                                   None,
                                                   6.8,
                                                   7.3,
                                                   7.5,)):
            self.assertEqual(average,expected)

class TestBestExonsFunction(unittest.TestCase):
    """Tests for the best_exons function
    """
    def setUp(self):
        self.fp_in = io.StringIO(
u"""Probeset ID	Gene Symbol	1_1	1_2	2_1	2_2	3_1	3_2	Mean(Cntl)	Mean(siETV4)	Ratio(siETV4 vs. Cntl)	Fold-Change(siETV4 vs. Cntl)	log2FoldChange	p-value	q-value
PSR19025918.hg.1	A1BG	8.66755	8.57167	8.67935	8.73928	8.8101	8.67708	8.719	8.66267	0.961711	-1.03981	-0.056323333	0.5347865	0.725553
PSR19025921.hg.1	A1BG	7.41787	7.17961	7.40133	7.6528	7.28002	7.49215	7.36641	7.44152	1.05344	1.05344	0.075113333	0.5820691	0.7383465
PSR19025922.hg.1	A1BG	7.50871	7.57826	7.30645	7.61757	7.62477	7.35605	7.47998	7.51729	1.02621	1.02621	0.037316667	0.7582407	0.779675
PSR19025925.hg.1	A1BG	7.63027	7.58905	7.47073	7.30594	7.72141	7.62109	7.60747	7.50536	0.93167	-1.07334	-0.10211	0.4111732	0.6843703
PSR19025926.hg.1	A1BG	5.81209	5.89395	5.54714	5.50756	5.68944	5.82583	5.68289	5.74245	1.04215	1.04215	0.059556667	0.6550312	0.7570314
PSR19025927.hg.1	A1BG	6.36444	6.68116	6.4564	6.72256	6.32783	6.10419	6.38289	6.50264	1.08654	1.08654	0.119746667	0.5002532	0.7148393
PSR19025928.hg.1	A1BG	6.81897	6.76408	6.71385	6.55553	6.81366	6.75598	6.78216	6.69186	0.939329	-1.06459	-0.090296667	0.3521274	0.6606918
PSR19025929.hg.1	A1BG	8.45677	8.48843	8.44105	8.35951	8.52791	8.5048	8.47524	8.45091	0.983278	-1.01701	-0.02433	0.7716908	0.7822665
PSR19025930.hg.1	A1BG	6.86999	7.02037	6.87301	6.80701	6.86267	6.85536	6.86856	6.89425	1.01797	1.01797	0.02569	0.7720515	0.7823363
PSR19013233.hg.1	A1BG-AS1	7.08364	6.81108	6.98058	6.70364	6.85819	6.65799	6.97414	6.72424	0.840952	-1.18913	-0.2499	0.02997736	0.3577892
PSR19013235.hg.1	A1BG-AS1	6.55169	6.35594	6.37204	6.43176	6.53112	6.39524	6.48495	6.39432	0.939112	-1.06484	-0.090636667	0.3146458	0.6438243
PSR19013236.hg.1	A1BG-AS1	6.42098	5.92741	6.46143	6.36713	6.25817	6.65999	6.38019	6.31818	0.957924	-1.04392	-0.062016667	0.742372	0.7767089
""")

    def test_best_exons_by_log2_fold_change(self):
        expected_output = \
"""Gene Symbol	1_1	1_2	2_1	2_2	3_1	3_2	Mean(Cntl)	Mean(siETV4)	Ratio(siETV4 vs. Cntl)	Fold-Change(siETV4 vs. Cntl)	log2FoldChange	p-value	q-value	Less than 4 exons
A1BG	6.53146666667	6.58490666667	6.46829	6.62764	6.43243	6.47405666667	6.47739666667	6.56220333333	1.06071	1.06071	0.0848055556667	0.579117833333	0.736739066667
A1BG-AS1	6.68543666667	6.36481	6.60468333333	6.50084333333	6.54916	6.57107333333	6.61309333333	6.47891333333	0.912662666667	-1.09929666667	-0.134184444667	0.36233172	0.592774133333	*
"""
        fp_out = io.StringIO()
        best_exons(self.fp_in,fp_out,rank_by='log2_fold_change')
        output = fp_out.getvalue()
        for obs,exp in zip(output.split(),expected_output.split()):
            ##print("%s, %s" % (obs,exp))
            self.assertEqual(obs,exp)

    def test_best_exons_by_p_value(self):
        expected_output = \
"""Gene Symbol	1_1	1_2	2_1	2_2	3_1	3_2	Mean(Cntl)	Mean(siETV4)	Ratio(siETV4 vs. Cntl)	Fold-Change(siETV4 vs. Cntl)	log2FoldChange	p-value	q-value	Less than 4 exons
A1BG	6.93789333333	7.01143	6.88032666667	6.86134333333	6.9543	6.82708666667	6.92417333333	6.89995333333	0.985846333333	-0.350463333333	-0.02422	0.4211846	0.6866338
A1BG-AS1	6.68543666667	6.36481	6.60468333333	6.50084333333	6.54916	6.57107333333	6.61309333333	6.47891333333	0.912662666667	-1.09929666667	-0.134184444667	0.36233172	0.592774133333	*
"""
        fp_out = io.StringIO()
        best_exons(self.fp_in,fp_out,rank_by='p_value')
        output = fp_out.getvalue()
        for obs,exp in zip(output.split(),expected_output.split()):
            ##print("%s, %s" % (obs,exp))
            self.assertEqual(obs,exp)

class TestTSVLineFunction(unittest.TestCase):
    """Tests for the tsv_line function
    """
    def test_tsv_line(self):
        data = ['one',2,'3']
        self.assertEqual(tsv_line(data),"one\t2\t3")

class TestOrdinalFunction(unittest.TestCase):
    """Tests for the ordinal function
    """
    def test_ordinal(self):
        self.assertEqual('1st',ordinal(1))
        self.assertEqual('2nd',ordinal(2))
        self.assertEqual('3rd',ordinal(3))
        self.assertEqual('4th',ordinal(4))
        self.assertEqual('10th',ordinal(10))
        self.assertEqual('11th',ordinal(11))
        self.assertEqual('12th',ordinal(12))
        self.assertEqual('13th',ordinal(13))
        self.assertEqual('21st',ordinal(21))
        self.assertEqual('22nd',ordinal(22))
        self.assertEqual('23rd',ordinal(23))
