build-indexes
=============

Scripts for setting up genome indexes for various programs:

 *  `fetch_fasta.sh`: download and build FASTA file for pre-defined organisms
 *  `build_indexes.sh`: build all indexes from a FASTA file
 *  `bfast_build_indexes.sh`: build bfast color-space indexes
 *  `bowtie_build_indexes.sh`: build color- and base-space bowtie indexes
 *  `srma_build_indexes.sh`: build indexes for srma
 *  `setup_genome_indexes.sh`: automatically and reproducibly set up genome indexes
 *  `build_rRNA_bowtie_indexes.sh`: create indexes and fastq_screen.conf for rRNA

fetch_fasta.sh
--------------
Reproducibly downloads and builds FASTA files for pre-defined organisms.

### Usage ###

    fetch_fasta.sh <name>

`<name>` identifies a specific organism and build, for example 'hg18' or
`mm9` (run without specifying a name to see a list of all the available
organisms).

### Outputs ###

Downloads and creates a FASTA file for the specified organism and puts
this into a`fasta` subdirectory in the current working directory. When
possible the script verifies the FASTA file by running an MD5 checksum
it.

An `.info` file is also written which contains details about the FASTA
file, such as source location and additional operations that were performed
to unpack and construct the file, and the date and user who ran the script.

### Adding new organisms ###

New organisms can be added to the script by creating additional
`setup_<name>` functions for each, and defining the source and operations
required to build it. For example:

     function setup_hg18() {
         set_name    "Homo sapiens"
         set_species "Human"
         set_build   "HG18/NCBI36.1 March 2006"
         set_info    "Base chr. (1 to 22, X, Y), 'random' and chrM - unmasked"
         set_mirror  http://hgdownload.cse.ucsc.edu/goldenPath/hg18/bigZips
         set_archive chromFa.zip
         set_ext     fa
         set_md5sum  8cdfcaee2db09f2437e73d1db22fe681
         # Delete haplotypes
         add_processing_step "Delete haplotypes" "rm -f *hap*"
     }

See the comments in the head of the script along with the existing
`setup_...` functions for more specifics.

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

setup_genome_indexes.sh
-----------------------
Automatically and reproducibly set up genome indexes.

### Usage ###

    setup_genome_indexes.sh

The `setup_genome_indexes.sh` script doesn't take any options, it runs through
hard-coded lists of organisms for obtaining the sequence and creating bowtie, bfast
and Picard/SRMA indexes, Galaxy `.loc files` and `fastq_screen` `.conf` files.

### Outputs ###

The script outputs genome indexes based on the following directory structure for
each organism:

    pwd/
        organism/
                organism.info
                organism.chr.list
                bowtie/
                      ...bowtie indexes...
                bfast/
                      ...bfast indexes...
                fasta/
                      organism.fasta
		      ...picard/srma indexes...

It also creates:

 *   `fastq_screen` directory: containing specified `fastq_screen` `.conf` files
 *   Galaxy `.loc` files: for bowtie, bfast, picard, all_fasta and fastq_screen
 *   `genome_indexes.html` file: HTML file listing the available genome indexes


build_rRNA_bowtie_indexes.sh
-----------------------------
Create bowtie indexes and `fastq_screen.conf` file for rRNA sequences.

### Usage ###

    build_rRNA_bowtie_indexes.sh <rRNAs>.tar.gz

The `build_rRNA_bowtie_indexes.sh` script unpacks the supplied archive file
`<rRNAs>.tar.gz` and copies the FASTA-formatted sequence files it contains, then
generates bowtie indexes from these and produces a `fastq_screen.conf` file for
them.

### Inputs ###

The script expects the input `<rRNAs>.tar.gz` file to unpack into the following
directory structure:

   rRNAs/
	fasta/
             ... fasta files ...

### Outputs ###

The script creates the following directory structure in the current directory:

    pwd/
        rRNAs/
             bowtie/
                   ...bowtie indexes...
             fasta/
		   ...rRNA fasta files...

It also creates `fastq_screen_rRNAs.conf` in the `fastq_screen` subdirectory of
the current directory.


Note on preparing reference genome files
----------------------------------------
Where the reference genome is a collection of FASTA files for each
chromosome, it's necessary to prepare a single file for the bfast and
bowtie index generation by concatenating them together, e.g.:

    cat chr* > hg18_random_chrM.fa

The individual chromosome FASTA files can then be archived, e.g.:

    tar -cvf hg18_random_chrM.tar chr*
    gzip hg18_random_chrM.tar
