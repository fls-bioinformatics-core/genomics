#! /usr/bin/perl -w

#### Program to retrieve N random tags from a ChIP alignment file
#### 'chrN start strand' for GLITR.
#### Ian Donaldson 16 November 2009

use strict;
use List::Util 'shuffle';

#### Usage
unless(@ARGV==3) {
  die("USAGE: $0 | Input CHIP align file | Number of random tags to extract | Output\n\n");
}

#### Files
open(INPUT, "<$ARGV[0]") or die("Could not open input!\n\n");
open(OUTPUT, ">$ARGV[2]") or die("Could not open output!\n\n");

#### Lines to extract
my $extract = $ARGV[1];

#### Make a list tell() positions in a list, start with beginning of first line 
my @line_starts = (0);

#### Read each line on input file to generate a list of line starts and shuffle
while(defined(my $line = <INPUT>)) {
   # Skip blank or comment lines
   if($line =~ /(^#|^\s)/) { next }

   # Determine line position
   my $position = tell(INPUT);

   push(@line_starts, $position);
   #print STDOUT "$position\n";
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

   my $current_line = <INPUT>;

   print OUTPUT "$current_line";
}

#### Close files
close(INPUT);
close(OUTPUT);

exit;
