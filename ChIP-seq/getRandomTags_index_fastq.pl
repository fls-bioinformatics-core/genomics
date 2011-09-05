#! /usr/bin/perl -w

#### Program to retrieve N random sequences from a FASTQ file
#### 4 lines e.g.
# @1_27_277
# T00000330300201203231033210203111021322202103001231
# +
# 4?<95%>>9%09A-@0:65@:;:9?(059+(,;'97'4<)(4%;'+4/<1

#### Ian Donaldson 16 November 2009

use strict;
use List::Util 'shuffle';

#### Usage
unless(@ARGV==3) {
  die("USAGE: $0 | Input FASTQ file | Number of random tags to extract | Output\n\n");
}

#### Files
open(INPUT, "<$ARGV[0]") or die("Could not open input!\n\n");
open(OUTPUT, ">$ARGV[2]") or die("Could not open output!\n\n");

#### Lines to extract
my $extract = $ARGV[1];

#### Make a list tell() positions in a list, start with beginning of first line 
my @line_starts = (0);

#### Line count
my $line_count = 0;

#### Read each line on input file to generate a list of line starts and shuffle
while(defined(my $line = <INPUT>)) {
   # Increment line counter 
   $line_count++;

   # Determine line position if on a 4th line (modulo 4)
   if( ($line_count % 4) == 0) { 
      my $position = tell(INPUT);

      push(@line_starts, $position);
      #print STDOUT "pos $position line $line_count\n";
   }
}

#### Remove last element of the list (end of last line)
pop(@line_starts);

print STDOUT "Filled line start position list!\n";

#### Suffle the line number array
my @shuffled_line_starts = shuffle(@line_starts);

print STDOUT "Shuffled line start position list!\n";

#### Get the line contents for the first N lines in the shuffled list
for(my $i=0; $i<$extract; $i++) {
   my $shuffled_start = $shuffled_line_starts[$i];

   seek(INPUT, $shuffled_start, 0);

   my $line1 = <INPUT>;
   my $line2 = <INPUT>; 
   my $line3 = <INPUT>;
   my $line4 = <INPUT>;

   print OUTPUT "$line1";
   print OUTPUT "$line2";
   print OUTPUT "$line3";
   print OUTPUT "$line4";
}

#### Close files
close(INPUT);
close(OUTPUT);

exit;
