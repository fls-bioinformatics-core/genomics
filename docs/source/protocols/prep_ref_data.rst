Reference data preparation
==========================

Genome sequence data and indexes
********************************

Suggested structure
-------------------

For a given genome build, the recommended basic structure is (e.g. for *Rattus
norvegicus* ``rn4``)::

 rn4/
  |
  +- rn4.info  (metadata file)
  |
  +- fasta/    (sequences)
  |
  +- bowtie/   (indexes for bowtie - both color- and letterspace)
  |
  +- bfast/    (indexes for bfast)
  |
  +- liftOver/ (chain files for liftOver from this assembly to others)
  |
  +- seq/      (per-chromosome nib files for sequence alignments)
  |
 ...

i.e. a top-level directory containing a ``.info`` file, plus directories for
FASTA sequences and derived or additional genome indexes for various aligners
and other programs.

Note that the indexes for SRMA are placed in the "fasta" directory, as SRMA needs .fa, .fai and .dict files all to be placed in the same directory.

Creating a directory for a new genome
-------------------------------------

To add a new genome index:

* Create a new top-level directory for the organism and genome build
* Create a ``fasta`` subdirectory to hold the sequence data, and download
  and prepare the FASTA file(s) within this directory (see below for hints)
* Create a ``.info`` file and record the details of the genome for future
  reference (see below for more detail on .info files)
* Create and populate ``bowtie``, ``bfast`` etc subdirectories with the
  appropriate indexes (see below for advice on generating indexes) 

Preparing fasta genome files
----------------------------

Where the reference genome is a collection of fasta files for each chromosome,
it's necessary to prepare a single file for the bfast and bowtie index
generation by concatenating them together, e.g.::

    cat chr* > hg18_random_chrM.fa

The individual chromosome fasta files can then be removed or archived, e.g.::

    tar -cvf hg18_random_chrM.tar chr*
    gzip hg18_random_chrM.tar

Metadata in .info files
***********************

Standard practice when add a new genome index is to also create a ``.info``
file (for example ``hg18_random_chrM.info``).

These are hand-generated text files consisting of header fields followed by
free text.

A typical header looks like (e.g. from ``mm9_random_chrM.info`` for *Mus musculus*
``mm9``)::

    # Organism: Mus musculus
    # Genome Build: MM9/NCBI37 July 2007
    # Manipulations: Base chr. (1 to 19, X, Y), chrN_random, chrM and chrUn_random - unmasked
    # Source: wget http://hgdownload.cse.ucsc.edu/goldenPath/mm9/bigZips/chromFa.tar.gz

The free text area can contain any additional information that the person preparing
the indexes thinks is important (for example, scripts or commands used to generate
the indexes for individual programs).

Scripts for index generation
****************************

This package includes a number of scripts for fetching and generating genome
indexes for ``Bfast``, ``Bowtie`` and ``SRMA``.

fetch_fasta.sh: download FASTA files
------------------------------------

The ``fetch_fasta.sh`` script is intended to reproducibly create FASTA files
for a set of genomes.

To see which genomes are available run the program without any arguments; to
obtain the FASTA file do e.g.::

    fetch_fasta.sh mm9

bowtie_build_indexes.sh: bowtie indexes
---------------------------------------

The script bowtie_build_indexes.sh can be used to generate color- and
nuleotide-space indexes from a FASTA file.

To use, go to the bowtie subdirectory for the genome and do e.g.::

    qsub -b y -V -cwd bowtie_build_indexes.sh ../fasta/genome.fa

This will create both color and nucleotide space indexes; to only generate
colorspace use the ``--cs`` option of the script, to only get nucleotide
space use ``--nt``.

bfast_build_indexes.sh: bfast indexes
-------------------------------------

``bfast_build_indexes.sh`` automates the steps required to prepare indexes
for ``bfast``.

srma_build_indexes.sh: SRMA indexes
-----------------------------------

``srma_build_indexes.sh`` automates the steps required to prepare indexes
for ``SRMA``. 
