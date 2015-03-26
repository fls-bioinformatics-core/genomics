NGS-general
===========

General NGS scripts that are used for both ChIP-seq and RNA-seq.

* ``explain_sam_flag.sh``: decodes bit-wise flag from SAM file
* ``extract_reads.py``: write out subsets of reads from input data files
* ``fastq_edit.py``: edit FASTQ files and data
* ``fastq_sniffer.py``: "sniff" FASTQ file to determine quality encoding
* ``SamStats``: counts uniquely map reads per chromosome/contig
* ``splitBarcodes.pl``: separate multiple barcodes in SOLiD data
* ``remove_mispairs.pl``: remove "singleton" reads from paired end fastq
* ``remove_mispairs.py``: remove "singleton" reads from paired end fastq
* ``separate_paired_fastq.pl``: separate F3 and F5 reads from fastq
* ``trim_fastq.pl``: trim down sequences in fastq file from 5' end
* ``uncompress_fastqgz.sh``: create ungzipped version of a compressed FASTQ
  file

.. _explain_sam_flag:

explain_sam_flag.sh
*******************

Convert a decimal bitwise SAM flag value to binary representation and
interpret each bit.

.. _extract_reads:

extract_reads.py
****************

Usage::

    extract_reads.py OPTIONS infile [infile ...]

Extract subsets of reads from each of the supplied files according to
specified criteria (e.g. random, matching a pattern etc). Input files
can be any mixture of FASTQ (``.fastq``, ``.fq``), CSFASTA
(``.csfasta``) and QUAL (``.qual``).

Output file names will be the input file names with ``.subset``
appended.

Options:

.. cmdoption:: -m PATTERN, --match=PATTERN

    Extract records that match Python regular expression
    ``PATTERN``

..cmdoption:: -n N

    Extract ``N`` random records from the input file(s)
    (default 500). If multiple input files are specified,
    the same subsets will be extracted for each.

.. _fastq_edit:

fastq_edit.py
*************

Usage::

    fastq_edit.py [options] <fastq_file>

Perform various operations on FASTQ file.

Options:

.. cmdoption:: --stats

    Generate basic stats for input FASTQ

.. cmdoption:: --instrument-name=INSTRUMENT_NAME

    Update the ``instrument name`` in the sequence
    identifier part of each read record and write updated
    FASTQ file to stdout

.. _fastq_sniffer:

fastq_sniffer.py
****************

Usage::

    fastq_sniffer.py <fastq_file>

"Sniff" FASTQ file to try and determine likely format and quality
encoding.

Attempts to identify FASTQ format and quality encoding, and suggests
likely datatype for import into Galaxy.

Use the ``--subset`` option to only use a subset of reads from the
file for the type determination (using a smaller set speeds up the
process at the risk of not being able to accuracy determine the
encoding convention).

See http://en.wikipedia.org/wiki/FASTQ_format for information on
the different quality encoding standards used in different FASTQ
formats.

Options:

.. cmdoption:: --subset=N_SUBSET

    try to determine encoding from a subset of consisting of
    the first ``N_SUBSET`` reads. (Quicker than using all reads
    but may not be accurate if subset is not representative
    of the file as a whole.)

.. _samstats:

SamStats
********

Counts how many reads are uniquely mapped onto each chromosome or
contig in a SAM file. To run::

    java -classpath <dir_with_SamStats.class> SamStats <sam_file>

or (if using a Jar file)::

    java -cp /path/to/SamStats.jar SamStats <sam_file>

(To compile into a jar, do ``jar cf SamStats.jar SamStats.class``)

Output is a text file ``SamStats_maponly_<sam_file>.stats``

.. _splitbarcodes:

splitBarcodes.pl
****************

Split csfasta and qual files containing multiple barcodes into separate
sets.

Usage::

    ./splitBarcodes.pl <barcode.csfasta> <read.csfasta> <read.qual>

Expects BC.csfasta, F3.csfasta and F3.qual files containing multiple
barcodes. Currently set up for 'BC Kit Module 1-16'.

Note that this utility also requires `BioPerl`.

.. _remove_mispairs:

remove_mispairs.pl
******************

Look through fastq file from solid2fastq that has interleaved paired
end reads and remove singletons (missing partner)

Usage::

    remove_mispairs.pl <interleaved FASTQ>

Outputs:

* ``<FASTQ>.paired``: copy of input fastq with all singleton reads
  removed
* ``<FASTQ>.single.header``: list of headers for all reads that were
  removed as singletons
* ``<FASTQ>.pair.header``: list of headers for all reads there were
  kept as part of a pair

.. _remove_mispairs_py:

remove_mispairs.py
******************

Python implementation of ``remove_mispairs.pl`` which can also remove
singletons for paired end fastq data file where the reads are not
interleaved.

.. _separate_paired_fastq:

separate_paired_fastq.pl
************************

Takes a fastq file with paired F3 and F5 reads and separate into a file for
each.

Usage::

    separate_paired_fastq.pl <interleaved FASTQ>

.. _trim_fastq:

trim_fastq.pl
*************

Takes a fastq file and keeps the first (5') bases of the sequences specified
by the user.

Usage::

    trim_fastq.pl <single end FASTQ> <desired length>

.. _uncompress_fastqgz:

uncompress_fastqgz.sh
*********************

Create uncompressed copies of fastq.gz file (if input is fastq.gz).

Usage::

    uncompress_fastqgz.sh <fastq>

``<fastq>`` can be either fastq or fastq.gz file.

The original file will not be removed or altered.
