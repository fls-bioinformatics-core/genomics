galaxy-scripts
==============

Some utility scripts for setting up Galaxy.

Genome Index Utilities
----------------------

- bfast_build_indexes.sh [OPTIONS] <genome_fasta_file>

  Builds the bfast color space indexes from the reference FASTA file.
  Indexes are .bif files created in the directory the script
  is run in. It also creates the .brg files for base and color space,
  and makes a symbolic link to the reference FASTA file.

  Run with -h option to print full usage information.

  NOTE: by default "bfast index" is run with options -d 1 and -w 14
  (specifying the hash width and depth of splitting respectively).
  These options can be changed by specifying -d and/or -w when
  running the script.

  NOTE: use the --dry-run option to print the commands without
  executing them.

  NOTE: if .brg and/or .bif files already exist then bfast index
  may not run correctly. It's recommended to remove any old files
  before rerunning the build script.

- bowtie_build_indexes.sh <genome_fasta_file>

  Builds the bowtie color and nucleotide space indexes from the reference
  FASTA file.
  Nucleotide indexes are <genome_name>.*.ebwt
  Color space indexes are <genome_name>_c.*.ebwt
  Index files are created in the directory the script is run in.

- srma_build_indexes.sh <genome_fasta_file>

  Creates the .fai and .dict files required by SRMA. Both files are
  created in the same directory as the reference FASTA file, which is
  where SRMA requires them to be; the script itself can be run from
  anywhere.

  (NOTE: that the path to the picard tools dir is hardcoded depending
  on the machine the script is being run on.)

Note on preparing reference genome files
----------------------------------------

Where the reference genome is a collection of FASTA files for each
chromosome, it's necessary to prepare a single file for the bfast and
bowtie index generation by concatenating them together, e.g.:

cat chr* > hg18_random_chrM.fa

The individual chromosome FASTA files can then be archived, e.g.:

tar -cvf hg18_random_chrM.tar chr*
gzip hg18_random_chrM.tar
