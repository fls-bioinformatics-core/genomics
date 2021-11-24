#! /usr/bin/perl -w
# my michael.james.clark
# found via Biostars: http://biostar.stackexchange.com/questions/5181/tools-to-calculate-average-coverage-for-a-bam-file

use strict;
my($num,$den)=(0,0);
while (my $cov=<STDIN>) {
    $num=$num+$cov;
    $den++;
}

my $cov=$num/$den;
print "Mean Coverage = $cov\n";
