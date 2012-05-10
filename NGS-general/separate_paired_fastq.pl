#! /usr/bin/perl -w
#
# Takes a fastq file with paired F3 and F5 reads and separate into a file for each.
#
# Ian Donaldson 17 February 2012


# Usage
unless(@ARGV==1) {
   die("USAGE $0 | interleaved FASTQ\n\n")
}

# Files
open(INPUT, "<$ARGV[0]");
open(F3, ">$ARGV[0]\.F3");
open(F5, ">$ARGV[0]\.F5");

# Loop thru till end of file
while(defined(my $line1 = <INPUT>)) {
   # First line caught by while, get the next seven lines using readline
   # This catches two fastq entries (4 lines each)
   my $line2 = readline(INPUT);
   my $line3 = readline(INPUT);
   my $line4 = readline(INPUT);

   my $line5 = readline(INPUT);
   my $line6 = readline(INPUT);
   my $line7 = readline(INPUT);
   my $line8 = readline(INPUT);

   # Separate output
   print F3 "$line1";
   print F3 "$line2";
   print F3 "$line3";
   print F3 "$line4";
   print F5 "$line5";
   print F5 "$line6";
   print F5 "$line7";
   print F5 "$line8";
}

# Close files
close(INPUT);
close(F3);
close(F5);

exit();
