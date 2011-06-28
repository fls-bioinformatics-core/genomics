#! /bin/bash
# Ian Donaldson 3 August 2010

# Get the directory name for this script
# The Perl and R scripts should be the same directory
QC_BOXPLOTTER_DIR=`dirname $0`

if [ $# != 1 ]; then
        echo "-----"
	echo "USAGE: ./colour_QC_script.sh *.qual"
	echo "This SHELL script will run two scripts to produce a boxplot of"	
	echo "SOLiD colorcall quality values from a .qual file." 
	echo "The first Perl script will split the .qual file columns in to"
        echo "separate files."
	echo "The second R script will plot the boxplot."	
        echo "By default all scripts need to be in the current directory."
        echo "DO NOT RUN IN PARALLEL IN SAME DIRECTORY!!!"
        echo "-----"
	exit
fi

# Input file and check it is present in directory
iFileN=$1

if test ! -s $iFileN ; then
	echo "$iFileN dosen't exist is empty!" 
    exit 
fi

# Report script location
echo "Running scripts from ${QC_BOXPLOTTER_DIR}"

# Check Perl script is present
# could add path to script
if test ! -s ${QC_BOXPLOTTER_DIR}/qual2Rinput_file_per_posn.pl ; then
        echo "qual2Rinput_file_per_posn.pl is missing from this directory!" 
    exit 
fi

# Check R script is present
# could add path to script
if test ! -s ${QC_BOXPLOTTER_DIR}/SOLiD_qual_boxplot.R ; then
        echo "SOLiD_qual_boxplot.R is missing from this directory!" 
    exit
fi

# Run file splitting command line
perl ${QC_BOXPLOTTER_DIR}/qual2Rinput_file_per_posn.pl $iFileN $iFileN

# Run R script on split files
R --no-save $iFileN < ${QC_BOXPLOTTER_DIR}/SOLiD_qual_boxplot.R

# Convert PS to PDF
if [ -e $iFileN\_seq-order_boxplot.ps ] ; then
    ps2pdfwr $iFileN\_seq-order_boxplot.ps $iFileN\_seq-order_boxplot.pdf
else
    echo Warning $iFileN\_seq-order_boxplot.ps not found
fi
if [ -e $iFileN\_primer-order_boxplot.ps ] ; then
    ps2pdfwr $iFileN\_primer-order_boxplot.ps $iFileN\_primer-order_boxplot.pdf
else
    echo Warning $iFileN\_primer-order_boxplot.ps
fi

# Rename output files based on $iFileN
#mv colour_quality_seq-order.ps $iFileN\_seq-order.ps
#mv colour_quality_primer-order.ps $iFileN\_primer-order.ps

# Remove files
rm $iFileN\_posn*
rm $iFileN\_pposn*

# Done
echo Finished!

exit
