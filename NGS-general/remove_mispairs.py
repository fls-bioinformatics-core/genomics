#!/usr/bin/env python
#
# Remove "singleton" reads from fastq file
import sys
import os
import logging

# Put .. onto Python search path for modules
SHARE_DIR = os.path.abspath(
    os.path.normpath(
        os.path.join(os.path.dirname(sys.argv[0]),'..')))
sys.path.append(SHARE_DIR)
import bcftbx.FASTQFile as FASTQFile

# Main program
if __name__ == "__main__":
    # Collect input fastq file name
    if len(sys.argv) < 2:
        print("Usage: %s fastq" % os.path.basename(sys.argv[0]))
        sys.exit()
    fastq = sys.argv[1]
    # Output file names
    fastq_out = fastq+".paired"
    singles_header = fastq+".single.header"
    pairs_header = fastq+".pair.header"
    # Loop over file and collect read names
    headers = set()
    pairs = set()
    n = 1
    for read in FASTQFile.FastqIterator(fastq):
        seqid = str(read.seqid)
        if seqid in headers:
            # Part of a pair
            pairs.add(seqid)
        else:
            headers.add(seqid)
        n += 1
        if not (n % 1000000): print("%s" % n)
    # Loop again outputing only paired reads
    fp = open(fastq_out,'w')
    fp_singles = open(singles_header,'w')
    fp_pairs = open(pairs_header,'w')
    n = 1
    for read in FASTQFile.FastqIterator(fastq):
        seqid = str(read.seqid)
        if seqid in pairs:
            # Output one read from pair
            fp.write(str(read)+"\n")
            fp_pairs.write(seqid+"\n")
        else:
            # Singleton read
            fp_singles.write(seqid+"\n")
        n += 1
        if not (n % 1000000): print("%s" % n)
    # Close files
    fp.close()
    fp_singles.close()
    fp_pairs.close()
    
                
    
    
    
