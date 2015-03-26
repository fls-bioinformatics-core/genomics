# Rcode.R
# R --no-save < SOLiD_qual_boxplot.R
# R --no-save 'arg1' 'arg2' < SOLiD_qual_boxplot.R
# Args: 'R'=1 '--no-save'=2 'arg1'=3 
# 
# Author: Ian Donaldson 1 August 2010
# Updated: Peter Briggs 16 February 2012
# Draws bars of a boxplot from individuals files (one per position in sequence reads)

#### Get argument for script
Args <- commandArgs()

fileName <- (Args[[3]])

#### Draw boxplot for sequence ordered data
###########################################

# filename
so_filename = paste(fileName, "seq-order_boxplot.ps", sep="_"); 

# turn on postscript
postscript(so_filename, paper = "a4", horizontal = TRUE)

# put all files in list
so_pattern = paste(basename(fileName), "posn*", sep="_")

#files <- list.files(pattern="qual_posn*")
files <- list.files(path=dirname(fileName),pattern=so_pattern,full.names=TRUE)

# Number of base pairs equal to number of files read in
bases = length(files)

# counter for current file
s=0

# list containing positions to draw colour
colours <- c(6,11,16,21,26,31,36,41,46)

# work thru each file in turn
for(i in files) {
   # increments for each file
   s = s+1

   # puts values from file into object
   values<-read.table(i, header=TRUE)

   # first position = first drawing of boxplot
   if(s==1){
      no_title = paste(basename(fileName), "Nucleotide order", sep=" - ")

      boxplot(values, xlim=c(0,bases), ylim=c(-1,35), outline=FALSE, boxfill=2, main=no_title)
   }

   # successive bars of plot without graph frames and axis, which increase the size of the .ps file
   # start of cycle draw colour
   else if (length(which(colours == s))) {
      boxplot(values,xlim=c(0,bases), ylim=c(-1,35), add=TRUE, at=s, axes=FALSE, boxfill="red", show.names=FALSE, outline=FALSE)
   }

   # successive bars of plot without graph frames and axis, which increase the size of the .ps file
   else{
      boxplot(values,xlim=c(0,bases), ylim=c(-1,35), add=TRUE, at=s, axes=FALSE, boxfill="cyan", show.names=FALSE, outline=FALSE)
   }
}

# Add X-axis labels - for start of each cycle
#
# Create a vector with empty strings (one vector element for each base)
axis_labels <- rep('',bases)
#
# Every five elements insert the base number (so we get 1,...,6,...11,... etc)
for(i in 1:bases) {
   if ((i-1) %% 5 == 0) {
      axis_labels[i] = toString(i)
   }
}
axis(1, at=axis_labels, labels=axis_labels)

# close postscript file
dev.off()
