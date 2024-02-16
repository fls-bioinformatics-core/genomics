#     mock.py: module providing mock Illumina data for testing
#     Copyright (C) University of Manchester 2012-2024 Peter Briggs
#
########################################################################

"""
mock.py

Provides data and classes for mocking up examples of outputs from
Illumina-based sequencer pipeline (e.g. GA2x or HiSeq), including example
directory structures and input and output files, to be used in testing.

These include:

- MockSampleSheet: synthesises a SampleSheet.csv
- MockIlluminaRun: synthesises the raw data output from a sequencer
- MockIlluminaData: synthesises the output from CASAVA/bcl2fastq run

There are also static classes with example data:

- SampleSheets: has properties with example SampleSheet.csv files
- RunInfoXml: has static methods for making RunInfo.xml files
- RunParametersXml: has static methods for making RunParameters.xml file

There is a function for mocking the STAR aligner:

- mockSTAR: driver function for a "mock" STAR executable

"""

#######################################################################
# Import modules that this module depends on
#######################################################################

from builtins import str
from builtins import range
import os
import io
import shutil
import gzip
import argparse
from .IlluminaData import IlluminaFastq
from .IlluminaData import SampleSheet
from .TabFile import TabFile
from .platforms import get_run_completion_files
from .utils import OrderedDictionary
from .utils import mkdir

#######################################################################
# Module data
#######################################################################

class SampleSheets:
    """
    Class with example sample sheets

    There is no need to instantiate this class, to access
    a specific sample sheet use e.g.:

    >>> print(SampleSheets.miseq)

    """
    miseq = u"""[Header],,,,,,,,,
IEMFileVersion,4,,,,,,,,
Date,11/23/2015,,,,,,,,
Workflow,GenerateFASTQ,,,,,,,,
Application,FASTQ Only,,,,,,,,
Assay,TruSeq HT,,,,,,,,
Description,,,,,,,,,
Chemistry,Amplicon,,,,,,,,
,,,,,,,,,
[Reads],,,,,,,,,
101,,,,,,,,,
101,,,,,,,,,
,,,,,,,,,
[Settings],,,,,,,,,
ReverseComplement,0,,,,,,,,
Adapter,AGATCGGAAGAGCACACGTCTGAACTCCAGTCA,,,,,,,,
AdapterRead2,AGATCGGAAGAGCGTCGTGTAGGGAAAGAGTGT,,,,,,,,
,,,,,,,,,
[Data],,,,,,,,,
Sample_ID,Sample_Name,Sample_Plate,Sample_Well,I7_Index_ID,index,I5_Index_ID,index2,Sample_Project,Description
Sample1,Sample1,,,D701,CGTGTAGG,D501,GACCTGTA,,
Sample2,Sample2,,,D702,CGTGTAGG,D501,ATGTAACT,,"""
    hiseq = u"""[Header],,,,,,,,,,
IEMFileVersion,4,,,,,,,,,
Date,11/11/2015,,,,,,,,,
Workflow,GenerateFASTQ,,,,,,,,,
Application,HiSeq FASTQ Only,,,,,,,,,
Assay,Nextera XT,,,,,,,,,
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
1,AB1,AB1,,,N701,TAAGGCGA,S504,AGAGTAGA,AB,
2,TM2,TM2,,,N701,TAAGGCGA,S517,GCGTAAGA,TM,
3,CD3,CD3,,,N701,GTGAAACG,S503,TCTTTCCC,CD,
4,EB4,EB4,,A1,N701,TAAGGCGA,S501,TAGATCGC,EB,
5,EB5,EB5,,A3,N703,AGGCAGAA,S501,TAGATCGC,EB,
6,EB6,EB6,,F3,N703,AGGCAGAA,S506,ACTGCATA,EB,
7,ML7,ML7,,,N701,GCCAATAT,S502,TCTTTCCC,ML,
8,VL8,VL8,,,N701,GCCAATAT,S503,TCTTTCCC,VL,"""
    novaseq = u"""[Header],,,,,,,,,,,
IEMFileVersion,5,,,,,,,,,,
Experiment Name,NovaSeq Run 40,,,,,,,,,,
Date,12/02/2022,,,,,,,,,,
Workflow,GenerateFASTQ,,,,,,,,,,
Application,NovaSeq FASTQ Only,,,,,,,,,,
Instrument Type,NovaSeq,,,,,,,,,,
Assay,Illumina Stranded mRNA,,,,,,,,,,
Index Adapters,IDT-Ilmn RNA UD Indexes SetABCD Ligation,,,,,,,,,,
Chemistry,Amplicon,,,,,,,,,,
,,,,,,,,,,,
[Reads],,,,,,,,,,,
101,,,,,,,,,,,
101,,,,,,,,,,,
,,,,,,,,,,,
[Settings],,,,,,,,,,,
Adapter,CTGTCTCTTATACACATCT,,,,,,,,,,
,,,,,,,,,,,
[Data],,,,,,,,,,,
Sample_ID,Sample_Name,Sample_Plate,Sample_Well,Index_Plate,Index_Plate_Well,I7_Index_ID,index,I5_Index_ID,index2,Sample_Project,Description
AI1,AI1,,,A,A04,UDP0025,AACCATAGAA,UDP0025,CCATCTCGCC,AI,
AI2,AI2,,,A,B04,UDP0026,GGTTGCGAGG,UDP0026,TTGCTCTATT,AI,
SC1,SC1,,,B,A12,UDP0185,ACGGTCCAAC,UDP0185,TGATGTAAGA,SC,
SC2,SC2,,,B,B12,UDP0186,GTAACTTGGT,UDP0186,AGGTATGGCG,SC,
"""

class RunInfoXml:
    """
    Class with example RunInfo.xml files

    There is no need to instantiate this class, to access
    a specific RunInfo.xml use e.g.:

    >>> print(RunInfoXml.hiseq('151125_AB12345_001_CD256X'))

    Arbitrary RunInfo.xml content can be created
    directly using the 'create' method.

    """
    @staticmethod
    def create(run_name,bases_mask,nlanes,tilecount=None,
               align_to_phix=False):
        # Split the run name
        items = run_name.split("_")
        try:
            datestamp = items[0]
        except IndexError:
            datestamp = "171018"
        try:
            instrument = items[1]
        except IndexError:
            instrument = "S00001"
        try:
            number = items[2]
        except IndexError:
            number = "1"
        try:
            flowcell = items[3]
        except IndexError:
            flowcell = "XXXXABCD1"
        if flowcell[0] in ('A','B',):
            flowcell = flowcell[1:]
        # Bases mask
        reads = []
        for item in bases_mask.split(","):
            is_indexed_read = ('Y' if item.upper().startswith("I")
                               else 'N')
            num_cycles = item[1:]
            assert int(num_cycles) > 0
            reads.append({ 'is_indexed_read': is_indexed_read,
                           'num_cycles': num_cycles})
        # Other attributes
        if tilecount is None:
            tilecount = 16
        # Construct the XML
        xml = u"""<?xml version="1.0"?>
<RunInfo xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" Version="2">
  <Run Id="%s" Number="%s">
    <Flowcell>%s</Flowcell>
    <Instrument>%s</Instrument>
    <Date>%s</Date>
""" % (run_name,number,flowcell,instrument,datestamp)
        # Add reads
        xml += "    <Reads>\n"
        for n,rd in enumerate(reads):
            xml += "      <Read Number=\"%s\" NumCycles=\"%s\" IsIndexedRead=\"%s\" />\n" % (n+1,rd['num_cycles'],rd['is_indexed_read'])
        xml += "    </Reads>\n"
        # Flowcell layout
        xml += "    <FlowcellLayout LaneCount=\"%s\" SurfaceCount=\"2\" SwathCount=\"1\" TileCount=\"%s\" />\n"  % (nlanes,tilecount)
        # AlignToPhiX
        if align_to_phix:
            xml += "    <AlignToPhiX>\n"
            for i in range(nlanes):
                xml += "      <Lane>%s</Lane>\n" % (i+1)
            xml += "    </AlignToPhiX>\n"
        # Footer
        xml += u"""  </Run>
</RunInfo>"""
        return xml
    @staticmethod
    def miseq(run_name):
        return RunInfoXml.create(run_name,"y101,I8,I8,y101",1,19)
    @staticmethod
    def hiseq(run_name):
        return RunInfoXml.create(run_name,"y101,I8,I8,y101",8,16,
                                 align_to_phix=True)
    @staticmethod
    def nextseq(run_name):
        return RunInfoXml.create(run_name,"y76,I6,y76",4,12)

class RunParametersXml:
    """
    Class with example RunParameters.xml files

    There is no need to instantiate this class; to create
    a mock RunParameters.xml file do e.g.:

    >>> with open('RunParameters.xml','wt') as fp:
    ...     fp.write(RunParametersXml.create(
    ...         '151125_AB12345_001_CD256X',
    ...         'Y51,I8,I8,Y51'))

    Different versions of the RunParameters file can be
    generated by explicitly specifying the ``rta_version``,
    where the major version can be either '2' (the default)
    or '3'.
    """
    @staticmethod
    def create(run_name,bases_mask,nlanes=1,flowcell_mode='SP',
               rta_version="2"):
        # Construct the XML
        return RunParametersXml.make_xml(rta_version=rta_version,
                                         run_name=run_name,
                                         bases_mask=bases_mask,
                                         nlanes=nlanes,
                                         flowcell_mode=flowcell_mode)

    def make_xml(rta_version,run_name,bases_mask,nlanes,flowcell_mode):
        # Get major RTA version
        version = str(rta_version)
        if version.lower().startswith('v'):
            version = version[1:]
        version = version.split('.')[0]
        # Split the run name
        items = run_name.split("_")
        try:
            datestamp = items[0]
        except IndexError:
            datestamp = "171018"
        try:
            instrument = items[1]
        except IndexError:
            instrument = "S00001"
        try:
            run_number = items[2]
        except IndexError:
            run_number = "1"
        try:
            flowcell = items[3]
        except IndexError:
            flowcell = "XXXXABCD1"
        if flowcell[0] in ('A','B',):
            flowcell = flowcell[1:]
        # Process bases mask
        reads = []
        for item in bases_mask.split(","):
            is_indexed_read = ('Y' if item.upper().startswith("I")
                               else 'N')
            num_cycles = item[1:]
            reads.append({ 'is_indexed_read': is_indexed_read,
                           'num_cycles': num_cycles})
        # Version 2
        if version == '2':
            read_data = []
            i = 0
            for r in reads:
                if not r['is_indexed_read']:
                    i += 1
                    read_data.append(
                        "    <Read{read_num}>{cycles}</Read{read_num}>".format(
                            read_num=i,
                            cycles=r['num_cycles']))
            i = 0
            for r in reads:
                if r['is_indexed_read']:
                    i += 1
                    read_data.append(
                        "    <Index{read_num}Read>{cycles}</Index{read_num}Read>".format(
                            read_num=i,
                            cycles=r['num_cycles']))
            xml = u"""<RunParameters xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <RunParametersVersion>Version_2_0_0</RunParametersVersion>
  <Setup>
    <SupportMultipleSurfacesInUI>true</SupportMultipleSurfacesInUI>
    <ApplicationVersion>2.2.1.9</ApplicationVersion>
    <ApplicationName>MiniSeq Control Software</ApplicationName>
    <NumTilesPerSwath>10</NumTilesPerSwath>
    <NumSwaths>3</NumSwaths>
    <NumLanes>{lanes}</NumLanes>
{read_data}
    <SectionPerLane>1</SectionPerLane>
    <LanePerSection>1</LanePerSection>
  </Setup>
  <RunID>{run_name}</RunID>
  <InstrumentID>{instrument}</InstrumentID>
  <RunNumber>{run_number}</RunNumber>
  <RTAVersion>2.11.4.0</RTAVersion>
  <SystemSuiteVersion>2.2.1.9</SystemSuiteVersion>
  <LocalRunManagerVersion>2.4.1.2636</LocalRunManagerVersion>
  <RecipeVersion>2.1.0.13</RecipeVersion>
  <FirmwareVersion>r.1.0.4</FirmwareVersion>
  <FlowCellRfidTag>
    <SerialNumber>{flowcell}</SerialNumber>
    <PartNumber>12345678</PartNumber>
    <LotNumber>23456789</LotNumber>
    <ExpirationDate>2022-04-08T00:00:00</ExpirationDate>
  </FlowCellRfidTag>
  <ReagentKitRfidTag>
    <SerialNumber>ML2133553-REAGT</SerialNumber>
    <PartNumber>23456789</PartNumber>
    <LotNumber>34567890</LotNumber>
    <ExpirationDate>2021-11-11T00:00:00</ExpirationDate>
  </ReagentKitRfidTag>
  <FlowCellSerial>{flowcell}</FlowCellSerial>
  <ReagentKitSerial>ML1234567-REAGT</ReagentKitSerial>
  <ExperimentName>Run {run_number}</ExperimentName>
  <LibraryID />
  <RunDescription />
  <Chemistry>Sequencer Chemistry</Chemistry>
  <SelectedTiles>
    <Tile>1_11102</Tile>
    <Tile>1_21102</Tile>
  </SelectedTiles>
  <RunFolder>D:\\Illumina\\Sequencing Temp\\{run_name}\\</RunFolder>
  <PreRunFolderRoot>D:\Illumina\PreRun</PreRunFolderRoot>
  <PreRunFolder>D:\\Illumina\\PreRun\\{instrument}_2022-11-21__07_45_10</PreRunFolder>
  <OutputFolder>D:\\Illumina\\Output\\{run_name}\\</OutputFolder>
  <RecipeFolder>C:\\Program Files\\Illumina\\Control Software\\Recipe\\High\\v1</RecipeFolder>
  <SimulationFolder />
  <RunStartDate>{datestamp}</RunStartDate>
  <FocusMethod>IXFocus</FocusMethod>
  <SurfaceToScan>Both</SurfaceToScan>
  <SaveFocusImages>false</SaveFocusImages>
  <SaveScanImages>false</SaveScanImages>
  <SelectiveSave>true</SelectiveSave>
  <IsPairedEnd>true</IsPairedEnd>
  <CustomReadOnePrimer>BP10</CustomReadOnePrimer>
  <CustomReadTwoPrimer>BP11</CustomReadTwoPrimer>
  <CustomIndexPrimer>BP14</CustomIndexPrimer>
  <CustomIndexTwoPrimer>BP14</CustomIndexTwoPrimer>
  <UsesCustomReadOnePrimer>false</UsesCustomReadOnePrimer>
  <UsesCustomReadTwoPrimer>false</UsesCustomReadTwoPrimer>
  <UsesCustomIndexPrimer>false</UsesCustomIndexPrimer>
  <UsesCustomIndexTwoPrimer>false</UsesCustomIndexTwoPrimer>
  <RunSetupType>LocalRunManager</RunSetupType>
  <UsesCustomIndexTwoPrimer>false</UsesCustomIndexTwoPrimer>
  <RunSetupType>LocalRunManager</RunSetupType>
  <RunMode>PerformanceDataRunMonitoringAndStorage</RunMode>
  <ComputerName>WIN-COMPUTER</ComputerName>
  <SequencingStarted>true</SequencingStarted>
  <PlannedRead1Cycles>76</PlannedRead1Cycles>
  <PlannedRead2Cycles>76</PlannedRead2Cycles>
  <PlannedIndex1ReadCycles>6</PlannedIndex1ReadCycles>
  <PlannedIndex2ReadCycles>0</PlannedIndex2ReadCycles>
  <IsRehyb>false</IsRehyb>
  <PurgeConsumables>true</PurgeConsumables>
  <MaxCyclesSupportedByReagentKit>168</MaxCyclesSupportedByReagentKit>
  <ExtraCyclesSupportedByReagentKit>0</ExtraCyclesSupportedByReagentKit>
  <RunStartTimeStamp>2022-11-25T09:01:16.8032505+00:00</RunStartTimeStamp>
  <CopyServiceRunId>19BCC157672C3A12</CopyServiceRunId>
  <LibPrepKitName>TruSeq LT</LibPrepKitName>
  <LocalRunManagerRunId>1234</LocalRunManagerRunId>
  <LocalRunManagerUserName />
  <ModuleName>GenerateFastQWorkflow</ModuleName>
  <ModuleVersion>2.0.1.17</ModuleVersion>
  <StateDescription />
  <BaseSpaceUserName>anony.muss@example.org</BaseSpaceUserName>
  <BaseSpaceRunId>567890123</BaseSpaceRunId>
</RunParameters>
""".format(lanes=nlanes,
           run_name=run_name,
           instrument=instrument,
           datestamp=datestamp,
           run_number=run_number,
           flowcell=flowcell,
           read_data='\n'.join(read_data))
        # Version 3
        if version == '3':
            read_data = []
            i = 0
            for r in reads:
                if not r['is_indexed_read']:
                    i += 1
                    read_data.append(
                        "  <Read{read_num}NumberOfCycles>{cycles}</Read{read_num}NumberOfCycles>".format(
                            read_num=i,
                            cycles=r['num_cycles']))
            i = 0
            for r in reads:
                if r['is_indexed_read']:
                    i += 1
                    read_data.append(
                        "  <IndexRead{read_num}NumberOfCycles>{cycles}</IndexRead{read_num}NumberOfCycles>".format(
                            read_num=i,
                            cycles=r['num_cycles']))
            xml = """<RunParameters xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <Surface>Both</Surface>
  <ReadType>PairedEnd</ReadType>
  <Side>B</Side>
{read_data}
  <PlannedRead1Cycles>59</PlannedRead1Cycles>
  <PlannedRead2Cycles>59</PlannedRead2Cycles>
  <PlannedIndex1ReadCycles>10</PlannedIndex1ReadCycles>
  <PlannedIndex2ReadCycles>10</PlannedIndex2ReadCycles>
  <RunNumber>38</RunNumber>
  <RtaVersion>v3.4.4</RtaVersion>
  <RecipeVersion>1.7.5</RecipeVersion>
  <ExperimentName>Run{run_number}</ExperimentName>
  <RfidsInfo>
    <FlowCellSerialBarcode>{flowcell}</FlowCellSerialBarcode>
    <FlowCellPartNumber>20023456</FlowCellPartNumber>
    <FlowCellLotNumber>20678901</FlowCellLotNumber>
    <FlowCellExpirationdate>08/08/2023 00:00:00</FlowCellExpirationdate>
    <FlowCellStartDate>11/24/2022 11:20:00</FlowCellStartDate>
    <FlowCellNumberOfReuseRemaining>1</FlowCellNumberOfReuseRemaining>
    <FlowCellSupportedModes>LTWashOnly;SP</FlowCellSupportedModes>
    <FlowCellMode>{flowcell_mode}</FlowCellMode>
    <FlowCellConsumableVersion>1</FlowCellConsumableVersion>
    <FlowCellRssi>3</FlowCellRssi>
    <LibraryTubeSerialBarcode>NV0678901-LIB</LibraryTubeSerialBarcode>
    <LibraryTubeSupportedModes>Universal</LibraryTubeSupportedModes>
    <LibraryTubePartNumber>20005678</LibraryTubePartNumber>
    <LibraryTubeLotNumber>1000012345</LibraryTubeLotNumber>
    <LibraryTubeExpirationdate>12/31/2169 00:00:00</LibraryTubeExpirationdate>
    <LibraryTubeStartDate>11/24/2022 11:20:00</LibraryTubeStartDate>
    <LibraryTubeRssi>4</LibraryTubeRssi>
    <SbsSerialBarcode>NV4567890-RGSBS</SbsSerialBarcode>
    <SbsSupportedModes>S2;S1;SP</SbsSupportedModes>
    <SbsPartNumber>20034567</SbsPartNumber>
    <SbsLotNumber>20678901</SbsLotNumber>
    <SbsExpirationdate>07/24/2023 00:00:00</SbsExpirationdate>
    <SbsStartDate>11/24/2022 11:20:00</SbsStartDate>
    <SbsCycleKit>138</SbsCycleKit>
    <SbsNumberOfCyclesRemaining>0</SbsNumberOfCyclesRemaining>
    <SbsNumberOfCyclesSupported>138</SbsNumberOfCyclesSupported>
    <SbsConsumableVersion>3</SbsConsumableVersion>
    <SbsRssi>4</SbsRssi>
    <ClusterSerialBarcode>NV4567890-RGCPE</ClusterSerialBarcode>
    <ClusterSupportedModes>SP</ClusterSupportedModes>
    <ClusterPartNumber>20034567</ClusterPartNumber>
    <ClusterLotNumber>20678901</ClusterLotNumber>
    <ClusterExpirationdate>06/08/2023 00:00:00</ClusterExpirationdate>
    <ClusterStartDate>11/24/2022 11:20:00</ClusterStartDate>
    <ClusterCycleKit>567</ClusterCycleKit>
    <ClusterNumberOfCyclesRemaining>407</ClusterNumberOfCyclesRemaining>
    <ClusterRssi>5</ClusterRssi>
    <BufferSerialBarcode>NV5678901-BUFFR</BufferSerialBarcode>
    <BufferSupportedModes>S2;S1;SP</BufferSupportedModes>
    <BufferPartNumber>20012345</BufferPartNumber>
    <BufferLotNumber>50000123</BufferLotNumber>
    <BufferExpirationdate>05/06/2023 00:00:00</BufferExpirationdate>
    <BufferNumberOfCyclesRemaining>192</BufferNumberOfCyclesRemaining>
    <BufferStartDate>11/24/2022 11:20:00</BufferStartDate>
    <BufferRssi>4</BufferRssi>
  </RfidsInfo>
  <RecipeFilePath>C:\Program Files\Illumina\Control Software\Recipe</RecipeFilePath>
  <SamplesheetFile>C:\\Users\sbsadmin\Desktop\sample sheet\Sample Sheet Run {run_number}.csv</SamplesheetFile>
  <UsedLimsSetup>false</UsedLimsSetup>
  <CeLinuxRunFolder>/ilmn/outputfolder/{run_name}/</CeLinuxRunFolder>
  <RtaRawRunFolder>/ilmn/outputfolder</RtaRawRunFolder>
  <CeMountRunFolder>Z:\outputfolder\{run_name}\</CeMountRunFolder>
  <OutputRunFolder>X:\{run_name}\</OutputRunFolder>
  <OutputRootFolder>X:\</OutputRootFolder>
  <SbcRunFolder>C:\ProgramData\Illumina\{run_name}\</SbcRunFolder>
  <PreRunFolder>C:\ProgramData\Illumina\RunSetupLogs\{instrument}_2022-11-24__11_01_09_SideB</PreRunFolder>
  <RunStartDate>{datestamp}</RunStartDate>
  <RunId>{run_name}</RunId>
  <UseBaseSpace>true</UseBaseSpace>
  <UseBaseSpaceMonitoringAndStorage>true</UseBaseSpaceMonitoringAndStorage>
  <BaseSpaceRunId>248358124</BaseSpaceRunId>
  <BaseSpaceEnvironment>use1-prod</BaseSpaceEnvironment>
  <BaseSpaceDomain />
  <Autocenter>true</Autocenter>
  <BiDirectionalScanning>true</BiDirectionalScanning>
  <UseCustomRecipe>false</UseCustomRecipe>
  <UseCustomRead1Primer>false</UseCustomRead1Primer>
  <UseCustomRead2Primer>false</UseCustomRead2Primer>
  <UseCustomIndexRead1Primer>false</UseCustomIndexRead1Primer>
  <IsRehyb>false</IsRehyb>
  <InstrumentName>{instrument}</InstrumentName>
  <PlatformType>HighThroughput</PlatformType>
  <Application>Control Software</Application>
  <ApplicationVersion>1.7.5</ApplicationVersion>
  <Build>27</Build>
  <FirmwareVersions>
    <FirmwareVersion>
      <Board>Random Board</Board>
      <Version>seq_randome@Sequencer_1.26.1</Version>
    </FirmwareVersion>
  </FirmwareVersions>
  <SendIlluminaHealthData>true</SendIlluminaHealthData>
  <UcsRunId>19AC0B9F304ADFF4</UcsRunId>
  <UcsVersion>1.6.3.1575</UcsVersion>
  <RunSetupMode>Manual</RunSetupMode>
  <WorkflowType>Standard</WorkflowType>
</RunParameters>
""".format(run_name=run_name,
           instrument=instrument,
           datestamp=datestamp,
           run_number=run_number,
           flowcell=flowcell,
           flowcell_mode=flowcell_mode,
           read_data='\n'.join(read_data))
        return xml

#######################################################################
# Class definitions
#######################################################################

class MockSampleSheet(SampleSheet):
    """
    Class for mocking up sample sheet files

    Example making an IEM-style sample sheet:

    >>> s = MockSampleSheet(fmt='IEM',has_lanes=False,dual_index=True)
    >>> s.set_header(Date="08/19/2016",Assay="Nextera XT")
    >>> s.set_reads(150,150)
    >>> s.set_settings(Adapter="AGATCGG",AdapterRead2="")
    >>> s.append_line(Sample_ID="Sample1",
    ...               Sample_Name="Sample1",
    ...               I7_Index_ID="D701",
    ...               index="CGTGTAGG",
    ...               I5_Index_ID="D501",
    ...               index2="GACCTGTA")
    >>> s.append_line(Sample_ID="Sample2",
    ...               Sample_Name="Sample2",
    ...               I7_Index_ID="D702",
    ...               index="CGTGTAGG",
    ...               I5_Index_ID="D502",
    ...               index2="ATGTAACT")
    >>> io.open("SampleSheet.csv","wt").write(s.show())

    Example making a CASAVA-style sample sheet:

    >>> s = MockSampleSheet(fmt="CASAVA",has_lanes=True)
    >>> s.append_line(FCID="ABC001XX",
    ...               Lane=1,
    ...               SampleID="884-1",
    ...               SampleRef="PB-881-1",
    ...               Index="AGTCAA",
    ...               Description="RNA-seq",
    ...               SampleProject="AR")
    >>> io.open("SampleSheet.csv","wt").write(s.show())

    """
    def __init__(self,fmt='IEM',has_lanes=False,dual_index=True,
                 quote_values=False,pad=False):
        """
        Create a new MockSampleSheet instance

        Arguments:
          fmt (str): either 'IEM' or 'CASAVA'
          has_lanes (boolean): if True then the output sample sheet
            will include a 'Lane' field
          dual_index (boolean): if True then IEM-style sample sheet
            will have dual index fields (not relevant for CASAVA-style)
          quote_values (boolean): if True then output data values will
            be surrounded by double quotes (default is not to quote
            values)
          pad (boolean): if True then output sample sheet will have
            additional commas on each line (simulates output from
            Excel) (default is not to pad output)

        """
        # Store argument values
        self._format = fmt
        self._has_lanes = has_lanes
        self._dual_index = dual_index
        # Output formatting
        self.quote_values = quote_values
        self.pad = pad
        # Instantiate the base object
        SampleSheet.__init__(self,fp=io.StringIO(self._template()))
        # Initialise additional sections for IEM
        if self._format == 'IEM':
            self.set_header(IEMFileVersion=4,
                            Date="11/23/2015",
                            Workflow="GenerateFASTQ",
                            Application="FASTQ Only",
                            Assay="TruSeq HT",
                            Description="",
                            Chemistry="Amplicon")
            self.set_reads(101,101)
            self.set_settings(ReverseComplement=0,
                              Adapter="AGATCGGAAGAGCACACGTCTGAACTCCAGTCA",
                              AdapterRead2="AGATCGGAAGAGCACACGTCTGAACTCCAGTCA")

    def _template(self):
        """
        Return template for initialising sample sheet
        """
        if self._format == 'CASAVA':
            cols = "SampleID,SampleRef,Index,Description,Control,Recipe,Operator,SampleProject"
            if self._has_lanes:
                cols = "Lane," + cols
            cols = "FCID," + cols
        elif self._format == 'IEM':
            if self._dual_index:
                cols = "Sample_ID,Sample_Name,Sample_Plate,Sample_Well,I7_Index_ID,index,I5_Index_ID,index2,Sample_Project,Description"
            else:
                cols = "Sample_ID,Sample_Name,Sample_Plate,Sample_Well,I7_Index_ID,index,Sample_Project,Description"
            if self._has_lanes:
                cols = "Lane," + cols
            cols = "[Data]\n" + cols
        return cols

    def set_header(self,**kws):
        """
        Set items in the [Header] section

        Supply keyword=value pairs to set the values for items
        in the sample sheet header

        For example:

        >>> s.set_header(Date="08/19/2016",Assay="Nextera XT")

        """
        new_header = OrderedDictionary()
        items = ('IEMFileVersion',
                 'Date',
                 'Workflow',
                 'Application',
                 'Assay',
                 'Description',
                 'Chemistry')
        for item in items:
            if item in kws:
                new_header[item] = kws[item]
            elif item in self._header:
                new_header[item] = self._header[item]
        for item in kws:
            if item not in items:
                new_header[item] = kws[item]
        self._header = new_header

    def set_reads(self,read1,read2=None):
        """
        Set values in the [Reads] section

        Supply length of read1 and (optionally) read2

        For example:

        >>> s.set_reads(150,150)

        """
        self._reads = [str(read1)]
        if read2 is not None:
            self._reads.append(str(read2))

    def set_settings(self,**kws):
        """
        Set items in the [Settings] section

        Supply keyword=value pairs to set the values for items
        in the sample sheet header

        For example:

        >>> s.set_settings(Adapter="AGATCGG",AdapterRead2="")

        """
        new_settings = OrderedDictionary()
        items = ('ReverseComplement',
                 'Adapter',
                 'AdapterRead2')
        for item in items:
            if item in kws:
                new_settings[item] = kws[item]
            elif item in self._settings:
                new_settings[item] = self._settings[item]
        self._settings = new_settings

    def append_line(self,**kws):
        """
        Add a line to the sample sheet

        For IEM-style sample sheets the lines are appended to
        the [Data] section.

        Supply keyword=value pairs to set the values for items
        in the line; the keywords should match the names of
        header items.

        For example:

        >>> s.s.append_line(Sample_ID="SMPL1",Sample_Project="PRJ1")

        """
        line = []
        for item in self.data.header():
            if item in kws:
                value = kws[item]
                if self.quote_values:
                    value = '"%s"' % value
            else:
                value = ''
            line.append(value)
        self.data.append(data=line)

    def show(self,fmt=None):
        """
        Construct and return sample sheet contents

        """
        output = SampleSheet.show(self,fmt=fmt)
        if self.pad:
            ncols = len(self.data.header())
            padded_output = []
            for line in output.split('\n'):
                ncols_in_line = len(line.split(','))
                if ncols_in_line < ncols:
                    line = line + ','*(ncols-ncols_in_line-1)
                padded_output.append(line)
            output = '\n'.join(padded_output)
        return output

class MockIlluminaRun:
    """
    Utility class for creating mock Illumina sequencer output dirctories

    Example usage:

    >>> mockrun = MockIlluminaRun('151125_AB12345_001_CD256X','miseq')
    >>> mockrun.create()

    To delete the physical directory structure when finished:

    >>> mockrun.remove()

    """
    def __init__(self,name,platform,top_dir=None,
                 ntiles=None,bases_mask=None,
                 sample_sheet_content=None,
                 flowcell_mode=None,complete=True):
        """
        Create a new MockIlluminaRun instance

        By default the content of the generated directory structure
        is determined exclusively by the choice of platform;
        however these can be tuned by specifying alternative values
        for the 'ntiles', 'bases_mask' and 'sample_sheet_content'
        arguments.

        Arguments:
          name (str): name for the run (used as top-level dir)
          platform (str): sequencing platform e.g. 'miseq', 'hiseq'
            'nextseq'
          top_dir (str): optionally specify a parent directory for
            the mock run (default is the current working directory)
          ntiles (int): optionally specify the number of tiles
          bases_mask (str): optionally specify a bases mask string
            e.g. "y101,I6,y101"
          sample_sheet_content (str): optionally specify content to
            be used to generate a sample sheet
          flowcell_mode (str): optionally specify the flow cell
            mode to be included in the run parameters
          complete (bool): default is to include the appropriate
            run completion files in the mock run; set to False to
            omit these files
        """
        self._created = False
        self._name = name
        if top_dir is not None:
            self._top_dir = os.path.abspath(top_dir)
        else:
            self._top_dir = os.getcwd()
        self._platform = platform
        self._complete = bool(complete)
        # Set defaults for platform
        if self._platform == "miniseq":
            # MiniSeq
            self._nlanes = 1
            self._bcl_ext = '.bcl.bgzf'
            self._sample_sheet_content = None
            self._bases_mask = "y80,I6,y80"
            self._ntiles = 1 #158
            self._include_filter = True
            self._include_control = True
            self._include_bci = False
            self._include_cycles = True
            self._include_config = True
            self._include_sample_sheet = False
            self._flowcell_mode = None
            self._rta_version = "2.11.4.0"
            self._completion_files = get_run_completion_files("miniseq")
        elif self._platform == "miseq":
            # MISeq
            self._nlanes = 1
            self._bcl_ext = '.bcl'
            self._sample_sheet_content = SampleSheets.miseq
            self._bases_mask = "y101,I8,I8,y101"
            self._ntiles = 12 #158
            self._include_filter = True
            self._include_control = True
            self._include_bci = False
            self._include_cycles = True
            self._include_config = True
            self._include_sample_sheet = True
            self._flowcell_mode = None
            self._rta_version = "2.11.4.0"
            self._completion_files = get_run_completion_files("miseq")
        elif self._platform == "hiseq":
            # HISeq
            self._nlanes = 8
            self._bcl_ext = '.bcl.gz'
            self._sample_sheet_content = SampleSheets.hiseq
            self._bases_mask = "y101,I8,I8,y101"
            self._ntiles = 12 #1216
            self._include_filter = True
            self._include_control = True
            self._include_bci = False
            self._include_cycles = True
            self._include_config = True
            self._include_sample_sheet = True
            self._flowcell_mode = None
            self._rta_version = "2.11.4.0"
            self._completion_files = get_run_completion_files("hiseq")
        elif self._platform == "nextseq":
            # NextSeq
            self._nlanes = 4
            self._bcl_ext = '.bcl.bgzf'
            self._sample_sheet_content = None
            self._bases_mask = "y76,I6,y76"
            self._ntiles = 158
            self._include_filter = True
            self._include_control = False
            self._include_bci = True
            self._include_cycles = False
            self._include_config = False
            self._include_sample_sheet = False
            self._flowcell_mode = None
            self._rta_version = "2.11.4.0"
            self._completion_files = get_run_completion_files("nextseq")
        elif self._platform == "novaseq":
            # NovaSeq
            self._nlanes = 2
            self._bcl_ext = '.bcl.bgzf'
            self._sample_sheet_content = None
            self._bases_mask = "y76,I10,I10,y76"
            self._ntiles = 158
            self._include_filter = True
            self._include_control = False
            self._include_bci = True
            self._include_cycles = False
            self._include_config = False
            self._include_sample_sheet = False
            self._flowcell_mode = 'SP'
            self._rta_version = "v3.4.4"
            self._completion_files = get_run_completion_files("novaseq6000")
        else:
            raise Exception("Unrecognised platform: %s" %
                            self._platform)
        # Override defaults
        if ntiles is not None:
            self._ntiles = ntiles
        if sample_sheet_content is not None:
            self._sample_sheet_content = sample_sheet_content
        if bases_mask is not None:
            self._bases_mask = bases_mask
        if flowcell_mode is not None:
            self._flowcell_mode = flowcell_mode

    @property
    def name(self):
        """
        Name of the mock run
        """
        return self._name

    @property
    def bcl_ext(self):
        """
        Bcl file extension
        """
        return self._bcl_ext

    @property
    def ntiles(self):
        """
        Number of tiles
        """
        return self._ntiles

    @property
    def lanes(self):
        """
        List of lane numbers
        """
        return [l for l in range(1,self._nlanes+1)]

    @property
    def flowcell_mode(self):
        """
        Flowcell mode
        """
        return self._flowcell_mode

    @property
    def dirn(self):
        """
        Full path to the mock run directory
        """
        return os.path.join(self._top_dir,self._name)

    def _path(self,*dirs):
        """
        Internal: return path under run directory
        """
        dirs0 = [self.dirn]
        dirs0.extend(dirs)
        return os.path.join(*dirs0)

    def create(self):
        """
        Build and populate the directory structure

        Creates the directory structure on disk which has been defined
        within the MockIlluminaRun object.

        Invoke the 'remove' method to delete the directory structure.

        'create' raises an OSError exception if any part of the directory
        structure already exists.

        """
        # Create top level directory
        if os.path.exists(self.dirn):
            raise OSError("%s already exists" % self.dirn)
        else:
            mkdir(self.dirn)
            self._created = True
        # Get local copies of paramaters
        bases_mask = self._bases_mask
        bcl_ext = self._bcl_ext
        nlanes = self._nlanes
        ntiles = self._ntiles
        ncycles = 0
        for rd in bases_mask.split(','):
            ncycles += int(rd[1:])
        flowcell_mode = self._flowcell_mode
        rta_version = self._rta_version
        # Basic directory structure
        mkdir(self._path('Data'))
        mkdir(self._path('Data','Intensities'))
        mkdir(self._path('Data','Intensities','BaseCalls'))
        mkdir(self._path('InterOp'))
        # Lanes
        for i in range(1,nlanes+1):
            # .locs files
            mkdir(self._path('Data','Intensities','L%03d' % i))
            for j in range(1101,1101+ntiles):
                io.open(self._path('Data','Intensities','L%03d' % i,
                                   's_%d_%d.locs' % (i,j)),'wb+').close()
            # BaseCalls directory
            mkdir(self._path('Data','Intensities','BaseCalls',
                             'L%03d' % i))
            for j in range(1101,1101+ntiles):
                if self._include_control:
                    # Add .control files
                    io.open(self._path('Data',
                                       'Intensities',
                                       'BaseCalls',
                                       'L%03d' % i,
                                       's_%d_%d.control' % (i,j)),'wb+').close()
                if self._include_filter:
                    # Add .filter files
                    io.open(self._path('Data',
                                       'Intensities',
                                       'BaseCalls',
                                       'L%03d' % i,
                                       's_%d_%d.filter' % (i,j)),'wb+').close()
                if not self._include_cycles:
                    # No cycle subdirectores (e.g. 'C121.1')
                    # so put bcl files directory in lane directory
                    # This is the case for NextSeq
                    for j in range(1,ntiles+1):
                        io.open(self._path('Data',
                                           'Intensities',
                                           'BaseCalls',
                                           'L%03d' % i,
                                           '%04d%s' % (j,bcl_ext)),'wb+').close()
                    if self._include_bci:
                        # Add .bci files (e.g. NextSeq)
                        io.open(self._path('Data',
                                           'Intensities',
                                           'BaseCalls',
                                           'L%03d' % i,
                                           '%04d%s.bci' % (j,bcl_ext)),'wb+').close()
            # Cycles subdirectories
            if self._include_cycles:
                for k in range(1,ncycles+1):
                    mkdir(self._path('Data',
                                     'Intensities',
                                     'BaseCalls',
                                     'L%03d' % i,
                                     'C%d.1' % k))
                    for j in range(1101,1101+ntiles):
                        # .bcl files
                        io.open(self._path('Data',
                                           'Intensities',
                                           'BaseCalls',
                                           'L%03d' % i,
                                           'C%d.1' % k,
                                           's_%d_%d%s' % (i,j,bcl_ext)),
                                'wb+').close()
                        # .stats files
                        io.open(self._path('Data',
                                           'Intensities',
                                           'BaseCalls',
                                           'L%03d' % i,
                                           'C%d.1' % k,
                                           's_%d_%d.stats' % (i,j)),'wb+').close()
        # RunInfo.xml
        run_info_xml = RunInfoXml.create(self.name,
                                         bases_mask,
                                         nlanes)
        with io.open(self._path('RunInfo.xml'),'wt') as fp:
            fp.write(run_info_xml)
        # RunParameters.xml
        run_parameters_xml = RunParametersXml.create(
            self.name,
            bases_mask,
            nlanes=nlanes,
            flowcell_mode=flowcell_mode,
            rta_version=rta_version)
        with io.open(self._path('RunParameters.xml'),'wt') as fp:
            fp.write(run_parameters_xml)
        # SampleSheet.csv
        if self._include_sample_sheet and \
           self._sample_sheet_content is not None:
            with io.open(self._path('Data','Intensities','BaseCalls',
                                    'SampleSheet.csv'),'wt') as fp:
                fp.write(str(self._sample_sheet_content))
        # (Empty) config.xml files
        if self._include_config:
            io.open(self._path('Data','Intensities','config.xml'),'wb+').close()
            io.open(self._path('Data','Intensities','BaseCalls','config.xml'),
                    'wb+').close()
        # Run completion files (e.g. 'RTAComplete.txt' etc)
        if self._complete and self._completion_files:
            for f in self._completion_files:
                io.open(self._path(f),'wb+').close()

    def remove(self):
        """
        Delete the directory structure and contents

        This removes the directory structure from disk that has
        previously been created using the create method.

        """
        if self._created:
            shutil.rmtree(self.dirn)
            self._created = False

class MockIlluminaData:
    """Utility class for creating mock Illumina analysis data directories

    The MockIlluminaData class allows artificial Illumina analysis data
    directories to be defined, created and populated, and then destroyed.

    These artifical directories are intended to be used for testing
    purposes.

    Two styles of analysis directories can be produced: 'casava'-style
    aims to mimic that produced from the CASAVA and bcl2fastq 1.8
    processing software; 'bcl2fastq2' mimics that from the bcl2fastq
    2.* software.

    Basic example usage:

    >>> mockdata = MockIlluminaData('130904_PJB_XXXXX','casava')
    >>> mockdata.add_fastq('PJB','PJB1','PJB1_GCCAAT_L001_R1_001.fastq.gz')
    >>> ...
    >>> mockdata.create()

    This will make a CASAVA-style directory structure like:

    1130904_PJB_XXXXX/
        Unaligned/
            Project_PJB/
                Sample_PJB1/
                    PJB1_GCCAAT_L001_R1_001.fastq.gz
        ...

    Using:

    >>> mockdata = MockIlluminaData('130904_PJB_XXXXX','bcl2fastq2')
    >>> mockdata.add_fastq('PJB','PJB1','PJB1_S1_L001_R1_001.fastq.gz')

    will make a bcl2fast2-style directory structure like:

    1130904_PJB_XXXXX/
        Unaligned/
            PJB/
               PJB1_S1_L001_R1_001.fastq.gz
        ...

    NB if the sample name in the fastq file name differs from the supplied
    sample name then the sample name will be used to create an additional
    directory level, e.g.:

    >>> mockdata = MockIlluminaData('130904_PJB_XXXXX','bcl2fastq2')
    >>> mockdata.add_fastq('PJB','PJB2','PJB2_input_S1_L001_R1_001.fastq.gz')

    will create:

    1130904_PJB_XXXXX/
        Unaligned/
            PJB/
               PJB2/
                   PJB2_input_S1_L001_R1_001.fastq.gz
        ...

    (this replicates the situation for bcl2fastq v2 where Sample_ID and
    Sample_Name differ.)

    Multiple fastqs can be more easily added using e.g.:

    >>> mockdata.add_fastq_batch('PJB','PJB2','PJB1_GCCAAT',lanes=(1,4,5))

    which creates 3 fastq entries for sample PJB2, with lane numbers 1, 4
    and 5.

    Paired-end mock data can be created using the 'paired_end' flag
    when instantiating the MockIlluminaData object.

    To delete the physical directory structure when finished:

    >>> mockdata.remove()

    """
    def __init__(self,name,package,
                 unaligned_dir='Unaligned',
                 paired_end=False,
                 no_lane_splitting=False,
                 top_dir=None):
        """Create new MockIlluminaData instance

        Makes a new empty MockIlluminaData object.

        Arguments:
          name: name of the directory for the mock data
          package: name of the conversion software package to mimic (can
            be 'casava' or 'bcl2fastq2')
          unaligned_dir: directory holding the mock projects etc (default is
            'Unaligned')
          paired_end: specify whether mock data is paired end (True) or not
            (False) (default is False)
          no_lane_splitting: (bcl2fastq2 only) mimick output from bcl2fastq2
            run with --no-lane-splitting (i.e. fastq names don't contain
            lane numbers) (default is False)
          top_dir: specify a parent directory for the mock data (default is
            the current working directory)

        """
        self.__created = False
        self.__name = name
        if package not in ('casava','bcl2fastq2'):
            raise Exception("Unknown package '%s': cannot make mock output dir"
                            % package)
        self.__package = package
        self.__unaligned_dir = unaligned_dir
        self.__paired_end = paired_end
        if package == 'bcl2fastq2':
            self.__no_lane_splitting = no_lane_splitting
        else:
            self.__no_lane_splitting = False
        self.__undetermined_dir = 'Undetermined_indices'
        if top_dir is not None:
            self.__top_dir = os.path.abspath(top_dir)
        else:
            self.__top_dir = os.getcwd()
        self.__projects = {}

    @property
    def name(self):
        """Name of the mock data

        """
        return self.__name

    @property
    def package(self):
        """
        Software package output that is being mimicked

        """
        return self.__package

    @property
    def dirn(self):
        """Full path to the mock data directory

        """
        return os.path.join(self.__top_dir,self.__name)

    @property
    def unaligned_dir(self):
        """Full path to the unaligned directory for the mock data

        """
        return os.path.join(self.dirn,self.__unaligned_dir)

    @property
    def paired_end(self):
        """Whether or not the mock data is paired ended

        """
        return self.__paired_end

    @property
    def projects(self):
        """List of project names within the mock data

        """
        projects = []
        for project_name in self.__projects:
            if project_name.startswith('Project_'):
                projects.append(project_name.split('_')[1])
            else:
                projects.append(project_name)
        projects.sort()
        return projects

    @property
    def has_undetermined(self):
        """Whether or not undetermined indices are included

        """
        return (self.__undetermined_dir in self.__projects)

    def samples_in_project(self,project_name):
        """List of sample names associated with a specific project

        Arguments:
          project_name: name of a project

        Returns:
          List of sample names

        """
        project = self.__projects[self.__project_dir(project_name)]
        samples = []
        for sample_name in project:
            if sample_name.startswith('Sample_'):
                samples.append(sample_name.split('_')[1])
            else:
                samples.append(sample_name)
        samples.sort()
        return samples

    def fastqs_in_sample(self,project_name,sample_name):
        """List of fastq names associated with a project/sample pair

        Arguments:
          project_name: name of a project
          sample_name: name of a sample

        Returns:
          List of fastq names.

        """
        project_dir = self.__project_dir(project_name)
        sample_dir = self.__sample_dir(sample_name)
        return self.__projects[project_dir][sample_dir]

    def __project_dir(self,project_name):
        """Internal: convert project name to internal representation

        Project names which are prepended with "Project_" will have this
        part removed.

        Arguments:
          project_name: name of a project

        Returns:
          Canonical project name for internal storage.

        """
        if project_name.startswith('Project_'):
            return project_name[8:]
        else:
            return project_name

    def __sample_dir(self,sample_name):
        """Internal: convert sample name to internal representation

        Sample names which are prepended with "Sample_" will have this
        part removed.

        Arguments:
          sample_name: name of a sample

        Returns:
          Canonical sample name for internal storage.

        """
        if sample_name.startswith('Sample_'):
            return sample_name[7:]
        else:
            return sample_name

    def add_project(self,project_name):
        """Add a project to the MockIlluminaData instance

        Defines a project within the MockIlluminaData structure.
        Note that any leading 'Project_' is ignored i.e. the project
        name is taken to be the remainder of the name.

        No error is raised if the project already exists.

        Arguments:
          project_name: name of the new project

        Returns:
          Dictionary object corresponding to the project.

        """
        project_dir = self.__project_dir(project_name)
        if project_dir not in self.__projects:
            self.__projects[project_dir] = {}
        return self.__projects[project_dir]

    def add_sample(self,project_name,sample_name):
        """Add a sample to a project within the MockIlluminaData instance

        Defines a sample with a project in the MockIlluminaData
        structure. Note that any leading 'Sample_' is ignored i.e. the
        sample name is taken to be the remainder of the name.

        If the parent project doesn't exist yet then it will be
        added automatically; no error is raised if the sample already
        exists.

        Arguments:
          project_name: name of the parent project
          sample_name: name of the new sample

        Returns:
          List object corresponding to the sample.

        """
        project = self.add_project(project_name)
        sample_dir = self.__sample_dir(sample_name)
        if sample_dir not in project:
            project[sample_dir] = []
        return project[sample_dir]

    def add_fastq(self,project_name,sample_name,fastq):
        """Add a fastq to a sample within the MockIlluminaData instance

        Defines a fastq within a project/sample pair in the MockIlluminaData
        structure.

        NOTE: it is recommended to use add_fastq_batch, which offers more
        flexibility and automatically maintains consistency e.g. when
        mocking a paired end data structure.

        Arguments:
          project_name: parent project
          sample_name: parent sample
          fastq: name of the fastq to add

        """
        sample = self.add_sample(project_name,sample_name)
        sample.append(fastq)
        sample.sort()

    def add_fastq_batch(self,project_name,sample_name,fastq_base,fastq_ext='fastq.gz',
                        lanes=(1,),reads=None):
        """Add a set of fastqs within a sample

        This method adds a set of fastqs within a sample with a single
        invocation, and is intended to simulate the situation where there
        are multiple fastqs due to paired end sequencing and/or sequencing
        of the sample across multiple lanes.

        The fastq names are constructed from a base name (e.g. 'PJB-1_GCCAAT'),
        plus a list/tuple of lane numbers. One fastq will be added for each
        lane number specified, e.g.:

        >>> d.add_fastq_batch('PJB','PJB-1','PJB-1_GCCAAT',lanes=(1,4,5))

        will add PJB-1_GCCAAT_L001_R1_001, PJB-1_GCCAAT_L004_R1_001 and
        PJB-1_GCCAAT_L005_R1_001 fastqs.

        If the MockIlluminaData object was created with the paired_end flag
        set to True then matching R2 fastqs will also be added.

        If the MockIlluminaData object was created with the no_lane_splitting
        flag set to True and the package as 'bcl2fastq' then the 'lanes'
        specification will be ignored and the fastq names will not contain
        lane identifiers.

        Arguments:
          project_name: parent project
          sample_name: parent sample
          fastq_base: base name of the fastq name i.e. just the sample name
            and barcode sequence (e.g. 'PJB-1_GCCAAT')
          fastq_ext: file extension to use (optional, defaults to 'fastq.gz')
          lanes: list, tuple or iterable with lane numbers (optional,
            defaults to (1,))
          reads: list, tuple or iterable with reads to make (optional,
            defaults to ('R1') for single end and ('R1','R2') for paired
            end)

        """
        if reads is None:
            if self.__paired_end:
                reads = ('R1','R2')
            else:
                reads = ('R1',)
        if not self.__no_lane_splitting:
            # Include explicit lane information
            for lane in lanes:
                for read in reads:
                    fastq = "%s_L%03d_%s_001.%s" % (fastq_base,
                                                    lane,read,
                                                    fastq_ext)
                    self.add_fastq(project_name,sample_name,fastq)
        else:
            # Replicate output from bcl2fastq --no-lane-splitting
            for read in reads:
                fastq = "%s_%s_001.%s" % (fastq_base,
                                          read,
                                          fastq_ext)
                self.add_fastq(project_name,sample_name,fastq)

    def add_undetermined(self,lanes=(1,),reads=None):
        """Add directories and files for undetermined reads

        This method adds a set of fastqs for any undetermined reads from
        demultiplexing.

        Arguments:
          lanes: list, tuple or iterable with lane numbers (optional,
            defaults to (1,))
          reads: list, tuple or iterable with reads to make (optional,
            defaults to ('R1') for single end and ('R1','R2') for paired
            end)

        """
        if not self.__no_lane_splitting:
            for lane in lanes:
                sample_name = "lane%d" % lane
                if self.package == 'casava':
                    # CASAVA-style naming
                    fastq_base = "lane%d_Undetermined" % lane
                elif self.package == 'bcl2fastq2':
                    # bcl2fastq2-style naming
                    fastq_base = "Undetermined_S0"
                self.add_sample(self.__undetermined_dir,sample_name)
                self.add_fastq_batch(self.__undetermined_dir,sample_name,
                                     fastq_base,lanes=(lane,),reads=reads)
        else:
            sample_name = "undetermined"
            fastq_base = "Undetermined_S0"
            self.add_sample(self.__undetermined_dir,sample_name)
            self.add_fastq_batch(self.__undetermined_dir,sample_name,
                                 fastq_base,lanes=None,reads=reads)

    def create(self,force_sample_dir=False):
        """Build and populate the directory structure

        Creates the directory structure on disk which has been defined
        within the MockIlluminaData object.

        Invoke the 'remove' method to delete the directory structure.

        The contents of the MockIlluminaData object can be modified
        after the directory structure has been created, but changes will
        not be reflected on disk. Instead it is necessary to first
        remove the directory structure, and then re-invoke the create
        method.

        create raises an OSError exception if any part of the directory
        structure already exists.

        Arguments:
          force_sample_dir (bool): if True then for bcl2fastq-style
            output, always insert a "sample" subdirectory grouping
            Fastqs for each sample, even if it wouldn't normally be
            created (default is to only add sample subdirectory if
            sample name differs from sample ID)

        """
        # Create top level directory
        if os.path.exists(self.dirn):
            raise OSError("%s already exists" % self.dirn)
        else:
            mkdir(self.dirn)
            self.__created = True
        # "Unaligned" directory
        mkdir(self.unaligned_dir)
        if self.package == 'casava':
            self._populate_casava()
        elif self.package == 'bcl2fastq2':
            self._populate_bcl2fastq2(force_sample_dir=force_sample_dir)

    def _populate_casava(self):
        """
        Populate the MockIlluminaData structure in the style of CASAVA

        """
        # Populate with projects, samples etc
        for project_name in self.__projects:
            if project_name == self.__undetermined_dir:
                project_dirn = os.path.join(self.unaligned_dir,project_name)
            else:
                project_dirn = os.path.join(self.unaligned_dir,
                                            "Project_%s" % project_name)
            mkdir(project_dirn)
            for sample_name in self.__projects[project_name]:
                sample_dirn = os.path.join(project_dirn,
                                           "Sample_%s" % sample_name)
                mkdir(sample_dirn)
                for fastq in self.__projects[project_name][sample_name]:
                    fq = os.path.join(sample_dirn,fastq)
                    self._touch(fq)

    def _populate_bcl2fastq2(self,force_sample_dir=False):
        """
        Populate the MockIlluminaData structure in the style of bcl2fastq2

        Arguments:
          force_sample_dir (bool): if True then always insert a
            "sample" subdirectory grouping Fastqs for each sample,
            even if it wouldn't normally be created (default is
            to only add sample subdirectory if sample name differs
            from sample ID)

        """
        for project_name in self.__projects:
            if project_name == self.__undetermined_dir:
                project_dirn = self.unaligned_dir
            else:
                project_dirn = os.path.join(self.unaligned_dir,project_name)
            mkdir(project_dirn)
            for sample_name in self.__projects[project_name]:
                fastqs = []
                for fastq in self.__projects[project_name][sample_name]:
                    # Check if sample name matches that for fastq
                    fq_sample_name = IlluminaFastq(fastq).sample_name
                    if (force_sample_dir or fq_sample_name != sample_name) and \
                       fq_sample_name != 'Undetermined':
                        # Create an intermediate directory
                        sample_dirn = os.path.join(project_dirn,sample_name)
                        mkdir(sample_dirn)
                    else:
                        sample_dirn = project_dirn
                    # Check for leading directory on fastq name
                    if os.path.dirname(fastq):
                        leading_dir = os.path.join(sample_dirn,
                                                   os.path.dirname(fastq))
                        mkdir(leading_dir)
                    # "Touch" the file (i.e. creates an empty file)
                    fq = os.path.join(sample_dirn,fastq)
                    self._touch(fq)
                    fastqs.append(os.path.basename(fastq))
                # Update the list of fastqs
                self.__projects[project_name][sample_name] = fastqs
            # Add 'Reports' and 'Stats' directories
            for name in ('Reports','Stats',):
                dirn = os.path.join(self.unaligned_dir,name)
                mkdir(dirn)

    def _touch(self,f):
        """Internal: create empty file
        """
        if f.endswith(".gz"):
            # Make empty gzipped file
            with gzip.open(f,'wb') as fp:
                fp.write(b"")
        else:
            # Make regular empty file
            with io.open(f,'wb') as fp:
                fp.write(b"")

    def remove(self):
        """Delete the directory structure and contents

        This removes the directory structure from disk that has
        previously been created using the create method.

        """
        if self.__created:
            shutil.rmtree(self.dirn)
            self.__created = False

    def __repr__(self):
        """Implement __repr__ for debug purposes
        """
        if not self.__created:
            return ("<%s: not created>" % self.dirn)
        rep = []
        for d in os.walk(self.dirn):
            for d1 in d[1]:
                rep.append(os.path.join(d[0],d1))
            for f in d[2]:
                rep.append(os.path.join(d[0],f))
        return '\n'.join(sorted(rep))

def mockSTAR(argv,unmapped_output=False):
    """
    Driver function for a "mock" STAR executable

    The mock executable should be a file with the
    following content:

    ::

        #!/bin/bash
        export PYTHONPATH=%s:$PYTHONPATH
        python -c "import sys ; from bcftbx.mock import mockSTAR ; mockSTAR(sys.argv[1:],unmapped_output=%s)" $@

    When executed it produces  a single output
    (ReadsPerGene.out.tab file).

    Arguments:
      argv (list): command line to be used as input
      unmapped_output (bool): if True then produce
        mock "unmapped" output
    """
    p = argparse.ArgumentParser(argv)
    p.add_argument('--runMode',action="store")
    p.add_argument('--genomeLoad',action="store")
    p.add_argument('--genomeDir',action="store")
    p.add_argument('--readFilesIn',action="store",nargs='+')
    p.add_argument('--quantMode',action="store")
    p.add_argument('--outSAMtype',action="store",nargs=2)
    p.add_argument('--outSAMstrandField',action="store")
    p.add_argument('--outFileNamePrefix',action="store",dest='prefix')
    p.add_argument('--runThreadN',action="store")
    args = p.parse_args(argv)
    with io.open("%sReadsPerGene.out.tab" % args.prefix,'wt') as fp:
        if not unmapped_output:
            fp.write(u"""N_unmapped	2026581	2026581	2026581
N_multimapping	4020538	4020538	4020538
N_noFeature	8533504	24725707	8782932
N_ambiguous	618069	13658	192220
ENSMUSG00000102592.1	0	0	0
ENSMUSG00000088333.2	0	0	0
ENSMUSG00000103265.1	4	0	4
ENSMUSG00000103922.1	23	23	0
ENSMUSG00000033845.13	437	0	437
ENSMUSG00000102275.1	19	0	19
ENSMUSG00000025903.14	669	2	667
ENSMUSG00000104217.1	0	0	0
ENSMUSG00000033813.15	805	0	805
ENSMUSG00000062588.4	11	11	0
ENSMUSG00000103280.1	9	9	0
ENSMUSG00000002459.17	3	3	0
ENSMUSG00000064363.1	74259	393	73866
ENSMUSG00000064364.1	0	0	0
ENSMUSG00000064365.1	0	0	0
ENSMUSG00000064366.1	0	0	0
ENSMUSG00000064367.1	148640	7892	152477
ENSMUSG00000064368.1	44003	42532	13212
ENSMUSG00000064369.1	6	275	6
ENSMUSG00000064370.1	122199	199	123042
""")
        else:
            fp.write(u"""N_unmapped	1	1	1
N_multimapping	0	0	0
N_noFeature	0	0	0
N_ambiguous	0	0	0
ENSG00000223972.5	0	0	0
ENSG00000227232.5	0	0	0
ENSG00000278267.1	0	0	0
ENSG00000243485.3	0	0	0
ENSG00000274890.1	0	0	0
ENSG00000237613.2	0	0	0
ENSG00000268020.3	0	0	0
ENSG00000240361.1	0	0	0
ENSG00000186092.4	0	0	0
ENSG00000238009.6	0	0	0
""")
