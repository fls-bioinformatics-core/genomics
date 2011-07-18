#!/bin/sh
#
# check_for_UCSC_tools.sh <Extra_UCSC_tools_dir>
#
# Script that checks the user's path plus the UCSC-tools directory for
# local versions of the UCSC executables available from
# http://hgdownload.cse.ucsc.edu/admin/exe/linux.x86_64/
#
# If a tool isn't found then the user is asked if they would like to
# download and add it to the UCSC-tools directory
#
if [ "$1" == "" ] ; then
    echo Please supply a directory for the UCSC tools
    exit 1
fi
EXTRA_UCSC_TOOLS=$1
export PATH=${PATH}:${EXTRA_UCSC_TOOLS}
#
cd $EXTRA_UCSC_TOOLS
#
UCSC_TOOLS="bedClip \
    bedExtendRanges \
    bedGraphToBigWig \
    bedItemOverlapCount \
    bedSort \
    bedToBigBed \
    bigBedInfo \
    bigBedSummary \
    bigBedToBed \
    bigWigAverageOverBed \
    bigWigInfo \
    bigWigSummary \
    bigWigToBedGraph \
    bigWigToWig \
    blat \
    faCount \
    faFrag \
    faOneRecord \
    faPolyASizes \
    faRandomize \
    faSize \
    faSomeRecords \
    faToNib \
    faToTwoBit \
    fetchChromSizes \
    genePredToGtf \
    gff3ToGenePred \
    gtfToGenePred \
    hgWiggle \
    htmlCheck \
    liftOver \
    liftOverMerge \
    liftUp \
    mafSpeciesSubset \
    mafsInRegion \
    makeTableList \
    nibFrag \
    overlapSelect \
    paraFetch \
    paraSync \
    pslCDnaFilter \
    pslPretty \
    pslReps \
    pslSort \
    sizeof \
    stringify \
    textHistogram \
    twoBitInfo \
    twoBitToFa \
    validateFiles \
    wigCorrelate \
    wigToBigWig"

missing_progs=
for prog in $UCSC_TOOLS ; do
    got_prog=`which $prog 2>&1 | grep -v "which: no"`
    if [ -z $got_prog ] ; then
	echo $prog: not found
	missing_progs="$missing_progs $prog"
	echo -n "Download $prog in $EXTRA_UCSC_TOOLS? [y/N]:"
	if [ $? == "y" ] ; then
	    echo Downloading...
	    wget http://hgdownload.cse.ucsc.edu/admin/exe/linux.x86_64/$prog
	    chmod +x $prog
	    echo Downloaded to $EXTRA_UCSC_TOOLS
	fi
    fi
done
if [ -z $missing_tools ] ; then
    echo All UCSC tools found
fi
##
#

