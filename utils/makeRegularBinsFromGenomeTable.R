#!/usr/bin/Rscript

#######################################################
#
#       Dave Gerrard, University of Manchester
#       2011
#
######################################################


########FUNCTIONS


###########################################

# plan to be able to call this script thus: Rscript script.R arg1 arg2 ..
# get args from call
Args <- commandArgs(TRUE)

if(length(Args) != 2)  { 
	stop("Usage: makeRegularBinsFromGenomeTable.R [Genome Table File] [binSize]\n
		Make a bed file with bins of size [binSize] filling every chrom specified in [Genome Table File]
		Does something...
	")
	
}


old.o <- options("scipen"= 15)

chromTable <- read.table(Args[1]) 
binSize <- as.numeric(Args[2])
outputFileName <- paste(Args[1], binSize, "bp","bins","bed",sep=".")


for (i in 1:nrow(chromTable)) {

	this_chrom <- as.character(chromTable[i,1])
	chr_length <- as.numeric(chromTable[i,2] )
	
	if (binSize > chr_length)  {	# binSize is greater than chromosome length (e.g. chrM and contigs).
		write.table(cbind(this_chrom, 0, chr_length), file=outputFileName, append=T, quote=F,row.names=F, col.names=F,sep="\t")
	} else {
		starts <- seq(from=0, to=(chr_length - 1), by=binSize )
		ends <-  starts + binSize
		ends[length(ends)] <- chr_length # shorten the last bin to end of chromosome
		table <- cbind(this_chrom, starts, ends)

		#table[,2:3] <- format(table[,2:3], scientific = FALSE)


		write.table(table, file=outputFileName, append=T, quote=F,row.names=F, col.names=F,sep="\t") 
	}
}	



options(old.o)





