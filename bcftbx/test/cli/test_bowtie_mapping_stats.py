#######################################################################
# Tests
#######################################################################

import unittest
import io
from bcftbx.cli.bowtie_mapping_stats import BowtieMappingStats

class TestBowtieMappingStats(unittest.TestCase):
    def test_bowtie1_single_sample(self):
        """Process output from bowtie for single sample
        """
        fp = io.StringIO(u"""Time loading reference: 00:00:01
Time loading forward index: 00:00:00
Time loading mirror index: 00:00:02
Seeded quality full-index search: 00:10:20
# reads processed: 39808407
# reads with at least one reported alignment: 2737588 (6.88%)
# reads that failed to align: 33721722 (84.71%)
# reads with alignments suppressed due to -m: 3349097 (8.41%)
Reported 2737588 alignments to 1 output stream(s)
Time searching: 00:10:27
Overall time: 00:10:27
""")
        stats = BowtieMappingStats()
        stats.add_samples(fp=fp)
        # Check samples
        self.assertEqual(stats.n_samples,1)
        sample = stats.samples[0]
        self.assertEqual(sample.name,'1')
        self.assertEqual(sample.total_reads,39808407)
        self.assertEqual(sample.didnt_align,33721722)
        self.assertEqual(sample.uniquely_mapped,2737588)
        self.assertEqual(sample.bowtie_version,'1')
        self.assertFalse(sample.paired_end)
        # Check outputs
        tab_data = stats.tab_file()
        self.assertEqual(tab_data,"""Sample	1
	
total reads	39808407
didn't align	33721722
total mapped reads	6086685
  % of all reads	15.3%
uniquely mapped	2737588
  % of all reads	6.9%
  % of mapped reads	45.0%""")

    def test_bowtie1_many_samples(self):
        """Process output from bowtie for multiple samples
        """
        fp = io.StringIO(u"""/bin/bash -l /cvos/local/apps/sge/6.2u5/templar/spool/tw002/job_scripts/651785

JP01
Time loading reference: 00:00:01
Time loading forward index: 00:00:00
Time loading mirror index: 00:00:02
Seeded quality full-index search: 00:10:20
# reads processed: 39808407
# reads with at least one reported alignment: 2737588 (6.88%)
# reads that failed to align: 33721722 (84.71%)
# reads with alignments suppressed due to -m: 3349097 (8.41%)
Reported 2737588 alignments to 1 output stream(s)
Time searching: 00:10:27
Overall time: 00:10:27
JP02
Time loading reference: 00:00:00
Time loading forward index: 00:00:00
Time loading mirror index: 00:00:00
Seeded quality full-index search: 00:09:17
# reads processed: 34455085
# reads with at least one reported alignment: 4087382 (11.86%)
# reads that failed to align: 25744573 (74.72%)
# reads with alignments suppressed due to -m: 4623130 (13.42%)
Reported 4087382 alignments to 1 output stream(s)
Time searching: 00:09:18
Overall time: 00:09:18
JP03
Time loading reference: 00:00:00
Time loading forward index: 00:00:00Time loading mirror index: 00:00:00
Seeded quality full-index search: 00:10:41
# reads processed: 40319096
# reads with at least one reported alignment: 3094671 (7.68%)
# reads that failed to align: 33236646 (82.43%)
# reads with alignments suppressed due to -m: 3987779 (9.89%)
Reported 3094671 alignments to 1 output stream(s)
Time searching: 00:10:42
Overall time: 00:10:42
JP04
Time loading reference: 00:00:00
Time loading forward index: 00:00:00
Time loading mirror index: 00:00:00
Seeded quality full-index search: 00:33:25
# reads processed: 129900841
# reads with at least one reported alignment: 10086835 (7.77%)
# reads that failed to align: 106040617 (81.63%)
# reads with alignments suppressed due to -m: 13773389 (10.60%)
Reported 10086835 alignments to 1 output stream(s)
Time searching: 00:33:26
Overall time: 00:33:26
""")
        stats = BowtieMappingStats()
        n_added = stats.add_samples(fp=fp)
        self.assertEqual(n_added,4)
        self.assertEqual(stats.n_samples,4)
        expected_names = ['1','2','3','4']
        expected_total_reads = [39808407,34455085,40319096,129900841]
        expected_didnt_align = [33721722,25744573,33236646,106040617]
        expected_uniquely_mapped = [2737588,4087382,3094671,10086835]
        for i in range(4):
            sample = stats.samples[i]
            self.assertEqual(sample.name,expected_names[i])
            self.assertEqual(sample.total_reads,expected_total_reads[i])
            self.assertEqual(sample.didnt_align,expected_didnt_align[i])
            self.assertEqual(sample.uniquely_mapped,expected_uniquely_mapped[i])
            self.assertEqual(sample.bowtie_version,'1')
            self.assertFalse(sample.paired_end)
        # Check outputs
        tab_data = stats.tab_file()
        self.assertEqual(tab_data,"""Sample	1	2	3	4
				
total reads	39808407	34455085	40319096	129900841
didn't align	33721722	25744573	33236646	106040617
total mapped reads	6086685	8710512	7082450	23860224
  % of all reads	15.3%	25.3%	17.6%	18.4%
uniquely mapped	2737588	4087382	3094671	10086835
  % of all reads	6.9%	11.9%	7.7%	7.8%
  % of mapped reads	45.0%	46.9%	43.7%	42.3%""")

    def test_bowtie1_samples_multiple_files(self):
        """Process output from bowtie for multiple samples from multiple files
        """
        fp1 = io.StringIO(u"""/bin/bash -l /cvos/local/apps/sge/6.2u5/templar/spool/tw002/job_scripts/651785

JP01
Time loading reference: 00:00:01
Time loading forward index: 00:00:00
Time loading mirror index: 00:00:02
Seeded quality full-index search: 00:10:20
# reads processed: 39808407
# reads with at least one reported alignment: 2737588 (6.88%)
# reads that failed to align: 33721722 (84.71%)
# reads with alignments suppressed due to -m: 3349097 (8.41%)
Reported 2737588 alignments to 1 output stream(s)
Time searching: 00:10:27
Overall time: 00:10:27
JP02
Time loading reference: 00:00:00
Time loading forward index: 00:00:00
Time loading mirror index: 00:00:00
Seeded quality full-index search: 00:09:17
# reads processed: 34455085
# reads with at least one reported alignment: 4087382 (11.86%)
# reads that failed to align: 25744573 (74.72%)
# reads with alignments suppressed due to -m: 4623130 (13.42%)
Reported 4087382 alignments to 1 output stream(s)
Time searching: 00:09:18
Overall time: 00:09:18
""")
        fp2 = io.StringIO(u"""JP03
Time loading reference: 00:00:00
Time loading forward index: 00:00:00Time loading mirror index: 00:00:00
Seeded quality full-index search: 00:10:41
# reads processed: 40319096
# reads with at least one reported alignment: 3094671 (7.68%)
# reads that failed to align: 33236646 (82.43%)
# reads with alignments suppressed due to -m: 3987779 (9.89%)
Reported 3094671 alignments to 1 output stream(s)
Time searching: 00:10:42
Overall time: 00:10:42
JP04
Time loading reference: 00:00:00
Time loading forward index: 00:00:00
Time loading mirror index: 00:00:00
Seeded quality full-index search: 00:33:25
# reads processed: 129900841
# reads with at least one reported alignment: 10086835 (7.77%)
# reads that failed to align: 106040617 (81.63%)
# reads with alignments suppressed due to -m: 13773389 (10.60%)
Reported 10086835 alignments to 1 output stream(s)
Time searching: 00:33:26
Overall time: 00:33:26
""")
        stats = BowtieMappingStats()
        n_added = stats.add_samples(filen="log1",fp=fp1)
        self.assertEqual(n_added,2)
        self.assertEqual(stats.n_samples,2)
        n_added = stats.add_samples(filen="log2",fp=fp2)
        self.assertEqual(n_added,2)
        self.assertEqual(stats.n_samples,4)
        expected_names = ['1','2','3','4']
        expected_total_reads = [39808407,34455085,40319096,129900841]
        expected_didnt_align = [33721722,25744573,33236646,106040617]
        expected_uniquely_mapped = [2737588,4087382,3094671,10086835]
        for i in range(4):
            sample = stats.samples[i]
            self.assertEqual(sample.name,expected_names[i])
            self.assertEqual(sample.total_reads,expected_total_reads[i])
            self.assertEqual(sample.didnt_align,expected_didnt_align[i])
            self.assertEqual(sample.uniquely_mapped,expected_uniquely_mapped[i])
            self.assertEqual(sample.bowtie_version,'1')
            self.assertFalse(sample.paired_end)
        # Check outputs
        tab_data = stats.tab_file()
        self.assertEqual(tab_data,"""Sample	1 (log1)	2 (log1)	3 (log2)	4 (log2)
				
total reads	39808407	34455085	40319096	129900841
didn't align	33721722	25744573	33236646	106040617
total mapped reads	6086685	8710512	7082450	23860224
  % of all reads	15.3%	25.3%	17.6%	18.4%
uniquely mapped	2737588	4087382	3094671	10086835
  % of all reads	6.9%	11.9%	7.7%	7.8%
  % of mapped reads	45.0%	46.9%	43.7%	42.3%""")

    def test_bowtie2_sample_single_sample(self):
        """Process output from bowtie2 for single sample
        """
        fp = io.StringIO(u"""Multiseed full-index search: 00:20:27
117279034 reads; of these:
  117279034 (100.00%) were unpaired; of these:
    1937614 (1.65%) aligned 0 times
    115341420 (98.35%) aligned exactly 1 time
    0 (0.00%) aligned >1 times
98.35% overall alignment rate
Time searching: 00:21:01
Overall time: 00:21:02
""")
        stats = BowtieMappingStats()
        n_added = stats.add_samples(filen='log1',fp=fp)
        self.assertEqual(n_added,1)
        self.assertEqual(stats.n_samples,1)
        sample = stats.samples[0]
        self.assertEqual(sample.name,'1')
        self.assertEqual(sample.total_reads,117279034)
        self.assertEqual(sample.didnt_align,1937614)
        self.assertEqual(sample.uniquely_mapped,115341420)
        self.assertEqual(sample.bowtie_version,'2')
        self.assertFalse(sample.paired_end)
        # Check outputs
        tab_data = stats.tab_file()
        self.assertEqual(tab_data,"""Sample	1
	
total reads	117279034
didn't align	1937614
total mapped reads	115341420
  % of all reads	98.3%
uniquely mapped	115341420
  % of all reads	98.3%
  % of mapped reads	100.0%""")

    def test_bowtie2_sample_single_PE_sample(self):
        """Process output from bowtie2 for single paired-end sample
        """
        fp = io.StringIO(u"""Multiseed full-index search: 01:45:33
85570063 reads; of these:
  85570063 (100.00%) were paired; of these:
    56052776 (65.51%) aligned concordantly 0 times
    22792207 (26.64%) aligned concordantly exactly 1 time
    6725080 (7.86%) aligned concordantly >1 times
    ----
    56052776 pairs aligned concordantly 0 times; of these:
      6635276 (11.84%) aligned discordantly 1 time
    ----
    49417500 pairs aligned 0 times concordantly or discordantly; of these:
      98835000 mates make up the pairs; of these:
        93969575 (95.08%) aligned 0 times
        1622693 (1.64%) aligned exactly 1 time
        3242732 (3.28%) aligned >1 times
45.09% overall alignment rate
Time searching: 01:46:03
Overall time: 01:46:03
""")
        stats = BowtieMappingStats()
        n_added = stats.add_samples(filen='log1',fp=fp)
        self.assertEqual(n_added,1)
        self.assertEqual(stats.n_samples,1)
        sample = stats.samples[0]
        self.assertEqual(sample.name,'1')
        self.assertEqual(sample.total_reads,85570063)
        self.assertEqual(sample.didnt_align,56052776)
        self.assertEqual(sample.uniquely_mapped,22792207)
        self.assertEqual(sample.bowtie_version,'2')
        self.assertTrue(sample.paired_end)
        # Check outputs
        tab_data = stats.tab_file()
        self.assertEqual(tab_data,"""Sample	1
	
total reads	85570063
didn't align	56052776
total mapped reads	29517287
  % of all reads	34.5%
uniquely mapped	22792207
  % of all reads	26.6%
  % of mapped reads	77.2%""")
