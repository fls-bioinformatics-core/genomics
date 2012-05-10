#! /usr/bin/perl -w
#
# Takes a fastq file and keeps the first (5') bases of the sequences.
#
# Ian Donaldson 5 March 2012


# Usage
unless(@ARGV==2) {
   die("USAGE $0 | single end FASTQ | desired length\n\n")
}

# Desired length
my $length = $ARGV[1];
chomp $length;

# Files
open(INPUT, "<$ARGV[0]");
open(OUTPUT, ">$ARGV[0]\.t$length");

# Loop thru till end of file
while(defined(my $line1 = <INPUT>)) {
   # First line caught by while, get the next seven lines using readline
   my $line2 = readline(INPUT);
   my $line3 = readline(INPUT);
   my $line4 = readline(INPUT);

   # Subtrings
   my $new_line2 = substr($line2, 0, $length+1);
   my $new_line4 = substr($line4, 0, $length);

   # Separate output
   print OUTPUT "$line1";
   print OUTPUT "$new_line2\n";
   print OUTPUT "$line3";
   print OUTPUT "$new_line4\n";
}

# Close files
close(INPUT);
close(OUTPUT);

exit();
