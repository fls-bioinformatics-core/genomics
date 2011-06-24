#!/bin/sh
#
# Dirty utility script to convert a SAM bitwise flag from decimal
# to binary representation, pad with zeros and then interpret
# what each bit means
#
# An online tool to do this is at
# http://picard.sourceforge.net/explain-flags.html
#
# See also:
# http://ppotato.wordpress.com/2010/08/25/samtool-bitwise-flag-paired-reads/
# http://seqanswers.com/forums/showthread.php?t=2301
#
echo Explain SAM flags in plain English
echo ==================================
echo
echo Convert a decimal SAM flag to binary representation and
echo print explanation of each bit.
echo See also http://picard.sourceforge.net/explain-flags.html
echo
echo "Usage: $0 <flag_value>"
echo
function isset() {
    if [ $1 == "1" ] ; then
	echo "YES $2"
    else
	echo "    $2"
    fi
}
if [ -z $1 ] ; then
    echo "No decimal flag value supplied"
    exit 1
fi
echo Decimal flag = $1
#
# Convert decimal to binary
bin=`echo "ibase=10; obase=2; $1" | bc`
#
# Pad with zeros
# FIXME This is horrible!
pad=12
len=`echo $bin | wc -c`
while [ $len -lt $pad ] ; do
    bin="0$bin"
    len=`echo $bin | wc -c`
done
echo Binary equivalent = $bin
echo
#
# Reverse
bin=`echo $bin | rev`
#
# Explain
echo Explanation:
echo ============
isset ${bin:0:1} "read paired"
isset ${bin:1:1} "read mapped in proper pair"
isset ${bin:2:1} "read unmapped"
isset ${bin:3:1} "mate unmapped"
isset ${bin:4:1} "read reverse strand"
isset ${bin:5:1} "mate reverse strand"
isset ${bin:6:1} "first in pair"
isset ${bin:7:1} "second in pair"
isset ${bin:8:1} "not primary alignment"
isset ${bin:9:1} "read fails platform/vendor quality checks"
isset ${bin:10:1} "read is PCR or optical duplicate"