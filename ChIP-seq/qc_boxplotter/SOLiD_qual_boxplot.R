# Rcode.R
# R --no-save < SOLiD_qual_boxplot.R
# R --no-save 'arg1' 'arg2' < SOLiD_qual_boxplot.R
# Args: 'R'=1 '--no-save'=2 'arg1'=3 
# 
# Author: Ian Donaldson 1 August 2010
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
      no_title = paste(fileName, "Nucleotide order", sep=" - ")

      boxplot(values, xlim=c(0,50), ylim=c(-1,35), outline=FALSE, boxfill=2, main=no_title)
   }

   # successive bars of plot without graph frames and axis, which increase the size of the .ps file
   # start of cycle draw colour
   else if (length(which(colours == s))) {
      boxplot(values,xlim=c(0,50), ylim=c(-1,35), add=TRUE, at=s, axes=FALSE, boxfill="red", show.names=FALSE, outline=FALSE)
   }

   # successive bars of plot without graph frames and axis, which increase the size of the .ps file
   else{
      boxplot(values,xlim=c(0,50), ylim=c(-1,35), add=TRUE, at=s, axes=FALSE, boxfill="cyan", show.names=FALSE, outline=FALSE)
   }
}

# Add X-axis labels - for start of each cycle
axis_labels <- c('1','','','','','6','','','','','11','','','','','16','','','','','21','','','','','26','','','','','31','','','','','36','','','','','41','','','','','46','','','','')
axis(1, at=axis_labels, labels=axis_labels)

# close postscript file
dev.off()


#### Draw boxplot for primer ligation ordered data
##################################################

# filename
po_filename = paste(fileName, "primer-order_boxplot.ps", sep="_"); 

# turn on postscript
postscript(po_filename, paper = "a4", horizontal = TRUE)

# put all files in list
po_pattern = paste(basename(fileName), "pposn*", sep="_")

#files <- list.files(pattern="qual_pposn*")
files <- list.files(path=dirname(fileName),pattern=po_pattern,full.names=TRUE)

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
      po_title = paste(fileName, "Primer order", sep=" - ")

      boxplot(values, xlim=c(0,50), ylim=c(-1,35), outline=FALSE, boxfill="red", main=po_title)
   }

   # successive bars of plot without graph frames and axis, which increase the size of the .ps file
   # start of cycle draw colour
   else if (length(which(colours == s))) {
      boxplot(values,xlim=c(0,50), ylim=c(-1,35), add=TRUE, at=s, axes=FALSE, boxfill="red", show.names=FALSE, outline=FALSE)
   }

   # successive bars of plot without graph frames and axis, which increase the size of the .ps file
   else{
      boxplot(values,xlim=c(0,50), ylim=c(-1,35), add=TRUE, at=s, axes=FALSE, boxfill="cyan", show.names=FALSE, outline=FALSE)
   }
}

# Add X-axis labels - for start of each cycle
axis_labels <- c('1','','','','','6','','','','','11','','','','','16','','','','','21','','','','','26','','','','','31','','','','','36','','','','','41','','','','','46','','','','')
axis(1, at=axis_labels, labels=axis_labels)


# close postscript file
dev.off()
