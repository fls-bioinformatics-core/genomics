#!/bin/sh
#
# boxplotps2png.sh: utility to generate PNGs from PS boxplots
#
# Usage: boxplotps2png.sh BOXPLOT1.ps [ BOXPLOT2.ps ... ]
#
# Outputs BOXPLOT1.png etc
#
# Check command line
if [ $# -lt 1 ] ; then
    echo "Usage: $0 BOXPLOT1.ps [ BOXPLOT2.ps ... ]"
    exit
fi
# 
# Use ImageMagick convert program to do the deed for each file
for i in $@ ; do
    # Check for postscript extension
    ext=${i##*.}
    if [ "$ext" == "ps" ] ; then
	boxplot_png=${i%.*}.png
	echo -n "Making $boxplot_png..."
	convert -rotate 90 $i -background white -flatten -resize 1060x750 -antialias $boxplot_png
	echo "done"
    else
	echo "$i: not a postscript file"
    fi
done
exit
##
#
