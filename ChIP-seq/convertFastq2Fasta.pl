#/usr/bin/perl -w
# Based on Mark Richardson's script

#$name = $ARGV[0];

#if ($name =~ /(SH.+?)\./ ) {
#        $strain = $1;
#
#}

my $in_plus = 0;

while ($line = <>) {
	if ($line =~ /^\@(chr|2micron)/) {
                $line =~ s/\@/\>/;
		$in_plus = 0;
		print "$line";
		next;
	}

	if($in_plus == 0) {
		if($line =~ /\+\s/) {
			$in_plus = 1;
			next;
		}

		else {
			print "$line";
		}
	}
}
