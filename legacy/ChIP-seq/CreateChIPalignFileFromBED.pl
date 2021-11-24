#! /usr/bin/perl -w

#### Program to convert a csfasta->BED file to ChIP alignment format for GLITR
#### Ian Donaldson 16 November 2009

use strict;

#### Usage
unless(@ARGV==2) {
  die("USAGE: $0 | Input CHIP align file | Output\n\n");
}

#### Files
open(INPUT, "<$ARGV[0]") or die("Could not open input!\n\n");
open(OUTPUT, ">$ARGV[1]") or die("Could not open output!\n\n");

#### Read each line of file, extract only chr, start and strand
while(defined(my $line = <INPUT>)) {
   if($line=~/(^\s|^#)/) { next }

   my($chr, $start, $strand) = '';

   my @line_bits = split(/\t/, $line);

   print OUTPUT "$line_bits[0]\t$line_bits[1]\t$line_bits[5]\n";
}

#### Close files
close(INPUT);
close(OUTPUT);

exit;
