NGS utilities
=============

**************************
Reporting ChIP-seq outputs
**************************

The :ref:`reference_make_macs2_xls` utility can be used to convert an
output tab-delimited ``.XLS`` file from ``macs2`` into an MS Excel
spreadsheet (either ``.xlsx`` or ``.xls`` format).

Additionally a ``.bed`` format file can be output, provided that ``macs2``
was not run with the ``--broad`` option.

To process output from older versions of ``macs`` (i.e. 1.4.2 and earlier)
the legacy :ref:`reference_make_macs_xls` utility can be used; however for
this version only MS XLS format is supported, and there is no option to
output a ``.bed`` file.

*************************
Reporting RNA-seq outputs
*************************

The :ref:`reference_bowtie_mapping_stats` utility can be used to summarise
the mapping statistics produced by ``bowtie2`` or ``bowtie``, and output to
an MS Excel spreadsheet file.

The utility reads the ``bowtie2`` log file and expects this to consist of
multiple blocks of text of the form:

::

    ...
    <SAMPLE_NAME>
    Time loading reference: 00:00:01
    Time loading forward index: 00:00:00
    Time loading mirror index: 00:00:02
    Seeded quality full-index search: 00:10:20
    # reads processed: 39808407
    # reads with at least one reported alignment: 2737588 (6.88%)
    # reads that failed to align: 33721722 (84.71%)
    # reads with alignments suppressed due to -m: 3349097 (8.41%)
    Reported 2737588 alignments to 1 output stream(s)
    Time searching: 00:10:27
    Overall time: 00:10:27
    ...

The sample name will be extracted along with the numbers of reads processed,
with at least one reported alignment, that failed to align, and with
alignments suppressed and tabulated in the output spreadsheet.

*******************************************
Determining strandedness of sequencing data
*******************************************

The :ref:`reference_fastq_strand` utility can be used to determine the
strandedness (forward, reverse, or unstranded) of sequencing data in Fastq
format, using either a single Fastq file, or an an R1/R2 pair of Fastqs.

.. note::

   The utility is a wrapper for the ``STAR`` mapper and requires that
   ``STAR`` has been installed separately and is available on the
   ``PATH``.

The simplest example checks the strandedness for a single genome:

::

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
flags:

::

    fastq_strand.py R1.fastq.gz R2.fastq.gz -g STARindex/hg38 -g STARindex/mm10

Alternatively a panel of indexes can be supplied via a configuration
file of the form:

::

    #Name	STAR index
    hg38	/mnt/data/STARindex/hg38
    mm10	/mnt/data/STARindex/mm10

(NB blank lines and lines starting with a ``#`` are ignored). Use the
``-c``/``--conf`` option to get the strandedness percentages using a
configuration file,  For example:

::

    fastq_strand.py -c model_organisms.conf R1.fastq.gz R2.fastq.gz

By default a random subset of 1000 read pairs is used from the input
Fastq pair; this can be changed using the ``--subset`` option. If the
subset is set to zero then all reads are used.

The number of threads used to run ``STAR`` can be set via the ``-n``
option; to keep all the outputs from ``STAR`` specify the
``--keep-star-output`` option.

The strandedness statistics can also be generated for a single Fastq
file, by only specifying one file on the command line. For example:

::

    fastq_strand.py -c model_organisms.conf R1.fastq.gz


***************************************
Manage contaminant sequences for FastQC
***************************************

The :ref:`reference_manage_seqs` utility can to help create and
update files with lists of so-called "contaminant" sequences, for
input into the FastQC program (specifically, via FastQC's
``--contaminants`` option).

For example, to create a new contaminants file using sequences from a
FASTA file:

::

    manage_seqs.py -o custom_contaminants.txt sequences.fa

To append sequences to an existing contaminants file:

::

    manage_seqs.py -a custom_contaminants.txt additional_seqs.fa

The inputs can be a mixture of FastQC "contaminants" format and/or
Fasta format files). The utility also check for redundancy (i.e.
sequences with multiple associated names) and contradictions (i.e.
names with multiple associated sequences).

*******************************
Convert SAM file to SOAP format
*******************************

The :ref:`reference_sam2soap` utility converts a SAM file to SOAP
format.
