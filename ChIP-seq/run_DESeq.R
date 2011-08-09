#!/usr/bin/Rscript

# R script to run DESeq.  Conditions hard-wired!
#
# Input file 5 columns:
# - 'Regions' chr_start_end for regions
# - Cond A - rep1
# - Cond A - rep2
# - Cond B - rep1
# - Cond B - rep2
#
# Ian Donaldson. 8 August 2011

# get args from call
Args <- commandArgs(TRUE)

if(length(Args) != 3)  { 
   stop("Usage: runDESeq.R [input file] [generic figure label] [output file]\n
   Run DESeq in R using a tab delimited file [input file] that has a column of chr_start_end called 'regions'
   and four columns of read counts for timeA_rep1 timeA_rep2 timeB_rep1 timeB_rep2 ('conds' order hard-wired).  
   A [generic figure label] adds specificity to the output diagrams (hard-wired). The final [output file] is
   created. 
   ")
}

inFile <- Args[1]
label <- Args[2]
outFile <- Args[3]

# DESeq in R:
library(DESeq)

# Make a input table
counts <- read.delim(file=inFile, header=TRUE, stringsAsFactors=TRUE)

# Give rows names from first col (‘regions’)
rownames ( counts ) <- counts$region

# Remove region column
counts <- counts[ , -1 ]

# Conditions, e.g. A= 2 to 2.5hr and B= 3 to 3.5hr
conds <- c("A", "A", "B", "B")

# Count data set
cds <- newCountDataSet (counts, conds)

# Estimate effective library size - better results when estimating from count data (tutorial)
cds <- estimateSizeFactors( cds )

sizeFactors( cds )

# Variance estimation
cds <- estimateVarianceFunctions( cds )

# Plot squared coefficients of variation (SCV) estimates of variation
scv_label <- paste(label, "SCV_plot.png", sep="_");
png(file=scv_label)
scvPlot( cds, ylim=c(0,2) ) 
dev.off()

# Variance fit diagnostics
# i.e. does the best fit line follow the single event estimates of variation
diagForA <- varianceFitDiagnostics( cds, "A")
diagForB <- varianceFitDiagnostics( cds, "B")

#Plot for A:
diagA_label <- paste(label, "varDiagnosticA.png", sep="_");
png(file=diagA_label)
smoothScatter( log10(diagForA$baseMean), log10(diagForA$baseVar) )
lines( log10(fittedBaseVar) ~ log10(baseMean), diagForA[ order(diagForA$baseMean), ], col="red" )
dev.off()

#Plot for B:
diagB_label <- paste(label, "varDiagnosticB.png", sep="_");
png(file=diagB_label)
smoothScatter( log10(diagForB$baseMean), log10(diagForB$baseVar) )
lines( log10(fittedBaseVar) ~ log10(baseMean), diagForB[ order(diagForB$baseMean), ], col="red" )
dev.off()

#Empirical cumulative density functions (ECDF) plot
ecdf_label <- paste(label, "ECDF.png", sep="_");
png(file=ecdf_label, width = 800, height = 480, units = "px")
par( mfrow=c(1,2 ) )
residualsEcdfPlot( cds, "A" )
residualsEcdfPlot( cds, "B" )
dev.off()

# Calculating differential expression
res <- nbinomTest( cds, "A", "B" )

# Write output
write.table(res, file=outFile, quote=F, sep="\t", row.names=F)

# Finish
quit(save="no")
