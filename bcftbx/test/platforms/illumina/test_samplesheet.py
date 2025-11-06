#######################################################################
# Tests for illumina.samplesheet.py module
#######################################################################

from bcftbx.platforms.illumina.samplesheet import *
from bcftbx.TabFile import TabDataLine
import unittest
import io
import tempfile
import shutil

class TestSampleSheet(unittest.TestCase):

    def setUp(self):
        self.hiseq_sample_sheet_content = u"""[Header],,,,,,,,,,
IEMFileVersion,4,,,,,,,,,
Date,06/03/2014,,,,,,,,,
Workflow,GenerateFASTQ,,,,,,,,,
Application,HiSeq FASTQ Only,,,,,,,,,
Assay,Nextera,,,,,,,,,
Description,,,,,,,,,,
Chemistry,Amplicon,,,,,,,,,
,,,,,,,,,,
[Reads],,,,,,,,,,
101,,,,,,,,,,
101,,,,,,,,,,
,,,,,,,,,,
[Settings],,,,,,,,,,
ReverseComplement,0,,,,,,,,,
Adapter,CTGTCTCTTATACACATCT,,,,,,,,,
,,,,,,,,,,
[Data],,,,,,,,,,
Lane,Sample_ID,Sample_Name,Sample_Plate,Sample_Well,I7_Index_ID,index,I5_Index_ID,index2,Sample_Project,Description
1,PJB1-1579,PJB1-1579,,,N701,CGATGTAT ,N501,TCTTTCCC,PeterBriggs,
1,PJB2-1580,PJB2-1580,,,N702,TGACCAAT ,N502,TCTTTCCC,PeterBriggs,
"""
        self.miseq_sample_sheet_content = u"""[Header]
IEMFileVersion,4
Date,4/11/2014
Workflow,Metagenomics
Application,Metagenomics 16S rRNA
Assay,Nextera XT
Description,
Chemistry,Amplicon

[Reads]
150
150

[Settings]
Adapter,CTGTCTCTTATACACATCT

[Data]
Sample_ID,Sample_Name,Sample_Plate,Sample_Well,I7_Index_ID,index,I5_Index_ID,index2,Sample_Project,Description
A8,A8,,,N701,TAAGGCGA,S501,TAGATCGC,PJB,
B8,B8,,,N702,CGTACTAG,S501,TAGATCGC,PJB,
"""
        self.casava_sample_sheet_content = u"""FCID,Lane,SampleID,SampleRef,Index,Description,Control,Recipe,Operator,SampleProject
DADA331XX,1,PhiX,PhiX control,,Control,,,Peter,Control
DADA331XX,2,884-1,PB-884-1,AGTCAA,RNA-seq,,,Peter,AR
DADA331XX,3,885-1,PB-885-1,AGTTCC,RNA-seq,,,Peter,AR
DADA331XX,4,886-1,PB-886-1,ATGTCA,RNA-seq,,,Peter,AR
DADA331XX,5,884-1,PB-884-1,AGTCAA,RNA-seq,,,Peter,AR
DADA331XX,6,885-1,PB-885-1,AGTTCC,RNA-seq,,,Peter,AR
DADA331XX,7,886-1,PB-886-1,ATGTCA,RNA-seq,,,Peter,AR
DADA331XX,8,PhiX,PhiX control,,Control,,,Peter,Control
"""
        self.hiseq_sample_sheet_id_and_name_differ_content = u"""[Header],,,,,,,,,,
IEMFileVersion,4,,,,,,,,,
Date,06/03/2014,,,,,,,,,
Workflow,GenerateFASTQ,,,,,,,,,
Application,HiSeq FASTQ Only,,,,,,,,,
Assay,Nextera,,,,,,,,,
Description,,,,,,,,,,
Chemistry,Amplicon,,,,,,,,,
,,,,,,,,,,
[Reads],,,,,,,,,,
101,,,,,,,,,,
101,,,,,,,,,,
,,,,,,,,,,
[Settings],,,,,,,,,,
ReverseComplement,0,,,,,,,,,
Adapter,CTGTCTCTTATACACATCT,,,,,,,,,
,,,,,,,,,,
[Data],,,,,,,,,,
Lane,Sample_ID,Sample_Name,Sample_Plate,Sample_Well,I7_Index_ID,index,I5_Index_ID,index2,Sample_Project,Description
1,PJB1,PJB1-1579,,,N701,CGATGTAT ,N501,TCTTTCCC,PeterBriggs,
1,PJB2,PJB2-1580,,,N702,TGACCAAT ,N502,TCTTTCCC,PeterBriggs,
"""
        self.nextseq_no_index_columns = u"""
[Header]
IEMFileVersion,4
Date,2/7/2017
Workflow,GenerateFASTQ
Application,NextSeq FASTQ Only
Assay,Nextera XT
Description,
Chemistry,Default

[Reads]
26
130

[Settings]
Adapter,CTGTCTCTTATACACATCT

[Data]
Sample_ID,Sample_Name,Sample_Plate,Sample_Well,Sample_Project,Description
PJB1,,,,,
"""
        self.miseq_header_values_have_commas = u"""
[Header]
IEMFileVersion,5
Date,12/12/2017
Workflow,GenerateFASTQ
Application,FASTQ Only
Instrument Type,MiSeq
Assay,Nextera XT
Index Adapters,"Nextera XT Index Kit (96 Indexes, 384 Samples)"
Description,
Chemistry,Amplicon

[Reads]
301
301

[Settings]
ReverseComplement,0
Adapter,CTGTCTCTTATACACATCT

[Data]
Sample_ID,Sample_Name,Sample_Plate,Sample_Well,I7_Index_ID,index,I5_Index_ID,index2,Sample_Project,Description
AO1,AO1,,,N701,TAAGGCGA,S517,GCGTAAGA,Anne Other,
AO2,AO2,,,N701,TAAGGCGA,S502,CTCTCTAT,Anne Other,
"""
        self.hiseq_sample_sheet_with_manifests = u"""[Header]
IEMFileVersion,4
Investigator Name,Peter B
Experiment Name,myexp
Date,1/19/2019
Workflow,GenerateFASTQ
Application,FASTQ Only
Assay,Nextera XT v2 Set A
Description,NGS_test
Chemistry,Amplicon

[Manifests]
A,TruSeqAmpliconManifest-1.txt
B,TruSeqAmpliconManifest-2.txt

[Reads]
151
151

[Settings]
ReverseComplement,0

[Data]
Lane,Sample_ID,Sample_Name,Sample_Plate,Sample_Well,I7_Index_ID,index,I5_Index_ID,index2,Sample_Project,Description,Manifest
1,PJB1-1579,PJB1-1579,,,N701,CGATGTAT ,N501,TCTTTCCC,PeterBriggs,,A
1,PJB2-1580,PJB2-1580,,,N702,TGACCAAT ,N502,TCTTTCCC,PeterBriggs,,B
"""

    def test_samplesheet_load_hiseq_sample_sheet(self):
        """
        SampleSheet: load a HiSEQ IEM-format sample sheet
        """
        iem = SampleSheet(fp=io.StringIO(
            self.hiseq_sample_sheet_content))
        # Check format
        self.assertEqual(iem.format,'IEM')
        # Check header
        self.assertEqual(iem.header_items,['IEMFileVersion',
                                           'Date',
                                           'Workflow',
                                           'Application',
                                           'Assay',
                                           'Description',
                                           'Chemistry'])
        self.assertEqual(iem.header['IEMFileVersion'],'4')
        self.assertEqual(iem.header['Date'],'06/03/2014')
        self.assertEqual(iem.header['Workflow'],'GenerateFASTQ')
        self.assertEqual(iem.header['Application'],'HiSeq FASTQ Only')
        self.assertEqual(iem.header['Assay'],'Nextera')
        self.assertEqual(iem.header['Description'],'')
        self.assertEqual(iem.header['Chemistry'],'Amplicon')
        # Check reads
        self.assertEqual(iem.reads,['101','101'])
        # Check settings
        self.assertEqual(iem.settings_items,['ReverseComplement',
                                              'Adapter'])
        self.assertEqual(iem.settings['ReverseComplement'],'0')
        self.assertEqual(iem.settings['Adapter'],'CTGTCTCTTATACACATCT')
        # Check data
        self.assertEqual(iem.data.header(),['Lane','Sample_ID','Sample_Name',
                                            'Sample_Plate','Sample_Well',
                                            'I7_Index_ID','index',
                                            'I5_Index_ID','index2',
                                            'Sample_Project','Description'])
        self.assertEqual(len(iem.data),2)
        self.assertEqual(iem.data[0]['Lane'],1)
        self.assertEqual(iem.data[0]['Sample_ID'],'PJB1-1579')
        self.assertEqual(iem.data[0]['Sample_Name'],'PJB1-1579')
        self.assertEqual(iem.data[0]['Sample_Plate'],'')
        self.assertEqual(iem.data[0]['Sample_Well'],'')
        self.assertEqual(iem.data[0]['I7_Index_ID'],'N701')
        self.assertEqual(iem.data[0]['index'],'CGATGTAT')
        self.assertEqual(iem.data[0]['I5_Index_ID'],'N501')
        self.assertEqual(iem.data[0]['index2'],'TCTTTCCC')
        self.assertEqual(iem.data[0]['Sample_Project'],'PeterBriggs')
        self.assertEqual(iem.data[0]['Description'],'')

    def test_samplesheet_show_hiseq_sample_sheet(self):
        """
        SampleSheet: reconstruct a HiSEQ sample sheet
        """
        iem = SampleSheet(fp=io.StringIO(
            self.hiseq_sample_sheet_content))
        expected = u"""[Header]
IEMFileVersion,4
Date,06/03/2014
Workflow,GenerateFASTQ
Application,HiSeq FASTQ Only
Assay,Nextera
Description,
Chemistry,Amplicon

[Reads]
101
101

[Settings]
ReverseComplement,0
Adapter,CTGTCTCTTATACACATCT

[Data]
Lane,Sample_ID,Sample_Name,Sample_Plate,Sample_Well,I7_Index_ID,index,I5_Index_ID,index2,Sample_Project,Description
1,PJB1-1579,PJB1-1579,,,N701,CGATGTAT,N501,TCTTTCCC,PeterBriggs,
1,PJB2-1580,PJB2-1580,,,N702,TGACCAAT,N502,TCTTTCCC,PeterBriggs,
"""
        for l1,l2 in zip(iem.show().split(),expected.split()):
            self.assertEqual(l1,l2)

    def test_samplesheet_convert_hiseq_sample_sheet_to_casava(self):
        """
        SampleSheet: convert HISeq IEM4 sample sheet to CASAVA format
        """
        iem = SampleSheet(fp=io.StringIO(
            self.hiseq_sample_sheet_content))
        expected = """FCID,Lane,SampleID,SampleRef,Index,Description,Control,Recipe,Operator,SampleProject
FC0001,1,PJB1-1579,,CGATGTAT-TCTTTCCC,,,,,PeterBriggs
FC0001,1,PJB2-1580,,TGACCAAT-TCTTTCCC,,,,,PeterBriggs
"""
        for l1,l2 in zip(iem.show(fmt='CASAVA').split(),expected.split()):
            self.assertEqual(l1,l2)

    def test_samplesheet_hiseq_predict_output(self):
        """
        SampleSheet: check predicted outputs for HISeq IEM4 sample sheet
        """
        iem = SampleSheet(fp=io.StringIO(
            self.hiseq_sample_sheet_content))
        output = iem.predict_output()
        self.assertTrue('Project_PeterBriggs' in output)
        self.assertTrue('Sample_PJB1-1579' in output['Project_PeterBriggs'])
        self.assertTrue('Sample_PJB2-1580' in output['Project_PeterBriggs'])
        self.assertEqual(output['Project_PeterBriggs']['Sample_PJB1-1579'],
                         ['PJB1-1579_CGATGTAT-TCTTTCCC_L001',])
        self.assertEqual(output['Project_PeterBriggs']['Sample_PJB2-1580'],
                         ['PJB2-1580_TGACCAAT-TCTTTCCC_L001',])

    def test_samplesheet_hiseq_predict_output_bcl2fastq2(self):
        """
        SampleSheet: check predicted bcl2fastq2 outputs for HISeq IEM4 sample sheet
        """
        iem = SampleSheet(fp=io.StringIO(
            self.hiseq_sample_sheet_content))
        output = iem.predict_output(fmt='bcl2fastq2')
        self.assertTrue('PeterBriggs' in output)
        self.assertEqual(output['PeterBriggs'],
                         ['PJB1-1579_S1_L001','PJB2-1580_S2_L001',])

    def test_samplesheet_load_miseq_sample_sheet(self):
        """
        SampleSheet: load a MiSEQ sample sheet
        """
        iem = SampleSheet(fp=io.StringIO(
            self.miseq_sample_sheet_content))
        # Check format
        self.assertEqual(iem.format,'IEM')
        # Check header
        self.assertEqual(iem.header_items,['IEMFileVersion',
                                           'Date',
                                           'Workflow',
                                           'Application',
                                           'Assay',
                                           'Description',
                                           'Chemistry'])
        self.assertEqual(iem.header['IEMFileVersion'],'4')
        self.assertEqual(iem.header['Date'],'4/11/2014')
        self.assertEqual(iem.header['Workflow'],'Metagenomics')
        self.assertEqual(iem.header['Application'],'Metagenomics 16S rRNA')
        self.assertEqual(iem.header['Assay'],'Nextera XT')
        self.assertEqual(iem.header['Description'],'')
        self.assertEqual(iem.header['Chemistry'],'Amplicon')
        # Check reads
        self.assertEqual(iem.reads,['150','150'])
        # Check settings
        self.assertEqual(iem.settings_items,['Adapter'])
        self.assertEqual(iem.settings['Adapter'],'CTGTCTCTTATACACATCT')
        # Check data
        self.assertEqual(iem.data.header(),['Sample_ID','Sample_Name',
                                            'Sample_Plate','Sample_Well',
                                            'I7_Index_ID','index',
                                            'I5_Index_ID','index2',
                                            'Sample_Project','Description'])
        self.assertEqual(len(iem.data),2)
        self.assertEqual(iem.data[0]['Sample_ID'],'A8')
        self.assertEqual(iem.data[0]['Sample_Name'],'A8')
        self.assertEqual(iem.data[0]['Sample_Plate'],'')
        self.assertEqual(iem.data[0]['Sample_Well'],'')
        self.assertEqual(iem.data[0]['I7_Index_ID'],'N701')
        self.assertEqual(iem.data[0]['index'],'TAAGGCGA')
        self.assertEqual(iem.data[0]['I5_Index_ID'],'S501')
        self.assertEqual(iem.data[0]['index2'],'TAGATCGC')
        self.assertEqual(iem.data[0]['Sample_Project'],'PJB')
        self.assertEqual(iem.data[0]['Description'],'')

    def test_samplesheet_show_miseq_sample_sheet(self):
        """
        SampleSheet: reconstruct a MiSEQ sample sheet
        """
        iem = SampleSheet(fp=io.StringIO(
            self.miseq_sample_sheet_content))
        expected = self.miseq_sample_sheet_content
        for l1,l2 in zip(iem.show().split(),expected.split()):
            self.assertEqual(l1,l2)

    def test_convert_miseq_sample_sheet_to_casava(self):
        """
        SampleSheet: convert MISeq IEM4 sample sheet to CASAVA format
        """
        iem = SampleSheet(fp=io.StringIO(
            self.miseq_sample_sheet_content))
        expected = u"""FCID,Lane,SampleID,SampleRef,Index,Description,Control,Recipe,Operator,SampleProject
FC0001,1,A8,,TAAGGCGA-TAGATCGC,,,,,PJB
FC0001,1,B8,,CGTACTAG-TAGATCGC,,,,,PJB
"""
        for l1,l2 in zip(iem.show(fmt='CASAVA').split(),expected.split()):
            self.assertEqual(l1,l2)

    def test_samplesheet_miseq_predict_output(self):
        """
        SampleSheet: check predicted outputs for MISeq IEM4 sample sheet
        """
        iem = SampleSheet(fp=io.StringIO(
            self.miseq_sample_sheet_content))
        output = iem.predict_output()
        self.assertTrue('Project_PJB' in output)
        self.assertTrue('Sample_A8' in output['Project_PJB'])
        self.assertTrue('Sample_B8' in output['Project_PJB'])
        self.assertEqual(output['Project_PJB']['Sample_A8'],
                         ['A8_TAAGGCGA-TAGATCGC_L001',])
        self.assertEqual(output['Project_PJB']['Sample_B8'],
                         ['B8_CGTACTAG-TAGATCGC_L001',])

    def test_samplesheet_miseq_predict_output_bcl2fastq2(self):
        """
        SampleSheet: check predicted bcl2fastq2 outputs for MISeq IEM4  sample sheet
        """
        iem = SampleSheet(fp=io.StringIO(
            self.miseq_sample_sheet_content))
        output = iem.predict_output(fmt='bcl2fastq2')
        self.assertTrue('PJB' in output)
        self.assertEqual(output['PJB'],
                         ['A8_S1','B8_S2',])

    def test_samplesheet_load_casava_sample_sheet(self):
        """
        SampleSheet: load a CASAVA-style sample sheet
        """
        casava = SampleSheet(fp=io.StringIO(
            self.casava_sample_sheet_content))
        # Check format
        self.assertEqual(casava.format,'CASAVA')
        # Check header
        self.assertEqual(casava.header_items,[])
        # Check reads
        self.assertEqual(casava.reads,[])
        # Check settings
        self.assertEqual(casava.settings_items,[])
        # Check data
        self.assertEqual(casava.data.header(),['FCID','Lane',
                                               'SampleID','SampleRef',
                                               'Index','Description',
                                               'Control','Recipe',
                                               'Operator','SampleProject'])
        self.assertEqual(len(casava.data),8)
        self.assertEqual(casava.data[0]['FCID'],'DADA331XX')
        self.assertEqual(casava.data[0]['Lane'],1)
        self.assertEqual(casava.data[0]['SampleID'],'PhiX')
        self.assertEqual(casava.data[0]['SampleRef'],'PhiX control')
        self.assertEqual(casava.data[0]['Index'],'')
        self.assertEqual(casava.data[0]['Description'],'Control')
        self.assertEqual(casava.data[0]['Control'],'')
        self.assertEqual(casava.data[0]['Recipe'],'')
        self.assertEqual(casava.data[0]['Operator'],'Peter')
        self.assertEqual(casava.data[0]['SampleProject'],'Control')
        self.assertEqual(casava.data[1]['FCID'],'DADA331XX')
        self.assertEqual(casava.data[1]['Lane'],2)
        self.assertEqual(casava.data[1]['SampleID'],'884-1')
        self.assertEqual(casava.data[1]['SampleRef'],'PB-884-1')
        self.assertEqual(casava.data[1]['Index'],'AGTCAA')
        self.assertEqual(casava.data[1]['Description'],'RNA-seq')
        self.assertEqual(casava.data[1]['Control'],'')
        self.assertEqual(casava.data[1]['Recipe'],'')
        self.assertEqual(casava.data[1]['Operator'],'Peter')
        self.assertEqual(casava.data[1]['SampleProject'],'AR')

    def test_samplesheet_show_casava_sample_sheet(self):
        """
        SampleSheet: reconstruct a CASAVA sample sheet
        """
        casava = SampleSheet(fp=io.StringIO(
            self.casava_sample_sheet_content))
        expected = self.casava_sample_sheet_content
        for l1,l2 in zip(casava.show().split(),expected.split()):
            self.assertEqual(l1,l2)

    def test_samplesheet_casava_predict_output(self):
        """
        SampleSheet: check predicted outputs for CASAVA sample sheet
        """
        casava = SampleSheet(fp=io.StringIO(
            self.casava_sample_sheet_content))
        output = casava.predict_output()
        self.assertTrue('Project_Control' in output)
        self.assertTrue('Sample_PhiX' in output['Project_Control'])
        self.assertEqual(output['Project_Control']['Sample_PhiX'],
                         ['PhiX_NoIndex_L001',
                          'PhiX_NoIndex_L008'])
        self.assertTrue('Project_AR' in output)
        self.assertTrue('Sample_884-1' in output['Project_AR'])
        self.assertTrue('Sample_885-1' in output['Project_AR'])
        self.assertTrue('Sample_886-1' in output['Project_AR'])
        self.assertEqual(output['Project_AR']['Sample_884-1'],
                         ['884-1_AGTCAA_L002',
                          '884-1_AGTCAA_L005'])
        self.assertEqual(output['Project_AR']['Sample_885-1'],
                         ['885-1_AGTTCC_L003',
                          '885-1_AGTTCC_L006'])
        self.assertEqual(output['Project_AR']['Sample_886-1'],
                         ['886-1_ATGTCA_L004',
                          '886-1_ATGTCA_L007'])

    def test_samplesheet_hiseq_predict_output_bcl2fastq2_id_and_names_differ(
            self):
        """
        SampleSheet: check predicted bcl2fastq2 outputs for HISeq IEM4 sample sheet when id and names differ
        """
        iem = SampleSheet(fp=io.StringIO(
            self.hiseq_sample_sheet_id_and_name_differ_content))
        output = iem.predict_output(fmt='bcl2fastq2')
        self.assertTrue('PeterBriggs' in output)
        self.assertEqual(output['PeterBriggs'],
                         ['PJB1/PJB1-1579_S1_L001','PJB2/PJB2-1580_S2_L001',])
    def test_len(self):
        """SampleSheet: test __len__ built-in

        """
        empty = SampleSheet()
        self.assertEqual(len(empty),0)
        hiseq = SampleSheet(fp=io.StringIO(
            self.hiseq_sample_sheet_content))
        self.assertEqual(len(hiseq),2)
        casava = SampleSheet(fp=io.StringIO(
            self.casava_sample_sheet_content))
        self.assertEqual(len(casava),8)

    def test_samplesheet_iter(self):
        """
        SampleSheet: test __iter__ built-in
        """
        hiseq = SampleSheet(fp=io.StringIO(
            self.hiseq_sample_sheet_content))
        for line0,line1 in zip(hiseq,hiseq.data):
            self.assertEqual(line0,line1)
        casava = SampleSheet(fp=io.StringIO(
            self.casava_sample_sheet_content))
        for line0,line1 in zip(casava,casava.data):
            self.assertEqual(line0,line1)

    def test_samplesheet_getitem(self):
        """
        SampleSheet: test __getitem__ built-in
        """
        hiseq = SampleSheet(fp=io.StringIO(
            self.hiseq_sample_sheet_content))
        self.assertEqual(hiseq[0],hiseq.data[0])
        self.assertEqual(hiseq[1],hiseq.data[1])
        casava = SampleSheet(fp=io.StringIO(
            self.casava_sample_sheet_content))
        self.assertEqual(casava[0],casava.data[0])
        self.assertEqual(casava[2],casava.data[2])
        self.assertEqual(casava[7],casava.data[7])

    def test_samplesheet_setitem(self):
        """
        SampleSheet: test __setitem__ built-in
        """
        hiseq = SampleSheet(fp=io.StringIO(
            self.hiseq_sample_sheet_content))
        hiseq[0]['Sample_ID'] = 'NewSample1'
        self.assertEqual(hiseq[0]['Sample_ID'],'NewSample1')
        casava = SampleSheet(fp=io.StringIO(
            self.casava_sample_sheet_content))
        casava[0]['SampleID'] = 'NewSample2'
        self.assertEqual(casava[0]['SampleID'],'NewSample2')

    def test_samplesheet_append(self):
        """
        SampleSheet: test append method
        """
        hiseq = SampleSheet(fp=io.StringIO(
            self.hiseq_sample_sheet_content))
        self.assertEqual(len(hiseq),2)
        new_line = hiseq.append()
        self.assertEqual(len(hiseq),3)

    def test_samplesheet_write_iem(self):
        """
        SampleSheet: write out IEM formatted sample sheet
        """
        miseq = SampleSheet(fp=io.StringIO(
            self.miseq_sample_sheet_content))
        fp=io.StringIO()
        miseq.write(fp=fp)
        self.assertEqual(fp.getvalue(),self.miseq_sample_sheet_content)

    def test_samplesheet_write_casava(self):
        """
        SampleSheet: write out CASAVA formatted sample sheet
        """
        casava = SampleSheet(fp=io.StringIO(
            self.casava_sample_sheet_content))
        fp=io.StringIO()
        casava.write(fp=fp)
        self.assertEqual(fp.getvalue(),self.casava_sample_sheet_content)

    def test_samplesheet_bad_input_unrecognised_section(self):
        """
        SampleSheet: raises exception for input with unrecognised section
        """
        fp = io.StringIO(u"""[Header]
IEMFileVersion,4
Date,06/03/2014

[Footer]
This,isTheEnd
""")
        self.assertRaises(IlluminaError, SampleSheet, fp=fp)

    def test_samplesheet_bad_input_not_sample_sheet(self):
        """
        SampleSheet: raises exception for non-IEM formatted input
        """
        fp = io.StringIO(u"""Something random
IEMFileVersion,4
Date,06/03/2014

[Footer]
This,isTheEnd
""")
        self.assertRaises(IlluminaError, SampleSheet, fp=fp)

    def test_samplesheet_duplicates_in_iem_format(self):
        """
        SampleSheet: check & fix duplicated names in IEM sample sheet
        """
        # Set up
        iem = SampleSheet(fp=io.StringIO(
            self.hiseq_sample_sheet_content))
        # Shouldn't find any duplicates when lanes are different
        self.assertEqual(len(iem.duplicated_names),0)
        # Create 3 duplicates by resetting lane numbers
        iem.data[1]['Sample_ID'] = iem.data[0]['Sample_ID']
        iem.data[1]['Sample_Name'] = iem.data[0]['Sample_Name']
        iem.data[1]['index'] = iem.data[0]['index']
        iem.data[1]['index2'] = iem.data[0]['index2']
        iem.data[1]['Sample_Project'] = iem.data[0]['Sample_Project']
        self.assertEqual(len(iem.duplicated_names),1)
        # Fix and check again (should be none)
        iem.fix_duplicated_names()
        self.assertEqual(iem.duplicated_names,[])

    def test_samplesheet_duplicates_in_iem_format_no_lanes(self):
        """
        SampleSheet: check & fix duplicated names in IEM sample sheet (no lanes)
        """
        # Set up
        iem = SampleSheet(fp=io.StringIO(
            self.miseq_sample_sheet_content))
        # Shouldn't find any duplicates when lanes are different
        self.assertEqual(len(iem.duplicated_names),0)
        # Create duplicates by resetting sample names and projects
        iem.data[1]['Sample_ID'] = iem.data[0]['Sample_ID']
        iem.data[1]['Sample_Name'] = iem.data[0]['Sample_Name']
        iem.data[1]['index'] = iem.data[0]['index']
        iem.data[1]['index2'] = iem.data[0]['index2']
        iem.data[1]['Sample_Project'] = iem.data[0]['Sample_Project']
        self.assertEqual(len(iem.duplicated_names),1)
        # Fix and check again (should be none)
        iem.fix_duplicated_names()
        self.assertEqual(iem.duplicated_names,[])

    def test_samplesheet_duplicates_in_iem_format_no_index_columns(self):
        """
        SampleSheet: check duplicated names in IEM sample sheet (no index cols)
        """
        # Set up
        iem = SampleSheet(fp=io.StringIO(
            self.nextseq_no_index_columns))
        # Shouldn't find any duplicates
        self.assertEqual(len(iem.duplicated_names),0)
        # Fix and check again (should have no change)
        iem.fix_duplicated_names()
        self.assertEqual(len(iem.duplicated_names),0)

    def test_samplesheet_illegal_names_in_iem_format(self):
        """
        SampleSheet: check for illegal characters in IEM sample sheet
        """
        # Set up and introduce bad names
        iem = SampleSheet(fp=io.StringIO(
            self.hiseq_sample_sheet_content))
        iem.data[0]['Sample_ID'] = 'PJB1 1579'
        iem.data[0]['Sample_Name'] = 'PJB1 1579'
        iem.data[1]['Sample_Project'] = "PeterBriggs?"
        # Check for illegal names
        self.assertEqual(len(iem.illegal_names),2)
        # Fix and check again
        iem.fix_illegal_names()
        self.assertEqual(iem.illegal_names,[])
        # Verify that character replacement worked correctly
        self.assertEqual(iem.data[0]['Sample_ID'],'PJB1_1579')
        self.assertEqual(iem.data[0]['Sample_Name'],'PJB1_1579')
        self.assertEqual(iem.data[1]['Sample_Project'],"PeterBriggs")

    def test_samplesheet_empty_names_in_iem_format(self):
        """
        SampleSheet: check for empty sample/project names in IEM sample sheet
        """
        # Set up and introduce bad names
        iem = SampleSheet(fp=io.StringIO(
            self.hiseq_sample_sheet_content))
        iem.data[0]['Sample_ID'] = ''
        iem.data[1]['Sample_Project'] = ''
        # Check for empty names
        self.assertEqual(len(iem.empty_names),2)

    def test_samplesheet_duplicates_in_casava_format(self):
        """
        SampleSheet: check and fix duplicated names in CASAVA sample sheet
        """
        # Set up
        casava = SampleSheet(fp=io.StringIO(
            self.casava_sample_sheet_content))
        # Shouldn't find any duplicates when lanes are different
        self.assertEqual(len(casava.duplicated_names),0)
        # Create 3 duplicates by resetting lane numbers
        casava.data[4]['Lane'] = 2
        casava.data[5]['Lane'] = 3
        casava.data[6]['Lane'] = 4
        self.assertEqual(len(casava.duplicated_names),3)
        # Fix and check again (should be none)
        casava.fix_duplicated_names()
        self.assertEqual(casava.duplicated_names,[])

    def test_samplesheet_illegal_names_in_casava_format(self):
        """
        SampleSheet: check for illegal characters in CASAVA sample sheet
        """
        # Set up and introduce bad names
        casava = SampleSheet(fp=io.StringIO(
            self.casava_sample_sheet_content))
        casava.data[3]['SampleID'] = '886 1'
        casava.data[4]['SampleProject'] = "AR?"
        # Check for illegal names
        self.assertEqual(len(casava.illegal_names),2)
        # Fix and check again
        casava.fix_illegal_names()
        self.assertEqual(casava.illegal_names,[])
        # Verify that character replacement worked correctly
        self.assertEqual(casava.data[3]['SampleID'],'886_1')
        self.assertEqual(casava.data[4]['SampleProject'],"AR")

    def test_samplesheet_empty_names_in_casava_format(self):
        """
        SampleSheet: check for empty sample/project names in CASAVA sample sheet
        """
        # Set up and introduce bad names
        casava = SampleSheet(fp=io.StringIO(
            self.casava_sample_sheet_content))
        casava.data[3]['SampleID'] = ''
        casava.data[4]['SampleProject'] = ""
        # Check for illegal names
        self.assertEqual(len(casava.empty_names),2)

    def test_samplesheet_with_missing_data_section(self):
        """
        SampleSheet: handle IEM sample sheet with missing 'Data' section
        """
        contents = u"""[Header]
IEMFileVersion,4
Date,06/03/2014
Workflow,GenerateFASTQ
Application,HiSeq FASTQ Only
Assay,Nextera
Description,
Chemistry,Amplicon

[Reads]
101
101

[Settings]
ReverseComplement,0
Adapter,CTGTCTCTTATACACATCT
"""
        iem = SampleSheet(fp=io.StringIO(contents))
        for l1,l2 in zip(iem.show().split(),contents.split()):
            self.assertEqual(l1,l2)
        self.assertEqual(iem.column_names,[])
        self.assertEqual(iem.duplicated_names,[])
        self.assertEqual(iem.illegal_names,[])
        self.assertEqual(iem.empty_names,[])
        self.assertFalse(iem.has_lanes)

    def test_samplesheet_with_commas_and_quotes_in_header_section(self):
        """
        SampleSheet: handle IEM sample sheet with double quotes and comma in 'Header' section
        """
        iem = SampleSheet(fp=io.StringIO(self.miseq_header_values_have_commas))
        self.assertEqual(iem.header['IEMFileVersion'],"5")
        self.assertEqual(iem.header['Date'],"12/12/2017")
        self.assertEqual(iem.header['Workflow'],"GenerateFASTQ")
        self.assertEqual(iem.header['Application'],"FASTQ Only")
        self.assertEqual(iem.header['Instrument Type'],"MiSeq")
        self.assertEqual(iem.header['Assay'],"Nextera XT")
        self.assertEqual(iem.header['Index Adapters'],
                         "\"Nextera XT Index Kit (96 Indexes, 384 Samples)\"")
        self.assertEqual(iem.header['Description'],"")
        self.assertEqual(iem.header['Chemistry'],"Amplicon")

    def test_samplesheet_load_hiseq_sample_sheet_with_manifests(self):
        """
        SampleSheet: load a HiSEQ IEM-format sample sheet with 'Manifests' section
        """
        iem = SampleSheet(fp=io.StringIO(
            self.hiseq_sample_sheet_with_manifests))
        # Check format
        self.assertEqual(iem.format,'IEM')
        # Check header
        self.assertEqual(iem.header_items,['IEMFileVersion',
                                           'Investigator Name',
                                           'Experiment Name',
                                           'Date',
                                           'Workflow',
                                           'Application',
                                           'Assay',
                                           'Description',
                                           'Chemistry'])
        self.assertEqual(iem.header['IEMFileVersion'],'4')
        self.assertEqual(iem.header['Investigator Name'],'Peter B')
        self.assertEqual(iem.header['Experiment Name'],'myexp')
        self.assertEqual(iem.header['Date'],'1/19/2019')
        self.assertEqual(iem.header['Workflow'],'GenerateFASTQ')
        self.assertEqual(iem.header['Application'],'FASTQ Only')
        self.assertEqual(iem.header['Assay'],'Nextera XT v2 Set A')
        self.assertEqual(iem.header['Description'],'NGS_test')
        self.assertEqual(iem.header['Chemistry'],'Amplicon')
        # Check manifests
        self.assertEqual(iem.manifests_items,['A','B'])
        self.assertEqual(iem.manifests['A'],'TruSeqAmpliconManifest-1.txt')
        self.assertEqual(iem.manifests['B'],'TruSeqAmpliconManifest-2.txt')
        # Check reads
        self.assertEqual(iem.reads,['151','151'])
        # Check settings
        self.assertEqual(iem.settings_items,['ReverseComplement',])
        self.assertEqual(iem.settings['ReverseComplement'],'0')
        # Check data
        self.assertEqual(iem.data.header(),['Lane','Sample_ID','Sample_Name',
                                            'Sample_Plate','Sample_Well',
                                            'I7_Index_ID','index',
                                            'I5_Index_ID','index2',
                                            'Sample_Project','Description',
                                            'Manifest'])
        self.assertEqual(len(iem.data),2)
        self.assertEqual(iem.data[0]['Lane'],1)
        self.assertEqual(iem.data[0]['Sample_ID'],'PJB1-1579')
        self.assertEqual(iem.data[0]['Sample_Name'],'PJB1-1579')
        self.assertEqual(iem.data[0]['Sample_Plate'],'')
        self.assertEqual(iem.data[0]['Sample_Well'],'')
        self.assertEqual(iem.data[0]['I7_Index_ID'],'N701')
        self.assertEqual(iem.data[0]['index'],'CGATGTAT')
        self.assertEqual(iem.data[0]['I5_Index_ID'],'N501')
        self.assertEqual(iem.data[0]['index2'],'TCTTTCCC')
        self.assertEqual(iem.data[0]['Sample_Project'],'PeterBriggs')
        self.assertEqual(iem.data[0]['Description'],'')
        self.assertEqual(iem.data[0]['Manifest'],'A')

    def test_samplesheet_with_missing_values_in_header(self):
        """
        SampleSheet: handle IEM sample sheet with 'missing' values in header
        """
        contents = u"""[Header]
IEMFileVersion,4
Date,11/16/2015
Workflow,GenerateFASTQ
Application,RNA-Seq
Assay,TruSeq LT
Description
Chemistry,Default

[Reads]
150
150

[Settings]
Adapter,CTGTCTCTTATACACATCT

[Data]
Sample_ID,Sample_Name,Sample_Plate,Sample_Well,I7_Index_ID,index,I5_Index_ID,index2,Sample_Project,Description
A8,A8,,,N701,TAAGGCGA,S501,TAGATCGC,PJB,
B8,B8,,,N702,CGTACTAG,S501,TAGATCGC,PJB,
"""
        iem = SampleSheet(fp=io.StringIO(contents))
        # Check format
        self.assertEqual(iem.format,'IEM')
        # Check header
        self.assertEqual(iem.header_items,['IEMFileVersion',
                                           'Date',
                                           'Workflow',
                                           'Application',
                                           'Assay',
                                           'Description',
                                           'Chemistry'])
        self.assertEqual(iem.header['IEMFileVersion'],'4')
        self.assertEqual(iem.header['Date'],'11/16/2015')
        self.assertEqual(iem.header['Workflow'],'GenerateFASTQ')
        self.assertEqual(iem.header['Application'],'RNA-Seq')
        self.assertEqual(iem.header['Assay'],'TruSeq LT')
        self.assertEqual(iem.header['Description'],'')
        self.assertEqual(iem.header['Chemistry'],'Default')

class TestSampleSheetPredictor(unittest.TestCase):

    def setUp(self):
        self.hiseq_sample_sheet_content = u"""[Header]
IEMFileVersion,4
Date,06/03/2014
Workflow,GenerateFASTQ
Application,HiSeq FASTQ Only
Assay,Nextera
Description,
Chemistry,Amplicon

[Reads]
101
101

[Settings]
ReverseComplement,0
Adapter,CTGTCTCTTATACACATCT

[Data]
Lane,Sample_ID,Sample_Name,Sample_Plate,Sample_Well,I7_Index_ID,index,I5_Index_ID,index2,Sample_Project,Description
1,PJB1-1579,PJB1-1579,,,N701,CGATGTAT,N501,TCTTTCCC,PeterBriggs,
1,PJB2-1580,PJB2-1580,,,N702,TGACCAAT,N502,TCTTTCCC,PeterBriggs,
2,PJB1-1579,PJB1-1579,,,N701,CGATGTAT,N501,TCTTTCCC,PeterBriggs,
2,PJB2-1580,PJB2-1580,,,N702,TGACCAAT,N502,TCTTTCCC,PeterBriggs,
"""
        self.miseq_sample_sheet_content = u"""[Header]
IEMFileVersion,4
Date,4/11/2014
Workflow,Metagenomics
Application,Metagenomics 16S rRNA
Assay,Nextera XT
Description,
Chemistry,Amplicon

[Reads]
150
150

[Settings]
Adapter,CTGTCTCTTATACACATCT

[Data]
Sample_ID,Sample_Name,Sample_Plate,Sample_Well,I7_Index_ID,index,I5_Index_ID,index2,Sample_Project,Description
A8,A8,,,N701,TAAGGCGA,S501,TAGATCGC,PJB,
B8,B8,,,N702,CGTACTAG,S501,TAGATCGC,PJB,
"""
        self.casava_sample_sheet_content = u"""FCID,Lane,SampleID,SampleRef,Index,Description,Control,Recipe,Operator,SampleProject
DADA331XX,1,PhiX,PhiX control,CTGCCT,Control,,,Peter,Control
DADA331XX,2,884-1,PB-884-1,AGTCAA,RNA-seq,,,Peter,AR
DADA331XX,3,885-1,PB-885-1,AGTTCC,RNA-seq,,,Peter,AR
DADA331XX,4,886-1,PB-886-1,ATGTCA,RNA-seq,,,Peter,AR
DADA331XX,5,884-1,PB-884-1,AGTCAA,RNA-seq,,,Peter,AR
DADA331XX,6,885-1,PB-885-1,AGTTCC,RNA-seq,,,Peter,AR
DADA331XX,7,886-1,PB-886-1,ATGTCA,RNA-seq,,,Peter,AR
DADA331XX,8,PhiX,PhiX control,CTGCCT,Control,,,Peter,Control
"""
        self.hiseq_sample_sheet_id_and_name_differ_content = u"""[Header]
IEMFileVersion,4
Date,06/03/2014
Workflow,GenerateFASTQ
Application,HiSeq FASTQ Only
Assay,Nextera
Description,
Chemistry,Amplicon

[Reads]
101
101

[Settings]
ReverseComplement,0
Adapter,CTGTCTCTTATACACATCT

[Data]
Lane,Sample_ID,Sample_Name,Sample_Plate,Sample_Well,I7_Index_ID,index,I5_Index_ID,index2,Sample_Project,Description
1,PJB1,PJB1-1579,,,N701,CGATGTAT,N501,TCTTTCCC,PeterBriggs,
1,PJB2,PJB2-1580,,,N702,TGACCAAT,N502,TCTTTCCC,PeterBriggs,
2,PJB1,PJB1-1579,,,N701,CGATGTAT,N501,TCTTTCCC,PeterBriggs,
2,PJB2,PJB2-1580,,,N702,TGACCAAT,N502,TCTTTCCC,PeterBriggs,
"""
        self.hiseq_sample_sheet_name_no_id_content = u"""[Header]
IEMFileVersion,4
Date,06/03/2014
Workflow,GenerateFASTQ
Application,HiSeq FASTQ Only
Assay,Nextera
Description,
Chemistry,Amplicon

[Reads]
101
101

[Settings]
ReverseComplement,0
Adapter,CTGTCTCTTATACACATCT

[Data]
Lane,Sample_ID,Sample_Name,Sample_Plate,Sample_Well,I7_Index_ID,index,I5_Index_ID,index2,Sample_Project,Description
1,,PJB1-1579,,,N701,CGATGTAT,N501,TCTTTCCC,PeterBriggs,
1,,PJB2-1580,,,N702,TGACCAAT,N502,TCTTTCCC,PeterBriggs,
2,,PJB1-1579,,,N701,CGATGTAT,N501,TCTTTCCC,PeterBriggs,
2,,PJB2-1580,,,N702,TGACCAAT,N502,TCTTTCCC,PeterBriggs,
"""
        self.hiseq_sample_sheet_no_barcodes = u"""[Header]
IEMFileVersion,4
Date,06/03/2014
Workflow,GenerateFASTQ
Application,HiSeq FASTQ Only
Assay,Nextera
Description,
Chemistry,Amplicon

[Reads]
101
101

[Settings]
ReverseComplement,0
Adapter,CTGTCTCTTATACACATCT

[Data]
Lane,Sample_ID,Sample_Name,Sample_Plate,Sample_Well,I7_Index_ID,index,I5_Index_ID,index2,Sample_Project,Description
1,PJB1,PJB1,,,,,,,PeterBriggs,
2,PJB2,PJB2,,,,,,,PeterBriggs,
"""
        self.hiseq_sample_sheet_lanes_out_of_order = u"""[Header]
IEMFileVersion,4
Date,06/03/2014
Workflow,GenerateFASTQ
Application,HiSeq FASTQ Only
Assay,Nextera
Description,
Chemistry,Amplicon

[Reads]
101
101

[Settings]
ReverseComplement,0
Adapter,CTGTCTCTTATACACATCT

[Data]
Lane,Sample_ID,Sample_Name,Sample_Plate,Sample_Well,I7_Index_ID,index,I5_Index_ID,index2,Sample_Project,Description
2,AB1,AB1,,,N701,CGATGTAT,N501,TCTTTCCC,AlanBarclay,
2,AB2,AB2,,,N702,TGACCAAT,N502,TCTTTCCC,AlanBarclay,
1,CD3,CD3,,,N701,GTATCGAT,N501,TCTTTCCC,CarlDavis,
1,CD4,CD4,,,N702,CAATTGAC,N502,TCTTTCCC,CarlDavis,
"""
        self.hiseq_sample_sheet_no_barcodes = u"""[Header]
IEMFileVersion,4
Date,06/03/2014
Workflow,GenerateFASTQ
Application,HiSeq FASTQ Only
Assay,Nextera
Description,
Chemistry,Amplicon

[Reads]
101
101

[Settings]
ReverseComplement,0
Adapter,CTGTCTCTTATACACATCT

[Data]
Lane,Sample_ID,Sample_Name,Sample_Plate,Sample_Well,I7_Index_ID,index,I5_Index_ID,index2,Sample_Project,Description
1,PJB1,PJB1,,,,,,,PeterBriggs,
2,PJB2,PJB2,,,,,,,PeterBriggs,
"""
        self.miseq_sample_sheet_no_projects = u"""[Header]
IEMFileVersion,4
Date,11/23/2015
Workflow,GenerateFASTQ
Application,FASTQ Only
Assay,TruSeq HT
Description,
Chemistry,Amplicon

[Reads]
101
101

[Settings]
ReverseComplement,0
Adapter,AGATCGGAAGAGCACACGTCTGAACTCCAGTCA
AdapterRead2,AGATCGGAAGAGCGTCGTGTAGGGAAAGAGTGT

[Data]
Sample_ID,Sample_Name,Sample_Plate,Sample_Well,I7_Index_ID,index,I5_Index_ID,index2,Sample_Project,Description
Sample1,Sample1,,,D701,CGTGTAGG,D501,GACCTGTA,,
Sample2,Sample2,,,D702,CGTGTAGG,D501,ATGTAACT,,
"""

    def test_samplesheet_predictor_iem_with_lanes(self):
        """
        SampleSheetPredictor: handle IEM4 sample sheet with lanes
        """
        iem = SampleSheet(fp=io.StringIO(
            self.hiseq_sample_sheet_content))
        predictor = SampleSheetPredictor(sample_sheet=iem)
        # Get projects
        self.assertEqual(predictor.nprojects,1)
        self.assertEqual(predictor.project_names,["PeterBriggs"])
        project = predictor.get_project("PeterBriggs")
        self.assertRaises(KeyError,predictor.get_project,"DoesntExist")
        # Get samples
        self.assertEqual(project.sample_ids,["PJB1-1579","PJB2-1580"])
        sample1 = project.get_sample("PJB1-1579")
        sample2 = project.get_sample("PJB2-1580")
        self.assertRaises(KeyError,project.get_sample,"DoesntExist")
        # Check sample barcodes and lanes
        self.assertEqual(sample1.barcode_seqs,["CGATGTAT-TCTTTCCC"])
        self.assertEqual(sample2.barcode_seqs,["TGACCAAT-TCTTTCCC"])
        self.assertEqual(sample1.lanes("CGATGTAT-TCTTTCCC"),[1,2])
        self.assertEqual(sample2.lanes("TGACCAAT-TCTTTCCC"),[1,2])
        self.assertEqual(sample1.s_index,1)
        self.assertEqual(sample2.s_index,2)
        # Predict output fastqs bcl2fastq2
        predictor.set(package="bcl2fastq2")
        self.assertEqual(project.dir_name,"PeterBriggs")
        self.assertEqual(sample1.dir_name,None)
        self.assertEqual(sample1.fastqs(),
                         ["PJB1-1579_S1_L001_R1_001.fastq.gz",
                          "PJB1-1579_S1_L002_R1_001.fastq.gz"])
        self.assertEqual(sample2.dir_name,None)
        self.assertEqual(sample2.fastqs(),
                         ["PJB2-1580_S2_L001_R1_001.fastq.gz",
                          "PJB2-1580_S2_L002_R1_001.fastq.gz"])
        # Predict output fastqs bcl2fastq2 with no lane splitting
        predictor.set(package="bcl2fastq2",
                      no_lane_splitting=True,
                      paired_end=False)
        self.assertEqual(project.dir_name,"PeterBriggs")
        self.assertEqual(sample1.dir_name,None)
        self.assertEqual(sample1.fastqs(),
                         ["PJB1-1579_S1_R1_001.fastq.gz"])
        self.assertEqual(sample2.fastqs(),
                         ["PJB2-1580_S2_R1_001.fastq.gz"])
        # Predict output fastqs bcl2fastq2 paired end
        predictor.set(package="bcl2fastq2",
                      no_lane_splitting=False,
                      paired_end=True)
        self.assertEqual(project.dir_name,"PeterBriggs")
        self.assertEqual(sample1.dir_name,None)
        self.assertEqual(sample1.fastqs(),
                         ["PJB1-1579_S1_L001_R1_001.fastq.gz",
                          "PJB1-1579_S1_L001_R2_001.fastq.gz",
                          "PJB1-1579_S1_L002_R1_001.fastq.gz",
                          "PJB1-1579_S1_L002_R2_001.fastq.gz"])
        self.assertEqual(sample2.dir_name,None)
        self.assertEqual(sample2.fastqs(),
                         ["PJB2-1580_S2_L001_R1_001.fastq.gz",
                          "PJB2-1580_S2_L001_R2_001.fastq.gz",
                          "PJB2-1580_S2_L002_R1_001.fastq.gz",
                          "PJB2-1580_S2_L002_R2_001.fastq.gz"])
        # Predict output fastqs bcl2fastq2 paired end with
        # no lane splitting
        predictor.set(package="bcl2fastq2",
                      no_lane_splitting=True,
                      paired_end=True)
        self.assertEqual(project.dir_name,"PeterBriggs")
        self.assertEqual(sample1.dir_name,None)
        self.assertEqual(sample1.fastqs(),
                         ["PJB1-1579_S1_R1_001.fastq.gz",
                          "PJB1-1579_S1_R2_001.fastq.gz"])
        self.assertEqual(sample2.dir_name,None)
        self.assertEqual(sample2.fastqs(),
                         ["PJB2-1580_S2_R1_001.fastq.gz",
                          "PJB2-1580_S2_R2_001.fastq.gz"])
        # Predict output fastqs CASAVA/bcl2fastq 1.8*
        predictor.set(package="casava",
                      paired_end=False)
        self.assertEqual(project.dir_name,"Project_PeterBriggs")
        self.assertEqual(sample1.dir_name,"Sample_PJB1-1579")
        self.assertEqual(sample1.fastqs(),
                         ["PJB1-1579_CGATGTAT-TCTTTCCC_L001_R1_001.fastq.gz",
                          "PJB1-1579_CGATGTAT-TCTTTCCC_L002_R1_001.fastq.gz"])
        self.assertEqual(sample2.dir_name,"Sample_PJB2-1580")
        self.assertEqual(sample2.fastqs(),
                         ["PJB2-1580_TGACCAAT-TCTTTCCC_L001_R1_001.fastq.gz",
                          "PJB2-1580_TGACCAAT-TCTTTCCC_L002_R1_001.fastq.gz"])
        # Predict output fastqs CASAVA/bcl2fastq 1.8* paired end
        predictor.set(package="casava",
                      paired_end=True)
        self.assertEqual(project.dir_name,"Project_PeterBriggs")
        self.assertEqual(sample1.dir_name,"Sample_PJB1-1579")
        self.assertEqual(sample1.fastqs(),
                         ["PJB1-1579_CGATGTAT-TCTTTCCC_L001_R1_001.fastq.gz",
                          "PJB1-1579_CGATGTAT-TCTTTCCC_L001_R2_001.fastq.gz",
                          "PJB1-1579_CGATGTAT-TCTTTCCC_L002_R1_001.fastq.gz",
                          "PJB1-1579_CGATGTAT-TCTTTCCC_L002_R2_001.fastq.gz"])
        self.assertEqual(sample2.dir_name,"Sample_PJB2-1580")
        self.assertEqual(sample2.fastqs(),
                         ["PJB2-1580_TGACCAAT-TCTTTCCC_L001_R1_001.fastq.gz",
                          "PJB2-1580_TGACCAAT-TCTTTCCC_L001_R2_001.fastq.gz",
                          "PJB2-1580_TGACCAAT-TCTTTCCC_L002_R1_001.fastq.gz",
                          "PJB2-1580_TGACCAAT-TCTTTCCC_L002_R2_001.fastq.gz"])

    def test_samplesheet_predictor_iem_no_lanes(self):
        """
        SampleSheetPredictor: handle IEM4 sample sheet with no lanes
        """
        iem = SampleSheet(fp=io.StringIO(
            self.miseq_sample_sheet_content))
        predictor = SampleSheetPredictor(sample_sheet=iem)
        # Get projects
        self.assertEqual(predictor.nprojects,1)
        self.assertEqual(predictor.project_names,["PJB"])
        project = predictor.get_project("PJB")
        self.assertRaises(KeyError,predictor.get_project,"DoesntExist")
        # Get samples
        self.assertEqual(project.sample_ids,["A8","B8"])
        sample1 = project.get_sample("A8")
        sample2 = project.get_sample("B8")
        self.assertRaises(KeyError,project.get_sample,"DoesntExist")
        # Check barcodes and lanes
        self.assertEqual(sample1.barcode_seqs,["TAAGGCGA-TAGATCGC"])
        self.assertEqual(sample2.barcode_seqs,["CGTACTAG-TAGATCGC"])
        self.assertEqual(sample1.lanes("TAAGGCGA-TAGATCGC"),[])
        self.assertEqual(sample2.lanes("CGTACTAG-TAGATCGC"),[])
        self.assertEqual(sample1.s_index,1)
        self.assertEqual(sample2.s_index,2)
        # Predict output fastqs bcl2fastq2
        predictor.set(package="bcl2fastq2")
        self.assertEqual(project.dir_name,"PJB")
        self.assertEqual(sample1.dir_name,None)
        self.assertEqual(sample1.fastqs(),
                         ["A8_S1_L001_R1_001.fastq.gz"])
        self.assertEqual(sample2.dir_name,None)
        self.assertEqual(sample2.fastqs(),
                         ["B8_S2_L001_R1_001.fastq.gz"])
        # Predict output fastqs bcl2fastq2 with no lane splitting
        predictor.set(package="bcl2fastq2",
                      no_lane_splitting=True)
        self.assertEqual(project.dir_name,"PJB")
        self.assertEqual(sample1.dir_name,None)
        self.assertEqual(sample1.fastqs(),
                         ["A8_S1_R1_001.fastq.gz"])
        self.assertEqual(sample2.dir_name,None)
        self.assertEqual(sample2.fastqs(),
                         ["B8_S2_R1_001.fastq.gz"])
        # Predict output fastqs bcl2fastq2 paired end
        predictor.set(package="bcl2fastq2",
                      no_lane_splitting=False,
                      paired_end=True)
        self.assertEqual(project.dir_name,"PJB")
        self.assertEqual(sample1.dir_name,None)
        self.assertEqual(sample1.fastqs(),
                         ["A8_S1_L001_R1_001.fastq.gz",
                          "A8_S1_L001_R2_001.fastq.gz"])
        self.assertEqual(sample2.dir_name,None)
        self.assertEqual(sample2.fastqs(),
                         ["B8_S2_L001_R1_001.fastq.gz",
                          "B8_S2_L001_R2_001.fastq.gz"])
        # Predict output fastqs bcl2fastq2 paired end with
        # no lane splitting
        predictor.set(package="bcl2fastq2",
                      no_lane_splitting=True,
                      paired_end=True)
        self.assertEqual(project.dir_name,"PJB")
        self.assertEqual(sample1.dir_name,None)
        self.assertEqual(sample1.fastqs(),
                         ["A8_S1_R1_001.fastq.gz",
                          "A8_S1_R2_001.fastq.gz"])
        self.assertEqual(sample2.dir_name,None)
        self.assertEqual(sample2.fastqs(),
                         ["B8_S2_R1_001.fastq.gz",
                          "B8_S2_R2_001.fastq.gz"])
        # Predict output fastqs bcl2fastq2 paired end with
        # explicitly specified lanes
        predictor.set(package="bcl2fastq2",
                      no_lane_splitting=False,
                      lanes=(1,2),
                      paired_end=True)
        self.assertEqual(project.dir_name,"PJB")
        self.assertEqual(sample1.dir_name,None)
        self.assertEqual(sample1.fastqs(),
                         ["A8_S1_L001_R1_001.fastq.gz",
                          "A8_S1_L001_R2_001.fastq.gz",
                          "A8_S1_L002_R1_001.fastq.gz",
                          "A8_S1_L002_R2_001.fastq.gz"])
        self.assertEqual(sample2.dir_name,None)
        self.assertEqual(sample2.fastqs(),
                         ["B8_S2_L001_R1_001.fastq.gz",
                          "B8_S2_L001_R2_001.fastq.gz",
                          "B8_S2_L002_R1_001.fastq.gz",
                          "B8_S2_L002_R2_001.fastq.gz"])
        # Predict output fastqs CASAVA/bcl2fastq 1.8*
        predictor.set(package="casava",
                      lanes=None,
                      paired_end=False)
        self.assertEqual(project.dir_name,"Project_PJB")
        self.assertEqual(sample1.dir_name,"Sample_A8")
        self.assertEqual(sample1.fastqs(),
                         ["A8_TAAGGCGA-TAGATCGC_L001_R1_001.fastq.gz"])
        self.assertEqual(sample2.dir_name,"Sample_B8")
        self.assertEqual(sample2.fastqs(),
                         ["B8_CGTACTAG-TAGATCGC_L001_R1_001.fastq.gz"])
        # Predict output fastqs CASAVA/bcl2fastq 1.8* paired end
        predictor.set(package="casava",
                      paired_end=True)
        self.assertEqual(project.dir_name,"Project_PJB")
        self.assertEqual(sample1.dir_name,"Sample_A8")
        self.assertEqual(sample1.fastqs(),
                         ["A8_TAAGGCGA-TAGATCGC_L001_R1_001.fastq.gz",
                          "A8_TAAGGCGA-TAGATCGC_L001_R2_001.fastq.gz"])
        self.assertEqual(sample2.dir_name,"Sample_B8")
        self.assertEqual(sample2.fastqs(),
                         ["B8_CGTACTAG-TAGATCGC_L001_R1_001.fastq.gz",
                          "B8_CGTACTAG-TAGATCGC_L001_R2_001.fastq.gz"])
        # Predict output fastqs CASAVA/bcl2fastq 1.8* paired end
        # and explicitly specify lanes
        predictor.set(package="casava",
                      lanes=(1,2),
                      paired_end=True)
        self.assertEqual(project.dir_name,"Project_PJB")
        self.assertEqual(sample1.dir_name,"Sample_A8")
        self.assertEqual(sample1.fastqs(),
                         ["A8_TAAGGCGA-TAGATCGC_L001_R1_001.fastq.gz",
                          "A8_TAAGGCGA-TAGATCGC_L001_R2_001.fastq.gz",
                          "A8_TAAGGCGA-TAGATCGC_L002_R1_001.fastq.gz",
                          "A8_TAAGGCGA-TAGATCGC_L002_R2_001.fastq.gz"])
        self.assertEqual(sample2.dir_name,"Sample_B8")
        self.assertEqual(sample2.fastqs(),
                          ["B8_CGTACTAG-TAGATCGC_L001_R1_001.fastq.gz",
                           "B8_CGTACTAG-TAGATCGC_L001_R2_001.fastq.gz",
                           "B8_CGTACTAG-TAGATCGC_L002_R1_001.fastq.gz",
                           "B8_CGTACTAG-TAGATCGC_L002_R2_001.fastq.gz"])

    def test_samplesheet_predictor_casava(self):
        """
        SampleSheetPredictor: handle CASAVA-style sample sheet
        """
        casava = SampleSheet(fp=io.StringIO(
            self.casava_sample_sheet_content))
        predictor = SampleSheetPredictor(sample_sheet=casava)
        self.assertEqual(predictor.nprojects,2)
        self.assertEqual(predictor.project_names,["AR","Control"])
        self.assertRaises(KeyError,predictor.get_project,"DoesntExist")
        # Get projects
        project1 = predictor.get_project("Control")
        project2 = predictor.get_project("AR")
        self.assertEqual(project1.sample_ids,["PhiX"])
        self.assertEqual(project2.sample_ids,["884-1","885-1","886-1"])
        # Get samples
        sample1 = project1.get_sample("PhiX")
        sample2 = project2.get_sample("884-1")
        sample3 = project2.get_sample("885-1")
        sample4 = project2.get_sample("886-1")
        self.assertRaises(KeyError,project1.get_sample,"DoesntExist")
        self.assertRaises(KeyError,project2.get_sample,"DoesntExist")
        # Check assigned barcodes and lanes
        self.assertEqual(sample1.barcode_seqs,["CTGCCT"])
        self.assertEqual(sample2.barcode_seqs,["AGTCAA"])
        self.assertEqual(sample3.barcode_seqs,["AGTTCC"])
        self.assertEqual(sample4.barcode_seqs,["ATGTCA"])
        self.assertEqual(sample1.lanes("CTGCCT"),[1,8])
        self.assertEqual(sample2.lanes("AGTCAA"),[2,5])
        self.assertEqual(sample3.lanes("AGTTCC"),[3,6])
        self.assertEqual(sample4.lanes("ATGTCA"),[4,7])
        self.assertEqual(sample1.s_index,1)
        self.assertEqual(sample2.s_index,2)
        self.assertEqual(sample3.s_index,3)
        self.assertEqual(sample4.s_index,4)
        # Predict output fastqs bcl2fastq2
        predictor.set(package="bcl2fastq2")
        self.assertEqual(project1.dir_name,"Control")
        self.assertEqual(project2.dir_name,"AR")
        self.assertEqual(sample1.dir_name,None)
        self.assertEqual(sample1.fastqs(),
                         ["PhiX_S1_L001_R1_001.fastq.gz",
                          "PhiX_S1_L008_R1_001.fastq.gz"])
        self.assertEqual(sample2.dir_name,None)
        self.assertEqual(sample2.fastqs(),
                         ["884-1_S2_L002_R1_001.fastq.gz",
                          "884-1_S2_L005_R1_001.fastq.gz"])
        self.assertEqual(sample3.dir_name,None)
        self.assertEqual(sample3.fastqs(),
                         ["885-1_S3_L003_R1_001.fastq.gz",
                          "885-1_S3_L006_R1_001.fastq.gz"])
        self.assertEqual(sample4.dir_name,None)
        self.assertEqual(sample4.fastqs(),
                         ["886-1_S4_L004_R1_001.fastq.gz",
                          "886-1_S4_L007_R1_001.fastq.gz"])
        # Predict output fastqs CASAVA/bcl2fastq 1.8*
        predictor.set(package="casava")
        self.assertEqual(project1.dir_name,"Project_Control")
        self.assertEqual(project2.dir_name,"Project_AR")
        self.assertEqual(sample1.dir_name,"Sample_PhiX")
        self.assertEqual(sample1.fastqs(),
                         ["PhiX_CTGCCT_L001_R1_001.fastq.gz",
                          "PhiX_CTGCCT_L008_R1_001.fastq.gz"])
        self.assertEqual(sample2.dir_name,"Sample_884-1")
        self.assertEqual(sample2.fastqs(),
                         ["884-1_AGTCAA_L002_R1_001.fastq.gz",
                          "884-1_AGTCAA_L005_R1_001.fastq.gz"])
        self.assertEqual(sample3.dir_name,"Sample_885-1")
        self.assertEqual(sample3.fastqs(),
                         ["885-1_AGTTCC_L003_R1_001.fastq.gz",
                          "885-1_AGTTCC_L006_R1_001.fastq.gz"])
        self.assertEqual(sample4.dir_name,"Sample_886-1")
        self.assertEqual(sample4.fastqs(),
                         ["886-1_ATGTCA_L004_R1_001.fastq.gz",
                          "886-1_ATGTCA_L007_R1_001.fastq.gz"])

    def test_samplesheet_predictor_iem_id_and_names_differ(self):
        """
        SampleSheetPredictor: handle IEM4 sample sheet where sample ID differs from name
        """
        iem = SampleSheet(fp=io.StringIO(
            self.hiseq_sample_sheet_id_and_name_differ_content))
        predictor = SampleSheetPredictor(sample_sheet=iem)
        # Get projects
        self.assertEqual(predictor.nprojects,1)
        self.assertEqual(predictor.project_names,["PeterBriggs"])
        project = predictor.get_project("PeterBriggs")
        self.assertRaises(KeyError,predictor.get_project,"DoesntExist")
        # Get samples
        self.assertEqual(project.sample_ids,["PJB1-1579","PJB2-1580"])
        sample1 = project.get_sample("PJB1-1579")
        sample2 = project.get_sample("PJB2-1580")
        self.assertRaises(KeyError,project.get_sample,"DoesntExist")
        # Check sample barcodes and lanes
        self.assertEqual(sample1.barcode_seqs,["CGATGTAT-TCTTTCCC"])
        self.assertEqual(sample2.barcode_seqs,["TGACCAAT-TCTTTCCC"])
        self.assertEqual(sample1.lanes("CGATGTAT-TCTTTCCC"),[1,2])
        self.assertEqual(sample2.lanes("TGACCAAT-TCTTTCCC"),[1,2])
        self.assertEqual(sample1.s_index,1)
        self.assertEqual(sample2.s_index,2)
        # Predict output fastqs bcl2fastq2
        predictor.set(package="bcl2fastq2")
        self.assertEqual(project.dir_name,"PeterBriggs")
        self.assertEqual(sample1.dir_name,"PJB1")
        self.assertEqual(sample1.fastqs(),
                         ["PJB1-1579_S1_L001_R1_001.fastq.gz",
                          "PJB1-1579_S1_L002_R1_001.fastq.gz"])
        self.assertEqual(sample2.dir_name,"PJB2")
        self.assertEqual(sample2.fastqs(),
                         ["PJB2-1580_S2_L001_R1_001.fastq.gz",
                          "PJB2-1580_S2_L002_R1_001.fastq.gz"])
        # Predict output fastqs CASAVA/bcl2fastq 1.8*
        predictor.set(package="casava")
        self.assertEqual(project.dir_name,"Project_PeterBriggs")
        self.assertEqual(sample1.fastqs(),
                         ["PJB1-1579_CGATGTAT-TCTTTCCC_L001_R1_001.fastq.gz",
                          "PJB1-1579_CGATGTAT-TCTTTCCC_L002_R1_001.fastq.gz"])
        self.assertEqual(sample2.fastqs(),
                         ["PJB2-1580_TGACCAAT-TCTTTCCC_L001_R1_001.fastq.gz",
                          "PJB2-1580_TGACCAAT-TCTTTCCC_L002_R1_001.fastq.gz"])

    def test_samplesheet_predictor_iem_force_sample_dir(self):
        """
        SampleSheetPredictor: force insertion of sample dir for IEM4 sample sheet where ID and name are same
        """
        iem = SampleSheet(fp=io.StringIO(
            self.hiseq_sample_sheet_content))
        predictor = SampleSheetPredictor(sample_sheet=iem)
        # Get projects
        self.assertEqual(predictor.nprojects,1)
        self.assertEqual(predictor.project_names,["PeterBriggs"])
        project = predictor.get_project("PeterBriggs")
        self.assertRaises(KeyError,predictor.get_project,"DoesntExist")
        # Get samples
        self.assertEqual(project.sample_ids,["PJB1-1579","PJB2-1580"])
        sample1 = project.get_sample("PJB1-1579")
        sample2 = project.get_sample("PJB2-1580")
        self.assertRaises(KeyError,project.get_sample,"DoesntExist")
        # Check sample barcodes and lanes
        self.assertEqual(sample1.barcode_seqs,["CGATGTAT-TCTTTCCC"])
        self.assertEqual(sample2.barcode_seqs,["TGACCAAT-TCTTTCCC"])
        self.assertEqual(sample1.lanes("CGATGTAT-TCTTTCCC"),[1,2])
        self.assertEqual(sample2.lanes("TGACCAAT-TCTTTCCC"),[1,2])
        self.assertEqual(sample1.s_index,1)
        self.assertEqual(sample2.s_index,2)
        # Predict output fastqs bcl2fastq2
        predictor.set(package="bcl2fastq2",
                      force_sample_dir=True)
        self.assertEqual(project.dir_name,"PeterBriggs")
        self.assertEqual(sample1.dir_name,"PJB1-1579")
        self.assertEqual(sample1.fastqs(),
                         ["PJB1-1579_S1_L001_R1_001.fastq.gz",
                          "PJB1-1579_S1_L002_R1_001.fastq.gz"])
        self.assertEqual(sample2.dir_name,"PJB2-1580")
        self.assertEqual(sample2.fastqs(),
                         ["PJB2-1580_S2_L001_R1_001.fastq.gz",
                          "PJB2-1580_S2_L002_R1_001.fastq.gz"])
        # Predict output fastqs CASAVA/bcl2fastq 1.8*
        predictor.set(package="casava")
        self.assertEqual(project.dir_name,"Project_PeterBriggs")
        self.assertEqual(sample1.fastqs(),
                         ["PJB1-1579_CGATGTAT-TCTTTCCC_L001_R1_001.fastq.gz",
                          "PJB1-1579_CGATGTAT-TCTTTCCC_L002_R1_001.fastq.gz"])
        self.assertEqual(sample2.fastqs(),
                         ["PJB2-1580_TGACCAAT-TCTTTCCC_L001_R1_001.fastq.gz",
                          "PJB2-1580_TGACCAAT-TCTTTCCC_L002_R1_001.fastq.gz"])

    def test_samplesheet_predictor_iem_name_no_id(self):
        """
        SampleSheetPredictor: handle IEM4 sample sheet where sample name is supplied instead of ID
        """
        iem = SampleSheet(fp=io.StringIO(
            self.hiseq_sample_sheet_name_no_id_content))
        predictor = SampleSheetPredictor(sample_sheet=iem)
        # Get projects
        self.assertEqual(predictor.nprojects,1)
        self.assertEqual(predictor.project_names,["PeterBriggs"])
        project = predictor.get_project("PeterBriggs")
        self.assertRaises(KeyError,predictor.get_project,"DoesntExist")
        # Get samples
        self.assertEqual(project.sample_ids,["PJB1-1579","PJB2-1580"])
        sample1 = project.get_sample("PJB1-1579")
        sample2 = project.get_sample("PJB2-1580")
        self.assertRaises(KeyError,project.get_sample,"DoesntExist")
        # Check sample barcodes and lanes
        self.assertEqual(sample1.barcode_seqs,["CGATGTAT-TCTTTCCC"])
        self.assertEqual(sample2.barcode_seqs,["TGACCAAT-TCTTTCCC"])
        self.assertEqual(sample1.lanes("CGATGTAT-TCTTTCCC"),[1,2])
        self.assertEqual(sample2.lanes("TGACCAAT-TCTTTCCC"),[1,2])
        self.assertEqual(sample1.s_index,1)
        self.assertEqual(sample2.s_index,2)
        # Predict output fastqs bcl2fastq2
        predictor.set(package="bcl2fastq2")
        self.assertEqual(project.dir_name,"PeterBriggs")
        self.assertEqual(sample1.dir_name,None)
        self.assertEqual(sample1.fastqs(),
                         ["PJB1-1579_S1_L001_R1_001.fastq.gz",
                          "PJB1-1579_S1_L002_R1_001.fastq.gz"])
        self.assertEqual(sample2.dir_name,None)
        self.assertEqual(sample2.fastqs(),
                         ["PJB2-1580_S2_L001_R1_001.fastq.gz",
                          "PJB2-1580_S2_L002_R1_001.fastq.gz"])
        # Predict output fastqs CASAVA/bcl2fastq 1.8*
        predictor.set(package="casava")
        self.assertEqual(project.dir_name,"Project_PeterBriggs")
        self.assertEqual(sample1.fastqs(),
                         ["PJB1-1579_CGATGTAT-TCTTTCCC_L001_R1_001.fastq.gz",
                          "PJB1-1579_CGATGTAT-TCTTTCCC_L002_R1_001.fastq.gz"])
        self.assertEqual(sample2.fastqs(),
                         ["PJB2-1580_TGACCAAT-TCTTTCCC_L001_R1_001.fastq.gz",
                          "PJB2-1580_TGACCAAT-TCTTTCCC_L002_R1_001.fastq.gz"])

    def test_samplesheet_predictor_iem_no_barcodes(self):
        """
        SampleSheetPredictor: handle IEM4 sample sheet with no barcodes
        """
        iem = SampleSheet(fp=io.StringIO(
            self.hiseq_sample_sheet_no_barcodes))
        predictor = SampleSheetPredictor(sample_sheet=iem)
        # Get projects
        self.assertEqual(predictor.nprojects,1)
        self.assertEqual(predictor.project_names,["PeterBriggs"])
        project = predictor.get_project("PeterBriggs")
        self.assertRaises(KeyError,predictor.get_project,"DoesntExist")
        # Get samples
        self.assertEqual(project.sample_ids,["PJB1","PJB2"])
        sample1 = project.get_sample("PJB1")
        sample2 = project.get_sample("PJB2")
        self.assertRaises(KeyError,project.get_sample,"DoesntExist")
        # Check sample barcodes and lanes
        self.assertEqual(sample1.barcode_seqs,["NoIndex"])
        self.assertEqual(sample2.barcode_seqs,["NoIndex"])
        self.assertEqual(sample1.lanes(),[1,])
        self.assertEqual(sample2.lanes(),[2,])
        self.assertEqual(sample1.s_index,1)
        self.assertEqual(sample2.s_index,2)
        # Predict output fastqs bcl2fastq2
        predictor.set(package="bcl2fastq2")
        self.assertEqual(project.dir_name,"PeterBriggs")
        self.assertEqual(sample1.fastqs(),
                         ["PJB1_S1_L001_R1_001.fastq.gz"])
        self.assertEqual(sample2.fastqs(),
                         ["PJB2_S2_L002_R1_001.fastq.gz"])
        # Predict output fastqs CASAVA/bcl2fastq 1.8*
        predictor.set(package="casava")
        self.assertEqual(project.dir_name,"Project_PeterBriggs")
        self.assertEqual(sample1.fastqs(),
                         ["PJB1_NoIndex_L001_R1_001.fastq.gz"])
        self.assertEqual(sample2.fastqs(),
                         ["PJB2_NoIndex_L002_R1_001.fastq.gz"])

    def test_samplesheet_predictor_iem_lanes_out_of_order(self):
        """
        SampleSheetPredictor: handle IEM4 sample sheet with lane order reversed
        """
        iem = SampleSheet(fp=io.StringIO(
            self.hiseq_sample_sheet_lanes_out_of_order))
        predictor = SampleSheetPredictor(sample_sheet=iem)
        # Check projects
        self.assertEqual(predictor.nprojects,2)
        self.assertEqual(predictor.project_names,["AlanBarclay","CarlDavis"])
        # Check sample barcodes and lanes for first project
        project1 = predictor.get_project("AlanBarclay")
        self.assertEqual(project1.sample_ids,["AB1","AB2"])
        sample1 = project1.get_sample("AB1")
        sample2 = project1.get_sample("AB2")
        self.assertEqual(sample1.barcode_seqs,["CGATGTAT-TCTTTCCC"])
        self.assertEqual(sample2.barcode_seqs,["TGACCAAT-TCTTTCCC"])
        self.assertEqual(sample1.lanes("CGATGTAT-TCTTTCCC"),[2,])
        self.assertEqual(sample2.lanes("TGACCAAT-TCTTTCCC"),[2,])
        self.assertEqual(sample1.s_index,3)
        self.assertEqual(sample2.s_index,4)
        # Check sample barcodes and lanes for second project
        project2 = predictor.get_project("CarlDavis")
        self.assertEqual(project2.sample_ids,["CD3","CD4"])
        sample3 = project2.get_sample("CD3")
        sample4 = project2.get_sample("CD4")
        self.assertEqual(sample3.barcode_seqs,["GTATCGAT-TCTTTCCC"])
        self.assertEqual(sample4.barcode_seqs,["CAATTGAC-TCTTTCCC"])
        self.assertEqual(sample3.lanes("GTATCGAT-TCTTTCCC"),[1,])
        self.assertEqual(sample4.lanes("CAATTGAC-TCTTTCCC"),[1,])
        self.assertEqual(sample3.s_index,1)
        self.assertEqual(sample4.s_index,2)
        # Predict output fastqs bcl2fastq2
        predictor.set(package="bcl2fastq2")
        self.assertEqual(project1.dir_name,"AlanBarclay")
        self.assertEqual(sample1.fastqs(),
                         ["AB1_S3_L002_R1_001.fastq.gz"])
        self.assertEqual(sample2.fastqs(),
                         ["AB2_S4_L002_R1_001.fastq.gz"])
        self.assertEqual(project2.dir_name,"CarlDavis")
        self.assertEqual(sample3.fastqs(),
                         ["CD3_S1_L001_R1_001.fastq.gz"])
        self.assertEqual(sample4.fastqs(),
                         ["CD4_S2_L001_R1_001.fastq.gz"])
        # Predict output fastqs CASAVA/bcl2fastq 1.8*
        predictor.set(package="casava")
        self.assertEqual(project1.dir_name,"Project_AlanBarclay")
        self.assertEqual(sample1.fastqs(),
                         ["AB1_CGATGTAT-TCTTTCCC_L002_R1_001.fastq.gz"])
        self.assertEqual(sample2.fastqs(),
                         ["AB2_TGACCAAT-TCTTTCCC_L002_R1_001.fastq.gz"])
        self.assertEqual(project2.dir_name,"Project_CarlDavis")
        self.assertEqual(sample3.fastqs(),
                         ["CD3_GTATCGAT-TCTTTCCC_L001_R1_001.fastq.gz"])
        self.assertEqual(sample4.fastqs(),
                         ["CD4_CAATTGAC-TCTTTCCC_L001_R1_001.fastq.gz"])

    def test_samplesheet_predictor_iem_no_projects(self):
        """
        SampleSheetPredictor: handle IEM4 sample sheet with no projects
        """
        iem = SampleSheet(fp=io.StringIO(
            self.miseq_sample_sheet_no_projects))
        predictor = SampleSheetPredictor(sample_sheet=iem)
        # Get projects
        self.assertEqual(predictor.nprojects,1)
        self.assertEqual(predictor.project_names,[""])
        project = predictor.get_project("")
        self.assertRaises(KeyError,predictor.get_project,"DoesntExist")
        # Get samples
        self.assertEqual(project.sample_ids,["Sample1","Sample2"])
        sample1 = project.get_sample("Sample1")
        sample2 = project.get_sample("Sample2")
        self.assertRaises(KeyError,project.get_sample,"DoesntExist")
        # Check sample barcodes and lanes
        self.assertEqual(sample1.barcode_seqs,["CGTGTAGG-GACCTGTA"])
        self.assertEqual(sample2.barcode_seqs,["CGTGTAGG-ATGTAACT"])
        self.assertEqual(sample1.lanes("CGTGTAGG-GACCTGTA"),[])
        self.assertEqual(sample2.lanes("CGTGTAGG-ATGTAACT"),[])
        self.assertEqual(sample1.s_index,1)
        self.assertEqual(sample2.s_index,2)
        # Predict output fastqs bcl2fastq2
        predictor.set(package="bcl2fastq2")
        self.assertEqual(project.dir_name,"")
        self.assertEqual(sample1.fastqs(),
                         ["Sample1_S1_L001_R1_001.fastq.gz"])
        self.assertEqual(sample1.dir_name,None)
        self.assertEqual(sample2.fastqs(),
                         ["Sample2_S2_L001_R1_001.fastq.gz"])
        self.assertEqual(sample2.dir_name,None)
        # Predict output fastqs CASAVA/bcl2fastq 1.8*
        predictor.set(package="casava")
        self.assertEqual(project.dir_name,"")
        self.assertEqual(sample1.fastqs(),
                         ["Sample1_CGTGTAGG-GACCTGTA_L001_R1_001.fastq.gz"])
        self.assertEqual(sample2.fastqs(),
                         ["Sample2_CGTGTAGG-ATGTAACT_L001_R1_001.fastq.gz"])

    def test_samplesheet_predictor_iem_with_index_reads(self):
        """
        SampleSheetPredictor: handle IEM4 sample sheet with index reads
        """
        iem = SampleSheet(fp=io.StringIO(
            self.hiseq_sample_sheet_content))
        predictor = SampleSheetPredictor(sample_sheet=iem)
        # Get projects
        self.assertEqual(predictor.nprojects,1)
        self.assertEqual(predictor.project_names,["PeterBriggs"])
        project = predictor.get_project("PeterBriggs")
        self.assertRaises(KeyError,predictor.get_project,"DoesntExist")
        # Get samples
        self.assertEqual(project.sample_ids,["PJB1-1579","PJB2-1580"])
        sample1 = project.get_sample("PJB1-1579")
        sample2 = project.get_sample("PJB2-1580")
        self.assertRaises(KeyError,project.get_sample,"DoesntExist")
        # Check sample barcodes and lanes
        self.assertEqual(sample1.barcode_seqs,["CGATGTAT-TCTTTCCC"])
        self.assertEqual(sample2.barcode_seqs,["TGACCAAT-TCTTTCCC"])
        self.assertEqual(sample1.lanes("CGATGTAT-TCTTTCCC"),[1,2])
        self.assertEqual(sample2.lanes("TGACCAAT-TCTTTCCC"),[1,2])
        self.assertEqual(sample1.s_index,1)
        self.assertEqual(sample2.s_index,2)
        # Predict output fastqs bcl2fastq2
        predictor.set(package="bcl2fastq2",
                      paired_end=True,
                      include_index_reads=True)
        self.assertEqual(project.dir_name,"PeterBriggs")
        self.assertEqual(sample1.dir_name,None)
        self.assertEqual(sample1.fastqs(),
                         ["PJB1-1579_S1_L001_I1_001.fastq.gz",
                          "PJB1-1579_S1_L001_I2_001.fastq.gz",
                          "PJB1-1579_S1_L001_R1_001.fastq.gz",
                          "PJB1-1579_S1_L001_R2_001.fastq.gz",
                          "PJB1-1579_S1_L002_I1_001.fastq.gz",
                          "PJB1-1579_S1_L002_I2_001.fastq.gz",
                          "PJB1-1579_S1_L002_R1_001.fastq.gz",
                          "PJB1-1579_S1_L002_R2_001.fastq.gz"])
        self.assertEqual(sample2.dir_name,None)
        self.assertEqual(sample2.fastqs(),
                         ["PJB2-1580_S2_L001_I1_001.fastq.gz",
                          "PJB2-1580_S2_L001_I2_001.fastq.gz",
                          "PJB2-1580_S2_L001_R1_001.fastq.gz",
                          "PJB2-1580_S2_L001_R2_001.fastq.gz",
                          "PJB2-1580_S2_L002_I1_001.fastq.gz",
                          "PJB2-1580_S2_L002_I2_001.fastq.gz",
                          "PJB2-1580_S2_L002_R1_001.fastq.gz",
                          "PJB2-1580_S2_L002_R2_001.fastq.gz"])

    def test_samplesheet_predictor_iem_with_custom_reads(self):
        """
        SampleSheetPredictor: handle IEM4 sample sheet with custom reads
        """
        iem = SampleSheet(fp=io.StringIO(
            self.hiseq_sample_sheet_content))
        predictor = SampleSheetPredictor(sample_sheet=iem)
        # Get projects
        self.assertEqual(predictor.nprojects,1)
        self.assertEqual(predictor.project_names,["PeterBriggs"])
        project = predictor.get_project("PeterBriggs")
        self.assertRaises(KeyError,predictor.get_project,"DoesntExist")
        # Get samples
        self.assertEqual(project.sample_ids,["PJB1-1579","PJB2-1580"])
        sample1 = project.get_sample("PJB1-1579")
        sample2 = project.get_sample("PJB2-1580")
        self.assertRaises(KeyError,project.get_sample,"DoesntExist")
        # Check sample barcodes and lanes
        self.assertEqual(sample1.barcode_seqs,["CGATGTAT-TCTTTCCC"])
        self.assertEqual(sample2.barcode_seqs,["TGACCAAT-TCTTTCCC"])
        self.assertEqual(sample1.lanes("CGATGTAT-TCTTTCCC"),[1,2])
        self.assertEqual(sample2.lanes("TGACCAAT-TCTTTCCC"),[1,2])
        self.assertEqual(sample1.s_index,1)
        self.assertEqual(sample2.s_index,2)
        # Predict output fastqs bcl2fastq2
        predictor.set(package="bcl2fastq2",
                      reads=('R1','R2','R3','I1',),
                      include_index_reads=True)
        self.assertEqual(project.dir_name,"PeterBriggs")
        self.assertEqual(sample1.dir_name,None)
        self.assertEqual(sample1.fastqs(),
                         ["PJB1-1579_S1_L001_I1_001.fastq.gz",
                          "PJB1-1579_S1_L001_R1_001.fastq.gz",
                          "PJB1-1579_S1_L001_R2_001.fastq.gz",
                          "PJB1-1579_S1_L001_R3_001.fastq.gz",
                          "PJB1-1579_S1_L002_I1_001.fastq.gz",
                          "PJB1-1579_S1_L002_R1_001.fastq.gz",
                          "PJB1-1579_S1_L002_R2_001.fastq.gz",
                          "PJB1-1579_S1_L002_R3_001.fastq.gz"])
        self.assertEqual(sample2.dir_name,None)
        self.assertEqual(sample2.fastqs(),
                         ["PJB2-1580_S2_L001_I1_001.fastq.gz",
                          "PJB2-1580_S2_L001_R1_001.fastq.gz",
                          "PJB2-1580_S2_L001_R2_001.fastq.gz",
                          "PJB2-1580_S2_L001_R3_001.fastq.gz",
                          "PJB2-1580_S2_L002_I1_001.fastq.gz",
                          "PJB2-1580_S2_L002_R1_001.fastq.gz",
                          "PJB2-1580_S2_L002_R2_001.fastq.gz",
                          "PJB2-1580_S2_L002_R3_001.fastq.gz"])


class TestSampleSheetIndexSequence(unittest.TestCase):

    def test_casava_single_index(self):
        """
        samplesheet_index_sequence: check CASAVA sample sheet single index
        """
        line = TabDataLine(line="FC1,1,AB_control,,CGATGT,,,,,Control",
                           column_names=('FCID',
                                         'Lane',
                                         'SampleID',
                                         'SampleRef',
                                         'Index',
                                         'Description',
                                         'Control',
                                         'Recipe',
                                         'Operator',
                                         'SampleProject'),
                           delimiter=",")
        self.assertEqual(samplesheet_index_sequence(line),'CGATGT')

    def test_casava_dual_index(self):
        """
        samplesheet_index_sequence: check CASAVA sample sheet dual index
        """
        line = TabDataLine(line="FC1,1,C01,,TAAGGCGA-GCGTAAGA,,,,,KP",
                           column_names=('FCID',
                                         'Lane',
                                         'SampleID',
                                         'SampleRef',
                                         'Index',
                                         'Description',
                                         'Control',
                                         'Recipe',
                                         'Operator',
                                         'SampleProject'),
                           delimiter=",")
        self.assertEqual(samplesheet_index_sequence(line),'TAAGGCGA-GCGTAAGA')

    def test_iem_single_index(self):
        """
        samplesheet_index_sequence: check IEM4 sample sheet single index
        """
        line = TabDataLine(line="1,ABT1,ABT1,,,A002,CGATGT,AB,",
                           column_names=('Lane',
                                         'Sample_ID',
                                         'Sample_Name',
                                         'Sample_Plate',
                                         'Sample_Well',
                                         'I7_Index_ID',
                                         'index',
                                         'Sample_Project',
                                         'Description'),
                           delimiter=",")
        self.assertEqual(samplesheet_index_sequence(line),'CGATGT')

    def test_iem_dual_index(self):
        """
        samplesheet_index_sequence: check IEM4 sample sheet dual index
        """
        line = TabDataLine(line="1,S1,S1,,,D701,CGTGTAGG,D501,GACCTGTA,HO,",
                           column_names=('Lane',
                                         'Sample_ID',
                                         'Sample_Name',
                                         'Sample_Plate',
                                         'Sample_Well',
                                         'I7_Index_ID',
                                         'index',
                                         'I5_Index_ID',
                                         'index2',
                                         'Sample_Project',
                                         'Description'),
                           delimiter=",")
        self.assertEqual(samplesheet_index_sequence(line),'CGTGTAGG-GACCTGTA')

    def test_iem_no_index(self):
        """
        samplesheet_index_sequence: check IEM4 sample sheet no index column
        """
        line = TabDataLine(line="PB2,PB2,,,PB,",
                         column_names=('Sample_ID',
                                       'Sample_Name',
                                       'Sample_Plate',
                                       'Sample_Well',
                                       'Sample_Project',
                                       'Description'),
                           delimiter=",")
        self.assertEqual(samplesheet_index_sequence(line),None)
