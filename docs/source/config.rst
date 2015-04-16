Installation and set up
=======================

Installing the genomics/bcftbx package
**************************************

It is recommended to install directly from github using ``pip``::

    pip install git+https://github.com/fls-bioinformatics-core/genomics.git

from within the top-level source directory to install the package.

To use the package without installing it first you will need to add the
directory to your ``PYTHONPATH`` environment, and reference the scripts and
programs using their full paths.


Dependencies
************

The package consists predominantly of code written in Python, which has been
used extensively with Python 2.6 and 2.7.

In addition there are scripts requiring:

* ``bash``
* ``Perl``
* ``R``

and the following packages are required for subsets of the code:

* Perl: ``Statistics::Descriptive`` and ``BioPerl``
* python: ``xlwt``, ``xlrd`` and ``xlutils``

Finally, some of the utilities also use 3rd-party software packages,
including:

**Core software**

* ``bowtie`` http://bowtie-bio.sourceforge.net/index.shtml
* ``fastq_screen`` http://www.bioinformatics.bbsrc.ac.uk/projects/fastq_screen/
* ``convert`` (part of ``ImageMagick`` http://www.imagemagick.org/)

**Illumina-specific**

* ``BCL2FASTQ`` http://support.illumina.com/downloads/bcl2fastq_conversion_software_184.html
* ``FastQC`` http://www.bioinformatics.babraham.ac.uk/projects/fastqc/

**SOLiD-specific**

* ``solid2fastq`` (part of ``bfast`` http://sourceforge.net/projects/bfast/)
  - there are alternatives, see for example
  http://kevin-gattaca.blogspot.co.uk/2010/05/plethora-of-solid2fastq-or-csfasta.html
* ``SOLiD_preprocess_filter_v2.pl`` See https://www.biostars.org/p/71142/


Set up reference data
*********************

bowtie indexes
--------------

``fastq_screen`` needs bowtie indexes for each of the reference genomes that
you want to screen against.

The ``fetch_fasta.sh`` script can be used to acquire FASTA files for genome
builds of common reference organisms, for example::

    mkdir -p data/genomes/PhiX
    cd data/genomes/PhiX/
    fetch_fastas.sh PhiX

To generate bowtie indexes, use the ``bowtie_build_indexes.sh`` script, for
example::

    mkdir -p data/genomes/PhiX/bowtie
    cd data/genomes/PhiX/bowtie/
    bowtie_build_indexes.sh ../fasta/PhiX.fa

(This will create both colorspace and nucleotide space indexes by default.)

(Use ``bowtie2_build_indexes.sh`` to build indexes for bowtie2. Note that
bowtie2 does not support colorspace.)

(Alternatively use ``build_indexes.sh`` to make all the indexes: bfast, bowtie
and bowtie2, and SRMA.)

For rRNAs, get the ``rRNAs.tar.gz`` file and run the
``build_rRNA_bowtie_indexes.sh`` script, for example::

    cd data/genomes/
    wget .../rRNAs.tar.gz
    build_rRNA_bowtie_indexes.sh rRNAs.tar.gz

which will extract the FASTA sequences to a subdirectory ``rRNAs/fasta/`` and
create nucleotide- and colorspace bowtie indexes in ``rRNAs/bowtie``.

fastq_screen configuration files
--------------------------------

The QC scripts currently that there will be the following three ``fastq_screen``
configuration files:

* ``fastq_screen_model_organisms.conf``
* ``fastq_screen_other_organisms.conf``
* ``fastq_screen_rRNA.conf``

(The actual form of the names are::

    fastq_screen_<NAME><EXT>.conf

where ``<NAME>`` is one of ``model_organisms``, ``other_organisms`` or
``rRNA``, and ``<EXT>`` is an extension which is used to distinguish between
nucleotide- and colorspace indexes.)

Each configuration file defines "databases" with lines of the form::

    DATABASE	 Fly (dm3)	 /home/data/genomes/dm3/bowtie/dm3_het_chrM_chrU

for nucleotide space indexes, and
::

    DATABASE	 Fly (dm3)	 /home/data/genomes/dm3/bowtie/dm3_het_chrM_chrU_c

for colorspace. (In each case the path is the base name for the index files.)

.. _qc_setup:

Create `qc.setup`
*****************

When the package is installed a template ``qc.setup.sample`` file is
created in the ``config`` subdirectory - it needs to be copied to ``qc.setup``
and edited to set the locations for external software and data.
