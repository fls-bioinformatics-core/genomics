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
