#! /usr/bin/perl -w
#
#Get stats for coverage using a coverage file from genomeCoverageBed -d
#format of input is: chr position count
#Output mean and median for all positions inc. 0 count positions
#Ian Donaldson 16 June 2011
#
# Usage: perl calc_coverage <coverage_file>
#
# Note: this script requires Statistics::Descriptive module
# To install on Fedora, do "yum install perl-Statistics-Descriptive"

use Statistics::Descriptive; 
use strict;

# New stats instance
my $stat = Statistics::Descriptive::Full->new(); 

# Usage
unless(@ARGV == 1) {
   die"USAGE: $0 | Input coverage file\n\n";
}

# Read thru lines of coverage file and put score into list
open(INPUT, "<$ARGV[0]");

# List for counts
my @counts = ();

while(defined(my $line = <INPUT>)) {
   if($line =~ /(^\s|^#)/) { next }

   my @line_bits = split(/\t/, $line);
   my $count = $line_bits[2];

   push(@counts, $count);
}

# Add counts to stats object
$stat->add_data(@counts); 

# Calc stats
my $mean = $stat->mean();
my $median = $stat->median();

# Print
print STDOUT "$ARGV[0]\t$mean\t$median\n";

close(INPUT);
