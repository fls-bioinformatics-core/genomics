RNA-seq
=======

Scripts and tools for RNA-seq specific tasks.

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
