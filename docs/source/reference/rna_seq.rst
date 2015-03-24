RNA-seq
=======

Scripts and tools for RNA-seq specific tasks.

  * ``bowtie_mapping_stats.py``: summarise statistics from bowtie output in spreadsheet
  * ``GFFedit``: swap gene names in GFF file to gene ID
  * ``qc_bash_script.sh``: generalised QC pipeline for RNA-seq
  * ``Split``: filter reads from bowtie mapping against two genomes


bowtie_mapping_stats.py
***********************
Extract mapping statistics for each sample referenced in the input bowtie log
files and summarise the data in an XLS spreadsheet. Handles output from both
Bowtie and Bowtie2.

Usage::

    bowtie_mapping_stats.py [options] bowtie_log_file [ bowtie_log_file ... ]

By default the output file is called ``mapping_summary.xls``; use the ``-o`` option to
specify the spreadsheet name explicitly.

Options:

.. cmdoption:: -o xls_file

    specify name of the output XLS file (otherwise defaults to ``mapping_summary.xls``).


.. cmdoption:: -t

    write data to tab-delimited file in addition to the XLS file. The tab file will
    have the same name as the XLS file, with the extension replaced by ``.txt``

Input bowtie log file
---------------------

The program expects the input log file to consist of multiple blocks of text of the form::

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

The sample name will be extracted along with the numbers of reads processed, with at least one
reported alignment, that failed to align, and with alignments suppressed and tabulated in the
output spreadsheet.

GFFedit
*******

Takes a GFF file and edits it, changing gene names in the input file to the geneID (if
they are not of the DDB_G0...format), and outputs the edited GFF file.

Compilation::

    javac GFFedit.java
    jar cf GFFedit.jar GFFedit.class

Usage::

    java -cp /path/to/GFFedit.jar GFFedit <myfile>.gff

Arguments:

.. cmdoption:: myfile.gff

    input GFF file

Output:

.. cmdoption:: GFFedit_<myfile>.gff

    edited version of input file

qc_bash_script.sh
*****************

Generalised QC pipeline for RNA-seq: runs bowtie, fastq_screen and
qc_boxplotter on SOLiD data.

Usage::

    qc_bash_script.sh <analysis_dir> <sample_name> <csfasta> <qual> <bowtie_genome_index>

Arguments:

.. cmdoption:: analysis_dir

    directory to write the outputs to

.. cmdoption:: sample_name

    name of the sample

.. cmdoption:: csfasta

    input csfasta file

.. cmdoption:: qual

    input qual file

.. cmdoption:: bowtie_genome_index

    full path to bowtie genome index

Outputs:

Creates a ``qc`` subdirectory in ``analysis_dir`` which contains the fastq_screen
and boxplotter output files.

Split
*****

Takes in two SAM files from bowtie where the same sample has been mapped to
two genomes ("genomeS" and "genomeB"), and filters the reads to isolate those
which map only to genomeS, only to genomeB, and to both genomes (see "Output",
below).

Compilation::

    javac Split.java
    jar cf Split.jar Split.class

Usage::

    java -cp /path/to/Split.jar Split <map_to_genomeS>.sam <map_to_genomeB>.sam

Arguments:

.. cmdoption:: map_to_genomeS.sam

    SAM file from Bowtie with reads mapped to genomeS

.. cmdoption:: map_to_genomeB.sam

    SAM file from Bowtie with reads mapped to genomeB

Outputs 4 SAM files:

1. Reads that map to genomeS only
2. Reads that map to genomeB only
3. Reads that map to genomeS and genomeB keeping the genomeS genome coordinates
4. Reads that map to genomeS and genomeB keeping the genomeB genome coordinates

