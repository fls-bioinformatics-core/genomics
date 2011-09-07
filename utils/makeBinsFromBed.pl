#! /usr/bin/perl -w

#######################################################
#
#	Dave Gerrard, University of Manchester
#	2011
#
######################################################

use Getopt::Long;	# for option parsing
use POSIX;		# for rounding to integers
use Switch;		# for switch/case structure

if(@ARGV==0)  {
	die("USAGE: $0 [options] BED_FILE OUTPUT_FILE\n", 
"--marker [ midpoint | start | end | tss | tts ]
	On which component of feature to position the bin(s) (default midpoint).
	tss: transcription start site (using strand)
	tts: transcription termination site (using strand)	

--binType [ centred | upstream | downstream ]
	How to position the bin relative to the feature (default centred).
	If marker is start/end, position is relative to chromosome. 
	If marker is tss/tts, position is relative to strand of feature	
--offset n
	All bins are shifted by this many bases (default 0).
	If marker is start/end, n is relative to chromosome. 
	If marker is tss/tts, n is relative to strand of feature

--binSize n
	The size of the bins (default 200)
	
--makeIntervalBins n
	n bins are made of equal size within the feature. 
	The bins begin, and are numbered from, the marker.
	If > 0, ignores binSize, offset and binType.
	Incompatible with --marker midpoint \n
TIPS:
	To create single bp of the tss, use:  
		--marker tss  --binSize 1 --binType downstream
	To get a bin of 1000bp ending 500bp upstream of the tss, use: 
		--marker tss  --binSize 1000 --binType upstream --offset -500\n");
}


# option variables with default value
my $marker = "midpoint" ;
my $binType = "centred"; 
my $offset = 0 ;
my $binSize = 200 ; 
my $makeIntervalBins = 0; 

GetOptions (
	'marker=s' => \$marker,
	'binType=s' => \$binType,
	'offset=i' => \$offset,
	'binSize=i' => \$binSize,
	'makeIntervalBins=i' => \$makeIntervalBins
	);



print "marker\tbinType\toffset\tbinSize\tmakeIntervalBins\n" ;
print "$marker\t$binType\t$offset\t$binSize\t$makeIntervalBins\n" ;

my $inFileName = $ARGV[0];
my $outFileName = $ARGV[1] ;

if(($makeIntervalBins gt 0) && ($marker eq 'midpoint'))  {
	die "Incompatible parameters:- marker= $marker, binType=$binType, offset=$offset, binSize=$binSize, makeIntervalBins=$makeIntervalBins\n";
}


open (INPUT,"<$inFileName") or die "failed to open $inFileName\n";
open (OUTPUT, ">$outFileName") or die "failed to open $outFileName\n" ;
my $featureCount = 0 ;

while(defined(my $line = <INPUT>)) {

	# skip lines starting with comments,  blank lines, or 'track'
	if($line=~/(^\s|^#|^track)/) { next }
	chomp($line);
	$featureCount++ ;
	my($chr, $start, $end, $featName, $score, $strand) = '';

	($chr, $start, $end, $featName, $score, $strand) = split(/\t/, $line);
	#if(!defined($strand) || ( $strand ne '-' && $strand ne '+'))  {
	#       if(defined($score) && ($score eq '+') || ($score eq '-'))  {               # irregular bed file. Might be useful strand info in column 5.
        #	        $strand  = $score ;
	#        }
	#		
	#}
	
	#if(($score eq '+') || ($score eq '-'))  {		# irregular bed file. Might be useful strand info in column 5.
	#	$strand  = $score ; 
	#}
	#if (($marker eq 'tss' || $marker eq 'tts') && ($strand ne '-' && $strand ne '+') ) {
	 if (($marker eq 'tss' || $marker eq 'tts') && (!defined($strand))) {
		die "$marker specified as marker but cannot find strand information for feature $featureCount\n" ;
	}	

	
	my $binBaseName = '';
	if (defined($featName)) {
		$binBaseName = $featName ; 
	} else {
		$binBaseName = join(".",$inFileName,$featureCount) ; 
	}
	my $binStart ;
	my $binEnd ;
	if($makeIntervalBins > 0)  { 		## make interval bins
		my $featWidth = $end - $start ;
		my $intBinWidth = floor($featWidth / $makeIntervalBins ) ;
		#my $ascending = 1 ;
		if ($marker eq 'start' || ( $marker eq 'tss' && $strand eq '+' ) || ($marker eq 'tts' && $strand eq '-'))  {
			#print "made it to intervalbins plus\n" ;
			#$ascending = 1;
			$binStart = $start ;
			$binEnd = $start + $intBinWidth ;
			for( $i =1 ; $i <= $makeIntervalBins; $i++)  {
				$binName = join(".",$binBaseName,"intervalFrom",$marker,$i) ;
				print OUTPUT "$chr\t$binStart\t$binEnd\t$binName\n";		
				$binStart = $binEnd;
				$binEnd = $binStart + $intBinWidth;
			}
		} else {
			#$ascending = 0;
                        #print "made it to intervalbins minus\n" ;
                        $binEnd = $end ;
			$binStart = $end - $intBinWidth ;
                        for( $i =1 ; $i <= $makeIntervalBins; $i++)  {
                                $binName = join(".",$binBaseName,"intervalFrom",$marker,$i) ;
				print OUTPUT "$chr\t$binStart\t$binEnd\t$binName\n";
				$binEnd = $binStart;
				$binStart = $binEnd - $intBinWidth;
                        }			
		}
	} else  {				## make a regular bin
		my $focalPoint;    # probably not the most efficient but might stop me going insane trying to think of all combinations.
		if ($marker eq 'midpoint') {
			$focalPoint = floor($end - $start) + $start ;
		
		} elsif ($marker eq 'start' || ( $marker eq 'tss' && $strand eq '+' ) || ($marker eq 'tts' && $strand eq '-'))  {	
			$focalPoint = $start ;		
		} elsif ($marker eq 'end' || ($marker eq 'tts' && $strand eq '+') || ($marker eq 'tss' && $strand eq '-'))  {
			$focalPoint = $end ;
		} else {
			die "Cannot set focalPoint:-\n marker= $marker, binType=$binType, offset=$offset, binSize=$binSize, makeIntervalBins=$makeIntervalBins\n"; 	
		}

		# now set the bin margins. 
		if ($binType eq 'centred')  {
			$binStart = $focalPoint - floor($binSize/2) ;
			$binEnd = $binStart + $binSize ;
		} elsif (($marker eq 'start') || ($marker eq 'end') || ($strand eq '+' && ($marker eq 'tss'  || $marker eq 'tts' )))  {
			switch ($binType)  {			
				case 'upstream'   { 
					$binEnd = $focalPoint ;
					$binStart = $binEnd - $binSize;
				}
				case 'downstream' {  
					$binStart = $focalPoint ;
					$binEnd = $binStart + $binSize;
				}		
			}
		} elsif ($strand eq '-' && ( $marker eq 'tss' || $marker eq 'tts'))  {
			switch ($binType)  {
				case 'upstream'  {
                                        $binStart = $focalPoint ;
                                        $binEnd = $binStart + $binSize;					
				}
				case 'downstream' {
                                        $binEnd = $focalPoint ;
                                        $binStart = $binEnd - $binSize;					
				}
			}
		} else {
			 die "Cannot set bin margins:-\n marker= $marker, binType=$binType, offset=$offset, binSize=$binSize, makeIntervalBins=$makeIntervalBins\n";
		}

		$binName = join(".",$binBaseName,$marker,$binSize,$binType) ;		
		if ($offset != 0)  {		
			# Might need to change sign to account for strand if tss,tts
			my $tempOffSet = $offset ;
			if ($strand eq '-' && ($marker eq 'tss' || $marker eq 'tts'))  {
				$tempOffSet = 0 - $offset ;	
			}
			$binStart = $binStart + $tempOffSet ;
			$binEnd = $binEnd + $tempOffSet ;
			$binName = join(".", $binName,"offsetBy",$offset) ;
		}
		if ($binStart < 0) {
			$binStart = 0;
			print "WARNING: bin starts below zero set to 0\n" ;
		}
		if ($binEnd < 1)  {
			$binEnd = 1;
			print "WARNING: bin ends below one set to 1\n" ;
		}
		print OUTPUT "$chr\t$binStart\t$binEnd\t$binName\n";
	}

	
}
