#! /usr/bin/perl

# Split csfasta and qual files containing multiple barcodes into separate sets
# Ian Donaldson 1 Oct 2010

# TRY www.perlmonks.org/?node_id=848742

use strict;
use Bio::SeqIO;
use FileHandle;

#### Usage
##########
unless(@ARGV==3) {
   die("\nUSAGE: $0 <barcode.csfasta> <read.csfasta> <read.qual>\n",
       "Expects BC.csfasta, F3.csfasta and F3.qual files containing multiple barcodes.\n",
       "Currently set up for 'BC Kit Module 1-16'.\n\n");
}


#### Reject/summary files
#########################
open(LOG, ">$ARGV[0]\.log") or die("Could not open log file!\n\n");
open(REJECT_BC, ">$ARGV[0]\.reject") or die("Could not open bc reject file!\n\n");
open(REJECT_READS, ">$ARGV[1]\.reject") or die("Could not open reads reject file!\n\n");
open(REJECT_QUALS, ">$ARGV[2]\.reject") or die("Could not open quals reject file!\n\n");


#### Extract the expected barcode sequences from the barcode sequence file
#### and prepare filehandles
##########################################################################

# expected barcodes list
my @exp_codes_list = ();

# expected barcodes hash
my %exp_codes_hash = ();

# open barcode.csfasta
open(BC_SEQ, "<$ARGV[0]") or die("Could not open bar code csfasta file!\n$!\n\n");

EXP_LOOP: while(defined(my $bc_seq_line = <BC_SEQ>)) {
   # extract expected barcodes from header line
   if($bc_seq_line =~ /^# Library:DNA:/) {
      (my $exp_codes_temp) = $bc_seq_line =~ /# Library:DNA:(.*)\n/;

      # fill expected codes list
      @exp_codes_list = split(/\s/, $exp_codes_temp);

      # fill expected codes hash
      foreach (@exp_codes_list) {
         $exp_codes_hash{$_} = 1;
      }

      # exit main loop - stop reading the current file
      last EXP_LOOP       
   }

   # skip to next line if in wrong line - stop reading every line of file
   else { next EXP_LOOP }
}

close(BC_SEQ);

# make hashes of filehandles
my $part_read_name = $ARGV[1];
$part_read_name =~ s/\.csfasta//;

my $part_qual_name = $ARGV[2];
$part_qual_name =~ s/\.qual//;

my %FH_READS = ();
my %FH_QUALS = ();

$FH_READS{"30222"} = FileHandle->new("$part_read_name\_1.csfasta", "w");
$FH_READS{"21011"} = FileHandle->new("$part_read_name\_2.csfasta", "w");
$FH_READS{"13330"} = FileHandle->new("$part_read_name\_3.csfasta", "w");
$FH_READS{"02103"} = FileHandle->new("$part_read_name\_4.csfasta", "w");
$FH_READS{"32031"} = FileHandle->new("$part_read_name\_5.csfasta", "w");
$FH_READS{"11120"} = FileHandle->new("$part_read_name\_6.csfasta", "w");
$FH_READS{"00313"} = FileHandle->new("$part_read_name\_7.csfasta", "w");
$FH_READS{"23202"} = FileHandle->new("$part_read_name\_8.csfasta", "w");
$FH_READS{"01233"} = FileHandle->new("$part_read_name\_9.csfasta", "w");
$FH_READS{"22320"} = FileHandle->new("$part_read_name\_10.csfasta", "w");
$FH_READS{"33111"} = FileHandle->new("$part_read_name\_11.csfasta", "w");
$FH_READS{"10002"} = FileHandle->new("$part_read_name\_12.csfasta", "w");
$FH_READS{"03020"} = FileHandle->new("$part_read_name\_13.csfasta", "w");
$FH_READS{"12213"} = FileHandle->new("$part_read_name\_14.csfasta", "w");
$FH_READS{"31302"} = FileHandle->new("$part_read_name\_15.csfasta", "w");
$FH_READS{"20131"} = FileHandle->new("$part_read_name\_16.csfasta", "w");

$FH_QUALS{"30222"} = FileHandle->new("$part_qual_name\_1.qual", "w");
$FH_QUALS{"21011"} = FileHandle->new("$part_qual_name\_2.qual", "w");
$FH_QUALS{"13330"} = FileHandle->new("$part_qual_name\_3.qual", "w");
$FH_QUALS{"02103"} = FileHandle->new("$part_qual_name\_4.qual", "w");
$FH_QUALS{"32031"} = FileHandle->new("$part_qual_name\_5.qual", "w");
$FH_QUALS{"11120"} = FileHandle->new("$part_qual_name\_6.qual", "w");
$FH_QUALS{"00313"} = FileHandle->new("$part_qual_name\_7.qual", "w");
$FH_QUALS{"23202"} = FileHandle->new("$part_qual_name\_8.qual", "w");
$FH_QUALS{"01233"} = FileHandle->new("$part_qual_name\_9.qual", "w");
$FH_QUALS{"22320"} = FileHandle->new("$part_qual_name\_10.qual", "w");
$FH_QUALS{"33111"} = FileHandle->new("$part_qual_name\_11.qual", "w");
$FH_QUALS{"10002"} = FileHandle->new("$part_qual_name\_12.qual", "w");
$FH_QUALS{"03020"} = FileHandle->new("$part_qual_name\_13.qual", "w");
$FH_QUALS{"12213"} = FileHandle->new("$part_qual_name\_14.qual", "w");
$FH_QUALS{"31302"} = FileHandle->new("$part_qual_name\_15.qual", "w");
$FH_QUALS{"20131"} = FileHandle->new("$part_qual_name\_16.qual", "w");

# make hashes for read and quality split totals
my %count_reads = ();
my %count_quals = ();

$count_reads{"30222"} = [0, "1"];
$count_reads{"21011"} = [0, "2"];
$count_reads{"13330"} = [0, "3"];
$count_reads{"02103"} = [0, "4"];
$count_reads{"32031"} = [0, "5"];
$count_reads{"11120"} = [0, "6"];
$count_reads{"00313"} = [0, "7"];
$count_reads{"23202"} = [0, "8"];
$count_reads{"01233"} = [0, "9"];
$count_reads{"22320"} = [0, "10"];
$count_reads{"33111"} = [0, "11"];
$count_reads{"10002"} = [0, "12"];
$count_reads{"03020"} = [0, "13"];
$count_reads{"12213"} = [0, "14"];
$count_reads{"31302"} = [0, "15"];
$count_reads{"20131"} = [0, "16"];

$count_quals{"30222"} = [0, "1"];
$count_quals{"21011"} = [0, "2"];
$count_quals{"13330"} = [0, "3"];
$count_quals{"02103"} = [0, "4"];
$count_quals{"32031"} = [0, "5"];
$count_quals{"11120"} = [0, "6"];
$count_quals{"00313"} = [0, "7"];
$count_quals{"23202"} = [0, "8"];
$count_quals{"01233"} = [0, "9"];
$count_quals{"22320"} = [0, "10"];
$count_quals{"33111"} = [0, "11"];
$count_quals{"10002"} = [0, "12"];
$count_quals{"03020"} = [0, "13"];
$count_quals{"12213"} = [0, "14"];
$count_quals{"31302"} = [0, "15"];
$count_quals{"20131"} = [0, "16"];


#### For each read ID add its barcode sequence to a hash - partial sequence are allowed 
#### if they can be unambiguously matched
#######################################################################################

# Copy barcode sequence file and remove top 4 header lines
system("cp $ARGV[0] $ARGV[0]\.tmp");
system("sed -i '1,4d' $ARGV[0]\.tmp");

# barcode hash
my %barcode_hash = ();

# barcode counts
my $mm_barcodes = 0;
my $wt_barcodes = 0;
my $wt_reads = 0;
my $wt_quals = 0;
my $skip_barcodes = 0;
my $count_read_total = 0; 
my $count_qual_total = 0;
my $count_wrongcall_total = 0;
my $count_nocall_total = 0;
my $corrected_call = 0;
my $still_wrong_call = 0;
my $miss_read = 0;
my $miss_qual = 0;

# Load barcode sequence file to BioPerl object
my $bc_seq_in = Bio::SeqIO->new (-file => "$ARGV[0]\.tmp", '-format' => 'Fasta');

BC_LOOP: while ( my $bc_seq_obj = $bc_seq_in->next_seq() ) {
   my $bc_sequence = $bc_seq_obj->seq();

   # record total barcodes
   $wt_barcodes++;

   # remove initial letter base
   $bc_sequence =~ s/^\w//g;

   my $bc_name = ($bc_seq_obj->display_id());
   my $full_bc_name = $bc_name;
   $bc_name =~ s/_BC$//;

   #### If barcode sequence contains '.' work out full seq from list 
   if($bc_sequence =~ /\./) {
      # Barcodes with missed color calls '.' in seq
      $count_nocall_total++;

      # flag to catch whether match is found
      my $bc_match = 0;

      #print STDOUT "before: $bc_sequence "; 

      foreach my $exp_code (@exp_codes_list) {
         #print STDOUT "exp_code: $exp_code ";

         if($exp_code =~ /^$bc_sequence/) {
            $bc_sequence = $exp_code;

            $bc_match = 1;
         }
      }

      # skip this barcode if partial match is not found, will also catch if match is ambiguous
      unless($bc_match==1) { 
         $skip_barcodes++;

         print REJECT_BC "$full_bc_name\n$bc_sequence\n";

         next BC_LOOP; 
      }

      # record unambiguous miscall containing barcodes
      $mm_barcodes++;
   }

   # send header and colour seq to hash if full/corrected barcode matches the expected set
   if(exists($exp_codes_hash{$bc_sequence})) {   
      $barcode_hash{"$bc_name"} = "$bc_sequence";
   }

   # check whether the barcode contains only 1 wrong color call compared to expected barcodes 
   else {
      $count_wrongcall_total++;

      my $single_match = 0;
      my $corrected_bc = '';

      # for each expected key see how differences there are to the current barcode
      foreach my $exp_bc (@exp_codes_list) {
         my $num_wrong = CalcDifferences($exp_bc, $bc_sequence);

         #print "expbc: $exp_bc bcseq: $bc_sequence wrong: $num_wrong\n";

         if($num_wrong == 1) {
            $single_match++;

            $corrected_bc = $exp_bc;
         }
      }

      # after checking the wrong barcode to all other barcodes, if there is only a single difference
      # in one barcode add it to the name-barcode hash
      if($single_match == 1) {
         $barcode_hash{"$bc_name"} = "$corrected_bc";

         $corrected_call++;
      }

      else {
         print REJECT_BC ">$full_bc_name\n$bc_sequence\n";
         
         $still_wrong_call++;  
      }
   }

   #print "$bc_name => $bc_sequence\n";
}


# Find barcode for read sequences and sent to corressponding file
# ###############################################################

# Copy read sequence file and remove top 3 header lines
system("cp $ARGV[1] $ARGV[1]\.tmp");
system("sed -i '1,3d' $ARGV[1]\.tmp");

# Load read sequence file to BioPerl object 
#my $read_seq_in = Bio::SeqIO->new (-file => "$ARGV[1]\.tmp", '-format' => 'Fasta');
#
#while ( my $read_seq_obj = $read_seq_in->next_seq() ) {
#   my $read_sequence = $read_seq_obj->seq();
#
#   my $read_name = ($read_seq_obj->display_id());
#   my $tmp_read_name = $read_name;
#   $tmp_read_name =~ s/_F3$//;

# Load file using FileHandle
my $READ_SEQS = FileHandle->new("$ARGV[1]\.tmp", "r");
 
while(<$READ_SEQS>) {
   my $read_name = $_;
   chomp($read_name);

   my $tmp_read_name = $read_name;
   $tmp_read_name =~ s/^>//;
   $tmp_read_name =~ s/_F3$//;

   # record total reads
   $wt_reads++;

   my $read_sequence = $READ_SEQS->getline;
   chomp($read_sequence);

   #print "$read_sequence\n";

   # Retreive barcode from hash
   my $got_barcode = $barcode_hash{$tmp_read_name};

   if($got_barcode) {
      #TEST
      #print STDOUT "READ: $read_name BARCODE: $got_barcode\n";

      # print sequence to barcode file
      $FH_READS{$got_barcode}->print("$read_name\n$read_sequence\n");

      # count splits
      $count_reads{$got_barcode}[0]++;
   
      # count total
      $count_read_total++;
   }

   else {
      $miss_read++;

      print REJECT_READS "$read_name\n$read_sequence\n";
   }
}


# Find barcode for read qualities and sent to corressponding file
# ###############################################################

# Copy read quality file and remove top 3 header lines
system("cp $ARGV[2] $ARGV[2]\.tmp");
system("sed -i '1,3d' $ARGV[2]\.tmp");

# Load read quality file to BioPerl object
#my $read_qual_in = Bio::SeqIO::Quality->new (-file => "$ARGV[2]\.tmp", '-format' => 'qual');
#
#while ( my $read_qual_obj = $read_qual_in->next_qual() ) {
#   my $read_qualities = $read_qual_obj->qual();
#
#   my $read_name = ($read_qual_obj->display_id());
#   my $tmp_read_name = $read_name;
#   $tmp_read_name =~ s/_F3$//;
#

# Load file using FileHandle
my $READ_QUALS = FileHandle->new("$ARGV[2]\.tmp", "r");

while(<$READ_QUALS>) {
   my $read_name = $_;
   chomp($read_name);

   my $tmp_read_name = $read_name;
   $tmp_read_name =~ s/^>//;
   $tmp_read_name =~ s/_F3$//;

   # record total quals
   $wt_quals++;

   my $read_qualities = $READ_QUALS->getline;
   chomp($read_qualities);
 
   #print "$read_qualities\n";

   # Retreive barcode from hash
   my $got_barcode = $barcode_hash{$tmp_read_name};

   if($got_barcode) {
      # print qualities to barcode file
      $FH_QUALS{$got_barcode}->print("$read_name\n$read_qualities\n");      

      # count splits
      $count_quals{$got_barcode}[0]++;

      # count total
      $count_qual_total++;
   }

   else {
      $miss_qual++;

      print REJECT_QUALS "$read_name\n$read_qualities\n";
   }
}


#### Remove temporary barcode sequence files
############################################
system("rm $ARGV[0]\.tmp");
system("rm $ARGV[1]\.tmp");
system("rm $ARGV[2]\.tmp");


#### Summary
############
print LOG "Total processed barcodes = $wt_barcodes\n";
print LOG "Total processed reads = $wt_reads\n";
print LOG "Total processed qualities = $wt_quals\n";
print LOG "Total barcodes with color no-calls ('.' in seq) = $count_nocall_total\n";
print LOG "  Barcodes with unambiguous color no-calls (only 1 match to expected codes) = $mm_barcodes\n"; 
print LOG "  Skipped ambiguous barcodes (>1 match to expected codes) = $skip_barcodes\n";
print LOG "Total barcodes with color wrong-calls (full seq but some difference to expected) = $count_wrongcall_total\n";
print LOG "  Corrected barcodes (only 1 difference to expected barcode) = $corrected_call\n";
print LOG "  Rejected barcodes (>1 difference to expected barcode) = $still_wrong_call\n";
print LOG "Number of reads without barcodes = $miss_read\n";
print LOG "Number of quals without barcodes = $miss_qual\n";


print LOG "\nSorted reads (sample barcode total):\n";

my @sorted_read_keys = sort(keys(%count_reads));
foreach my $read_key (@sorted_read_keys) {
   print LOG "$count_reads{$read_key}[1]\t$read_key\t$count_reads{$read_key}[0]\n";
} 

print LOG "Read total = $count_read_total\n";

print LOG "\nSorted quality scores (sample barcode total):\n";
my @sorted_qual_keys = sort(keys(%count_quals));
foreach my $qual_key (@sorted_qual_keys) {
   print LOG "$count_quals{$qual_key}[1]\t$qual_key\t$count_quals{$qual_key}[0]\n";
} 

print LOG "Quality total = $count_qual_total\n";


#### Close reject files
#######################
close(LOG);
close(REJECT_BC);
close(REJECT_READS);
close(REJECT_QUALS);

exit;


#### Subroutine
###############

#CalcDifferences($exp_key, $bc_sequence)
sub CalcDifferences {
   my $exp = shift(@_);
   my @exp_chars = split('', $exp);

   my $wrong = shift(@_);
   my @wrong_chars = split('', $wrong);
   
   # check each letter of the 'expected' string against the same position in the 'wrong' string
   my $char_diffs = length($exp);
   #print "length $char_diffs\n";

   for(my $i=0; $i<5; $i++) {
      my $exp_char = $exp_chars[$i];
      my $wrong_char = $wrong_chars[$i];

      # if there is a match subtract 1 from the number of differences
      if($exp_char == $wrong_char) { $char_diffs-- }
   } 

   return $char_diffs;
}

