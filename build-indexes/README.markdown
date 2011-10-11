build-indexes
=============

Scripts for setting up genome indexes for various programs:

 *  `build_indexes.sh`: build all indexes from a FASTA file
 *  `bfast_build_indexes.sh`: build bfast color-space indexes
 *  `bowtie_build_indexes.sh`: build color- and base-space bowtie indexes
 *  `srma_build_indexes.sh`: build indexes for srma

build_indexes.sh
----------------
Builds all indexes (bfast, bowtie, SRMA) within a standard directory
structure from a FASTA file, by running the scripts for building the
individual indexes.

### Usage ###

    build_indexes.sh <fasta_file>

### Outputs ###

Typically you would create a new directory for each organism, and then
place the FASTA file in a `fasta` subdirectory e.g.

    hg18/
        fasta/
             hg18.fasta

Then invoke this script from within the top-level `hg18` directory e.g.

    build_indexes.sh fasta/hg18.fasta

resulting in:

    hg18/
        fasta/
        bfast/
        bowtie/

with the indexes placed in the appropriate directories (see the
individual scripts for more details).

bfast_build_indexes.sh
----------------------
Builds the bfast color-space indexes from a reference FASTA file.

### Usage ###

    bfast_build_indexes.sh [OPTIONS] <genome_fasta_file>

Run with -h option to print full usage information.

### Options ###

* `-d <depth>` Specify depth-of-splitting used by Bfast (default 1)
* `-w <hash_width>` Specify hash width used by Bfast (default 14)
* `--dry-run` Print commands without executing them
* `-h` Print usage information and defaults

### Outputs ###

Index files are created in the directory the script was run in.

* `.bif` index files
* `.brg` index files for base- and color-space
* Symbolic link to the reference (input) FASTA file.

### Tips ###

*    If `.brg` and/or `.bif` files already exist then bfast index
     may not run correctly. It's recommended to remove any old files
     before rerunning the build script.

bowtie_build_indexes.sh
-----------------------
Builds the bowtie color and nucleotide space indexes from the reference
FASTA file.

### Usage ###

    bowtie_build_indexes.sh <genome_fasta_file>

### Outputs ###

Index files are created in the directory the script was run in.

* Nucleotide indexes as `<genome_name>.*.ebwt`
* Color space indexes as `<genome_name>_c.*.ebwt`

srma_build_indexes.sh
---------------------
Creates the index files required by SRMA.

### Setup ###

By default the script expects the `CreateSequenceDictionary.jar` file to be
in the `/usr/share/java/picard-tools` directory; if this is not the case then
set the variable `PICARD_TOOLS_DIR` variable in your environment to point to
the actual location.

For example for `bash`:

    export PICARD_TOOLS_DIR=/path/to/my/picard-tools

### Usage ###

    srma_build_indexes.sh <genome_fasta_file>

### Outputs ###

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
