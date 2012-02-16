#! /usr/bin/perl -w
#
# Convert SOLiD file to format acceptible to R
# Creates 1 file per position of read
# Ian Donaldson 20 July 2010
# Modified to also output a second set of file in primer order - 5 Aug 2010
# Modified to obsfurcate the file names etc in the example below - 16 Jun 2011 (PJB)

use strict;

# example qual
# Thu May 20 10:34:56 2010 /share/apps/corona/bin/filter_fasta.pl --output=/data/results/.../results.F1B1/primary.20100520164903182 --name=solid0424_20100511_blah_blah --tag=F3 --minlength=50 --mincalls=25 --prefix=T /data/results/.../jobs/postPrimerSetPrimary.2176/rawseq 
# Cwd: /home/pipeline
# Title: solid0424_20100511_blah_blah
# >932_7_59_F3
# -1 -1 -1 -1 -1 4 8 4 4 -1 4 8 -1 -1 -1 -1 5 -1 4 -1 4 4 -1 4 -1 -1 4 4 -1 -1 4 -1 -1 4 -1 -1 4 4 4 -1 5 5 5 4 -1 4 5 -1 4 4 

# usage
unless(@ARGV == 2) {
   die"USAGE: $0 | Input qual file | Output suffix\n\n";
}

# input
open(INPUT, "<$ARGV[0]") or die("Could not open input!");

# array of extensions for intermediate files
my @extensions = ("AA","AB","AC","AD","AE","AF","AG","AH","AI","AJ","AK","AL","AM",
		  "AN","AO","AP","AQ","AR","AS","AT","AU","AV","AW","AX","AY","AZ",
		  "BA","BB","BC","BD","BE","BF","BG","BH","BI","BJ","BK","BL","BM",
		  "BN","BO","BP","BQ","BR","BS","BT","BU","BV","BW","BX");

# Open output files for sequence positions
# Files will be named <blah>_posnAA, <blah>_posnAB etc
# We'll store the file handles in an array so we can access them later on
my @output = ();
for (my $pos = 1; $pos <= 50; $pos++) {
    # Make names
    my $filename = ">$ARGV[1]\_posn" . $extensions[$pos-1];
    # Open file
    open(my $fh,$filename) or die("Could not open output for position " . $pos-1);
    # Store filehandle for writing in next step
    push(@output,$fh)
}

# extract data from file line by line
while(defined(my $line = <INPUT>)) {
   if($line =~ /(^#|^>)/) { next } # comment lines and headers
   # Output in sequence order
   my @line_bits = split(/\s/, $line);
   # Loop over line bits and write each to the appropriate file
   for (my $pos = 1; $pos <= 50; $pos++) {
       my $fh = $output[$pos-1];
       print $fh "$line_bits[$pos-1]\n";
   }
}

# Close the files
close(INPUT);
for (my $pos = 1; $pos <= 50; $pos++) {
    my $fh = $output[$pos-1];
    close($fh . $pos);
}

exit;
