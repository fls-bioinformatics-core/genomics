#! /usr/bin/perl -w
#
# Look through fastq file from solid2fastq that has interleaved paired end reads
# and remove singletons (missing partner)
#
# Ian Donaldson 15 February 2012
use strict;
use warnings;

# Usage
unless(@ARGV==1) {
   die("USAGE $0 | interleaved FASTQ from solid2fastq\n\n")
}

# Files
open(INPUT, "<$ARGV[0]");
open(PAIR, ">$ARGV[0]\.pair\.header");
open(SINGLE, ">$ARGV[0]\.single\.header");
open(OUTPUT, ">$ARGV[0]\.paired");

# Loop thru till end of file
while(defined(my $line1 = <INPUT>)) {
   # First line caught by while, get the next seven lines using readline
   # This catches two fastq entries (4 lines each) and records the file position
   # of the end of the forth and eighth lines
   #print "$line1";
   my $line2 = readline(INPUT);
   #print "$line2";
   my $line3 = readline(INPUT);
   #print "$line3";
   my $line4 = readline(INPUT);
   #print "$line4";

   # Record end of forth line (end of first fastq entry)
   my $position1 = tell(INPUT);
   #print "$line1";

   if (defined(my $line5 = readline(INPUT))) {
       my $line6 = readline(INPUT);
       my $line7 = readline(INPUT);
       my $line8 = readline(INPUT);

       # Record end of eighth line (end of second fastq entry)
       my $position2 = tell(INPUT);
       #print "$lineA";

       # The header of the first and second fastq entries match
       if($line1 eq $line5) {
	   #print "$line1";
	   #print "$line5";

	   # Goto the end of the eighth line as both entries are a pair
	   seek(INPUT,$position2,0);
      
	   # Main output containing all fastq data
	   print OUTPUT "$line1";
	   print OUTPUT "$line2";
	   print OUTPUT "$line3";
	   print OUTPUT "$line4";
	   print OUTPUT "$line5";
	   print OUTPUT "$line6";
	   print OUTPUT "$line7";
	   print OUTPUT "$line8";

	   # Headers of paired entries (summary file)
	   print PAIR "$line1";
	   print PAIR "$line5";
       }

       # The headers  of the first and second entries are different, i.e. not a pair
       elsif($line1 ne $line5) {
	   # Goto the end of the first entry - ready to see if it is a pair with the next entry, in the next loop
	   seek(INPUT,$position1,0);
	   
	   # Headers of unpaired entires (summary file)
	   print SINGLE "$line1";
       }
   }

   # Next loop that will start according to the seek
   next;
}

# Close files
close(INPUT);
close(PAIR);
close(SINGLE);
close(OUTPUT);

exit();
