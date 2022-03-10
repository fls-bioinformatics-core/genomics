QC utilities
============

Scripts for running general QC and data preparation on sequencing data
prior to library-specific analyses.

* :ref:`fastq_strand`

.. _fastq_strand:

fastq_strand.py
***************

Utility to determine the strandedness (forward, reverse, or both) from
an R1/R2 pair of Fastq files.

Requires that the ``STAR`` mapper is also installed and available on the
user's ``PATH``.

**Usage examples:**

The simplest example checks the strandedness for a single genome::

    fastq_strand.py R1.fastq.gz R2.fastq.gz -g STARindex/mm10

In this example, ``STARindex/mm10`` is a directory which contains the
``STAR`` indexes for the ``mm10`` genome build.

The output is a file called ``R1_fastq_strand.txt`` which summarises the
forward and reverse strandedness percentages::

    #fastq_strand version: 0.0.1	#Aligner: STAR	#Reads in subset: 1000
    #Genome	1st forward	2nd reverse
    STARindex/mm10	13.13	93.21

To include the count sums for unstranded, 1st read strand aligned and
2nd read strand aligned in the output file, specify the ``--counts``
option::

    #fastq_strand version: 0.0.1	#Aligner: STAR	#Reads in subset: 1000
    #Genome	1st forward	2nd reverse	Unstranded	1st read strand aligned	2nd read strand aligned
    STARindex/mm10	13.13	93.21	391087	51339	364535

Strandedness can be checked for multiple genomes by specifying
additional ``STAR`` indexes on the command line with multiple ``-g``
flags::

    fastq_strand.py R1.fastq.gz R2.fastq.gz -g STARindex/hg38 -g STARindex/mm10

Alternatively a panel of indexes can be supplied via a configuration
file of the form::

    #Name	STAR index
    hg38	/mnt/data/STARindex/hg38
    mm10	/mnt/data/STARindex/mm10

(NB blank lines and lines starting with a ``#`` are ignored). Use the
``-c``/``--conf`` option to get the strandedness percentages using a
configuration file, e.g.::

    fastq_strand.py -c model_organisms.conf R1.fastq.gz R2.fastq.gz

By default a random subset of 1000 read pairs is used from the input
Fastq pair; this can be changed using the ``--subset`` option. If the
subset is set to zero then all reads are used.

The number of threads used to run ``STAR`` can be set via the ``-n``
option; to keep all the outputs from ``STAR`` specify the
``--keep-star-output`` option.

The strandedness statistics can also be generated for a single Fastq
file, by only specifying one file on the command line. E.g.::

    fastq_strand.py -c model_organisms.conf R1.fastq.gz
