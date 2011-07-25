RNA-seq
=======

Scripts and tools for RNA-seq specific tasks.

GFFedit
-------
Takes a GFF file and edits it, changing gene names in the input file
to the geneID (if they are not of the DDB_G0...format), and outputs the
edited GFF file.

Compilation:

    javac GFFedit.java
    jar cf GFFedit.jar GFFedit.class

Usage:

    java -cp /path/to/GFFedit.jar GFFedit <myfile>.gff

Arguments:

* `myfile.gff`: input GFF file

Output:

* `GFFedit_<myfile>.gff`: edited version of input file

qc_bash_script.sh
-----------------
Generalised QC pipeline for RNA-seq: runs bowtie, fastq_screen and
qc_boxplotter on SOLiD data.

Usage:

    qc_bash_script.sh <analysis_dir> <sample_name> <csfasta> <qual> <bowtie_genome_index>

Arguments:

 *  `analysis_dir`: directory to write the outputs to
 *  `sample_name`: name of the sample
 *  `csfasta`: input csfasta file
 *  `qual`: input qual file
 *  `bowtie_genome_index`: full path to bowtie genome index

Outputs:

Creates a `qc` subdirectory in `analysis_dir` which contains the fastq_screen
and boxplotter output files.

Split
-----
Takes in two SAM files from bowtie where the same sample has been mapped to
two genomes ("genomeS" and "genomeB"), and filters the reads to isolate those
which map only to genomeS, only to genomeB, and to both genomes (see "Output",
below).

Compilation:

    javac Split.java
    jar cf Split.jar Split.class

Usage:

    java -cp /path/to/Split.jar Split <map_to_genomeS>.sam <map_to_genomeB>.sam

Arguments:

* `map_to_genomeS.sam`: SAM file from Bowtie with reads mapped to genomeS
* `map_to_genomeB.sam`: SAM file from Bowtie with reads mapped to genomeS

Output:

4 SAM files:

1. Reads that map to genomeS only
2. Reads that map to genomeB only
3. Reads that map to genomeS and genomeB keeping the genomeS genome coordinates
4, Reads that map to genomeS and genomeB keeping the genomeB genome coordinates
