build-indexes
=============

Scripts for setting up Genome Indexes.

bfast_build_indexes.sh
----------------------
Builds the bfast color-space indexes from a reference FASTA file.

### Usage: ###

    bfast_build_indexes.sh [OPTIONS] <genome_fasta_file>

Run with -h option to print full usage information.

### Outputs: ###

Index file are created in the directory the script was run in.

* `.bif` index files
* `.brg` index files for base- and color-space
* Symbolic link to the reference (input) FASTA file.

**NOTE:** by default "bfast index" is run with options -d 1 and -w 14
(specifying the hash width and depth of splitting respectively).
These options can be changed by specifying -d and/or -w when
running the script.

**NOTE:** use the --dry-run option to print the commands without
executing them.

**NOTE:** if .brg and/or .bif files already exist then bfast index
may not run correctly. It's recommended to remove any old files
before rerunning the build script.

bowtie_build_indexes.sh
-----------------------
Builds the bowtie color and nucleotide space indexes from the reference
FASTA file.

### Usage: ###

    bowtie_build_indexes.sh <genome_fasta_file>

### Outputs: ###

Index files are created in the directory the script was run in.

* Nucleotide indexes as `<genome_name>.*.ebwt`
* Color space indexes as `<genome_name>_c.*.ebwt`

srma_build_indexes.sh
---------------------
Creates the index files reqyure by SRMA.

### Setup: ###

Edit the `PICARD_TOOLS` variable in the script to point to the directory
holding the `CreateSequenceDictionary.jar` file.

### Usage: ###

    srma_build_indexes.sh <genome_fasta_file>

### Outputs: ###

Index files are created in the same directory as the reference FASTA file
(which is where SRMA requires them to be); the script itself can be run from
anywhere.

* `.fai` and `.dict` files required by SRMA.

index_indexes.sh
----------------
Utility for exploring/reporting on existing genome indexes within a directory
hierarchy.

### Usage ###

    index_indexes.sh <dir>

### Outputs ###

Searches <dir> and its subdirectories recursively and prints a report of the genome
index-specific files (fasta, info etc) it finds.

Note on preparing reference genome files
----------------------------------------
Where the reference genome is a collection of FASTA files for each
chromosome, it's necessary to prepare a single file for the bfast and
bowtie index generation by concatenating them together, e.g.:

    cat chr* > hg18_random_chrM.fa

The individual chromosome FASTA files can then be archived, e.g.:

    tar -cvf hg18_random_chrM.tar chr*
    gzip hg18_random_chrM.tar
