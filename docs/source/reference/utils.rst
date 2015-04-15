General non-bioinformatic utilities
===================================

General utility scripts/tools.

* :ref:`cd_set_umask`: setup script to automagically set umask for specific
  directory
* :ref:`cmpdirs`: compare contents of two directories
* :ref:`cluster_load`: report Grid Engine usage via qstat wrapper
* :ref:`do_sh`: execute shell command iteratively with range of integer index
  values
* :ref:`makeBinsFromBed`: create bin files for binning applications
* :ref:`makeRegularBinsFromGenomeTable`: make bin file from set of chromosomes
* :ref:`make_mock_solid_dir`: create mock SOLiD directory structure for
  testing
* :ref:`manage_seqs`: handling sets of named sequences (e.g. FastQC
  contaminants file)
* :ref:`md5checker`: check files and directories using MD5 sums
* :ref:`symlink_checker`: check and update symbolic links

.. _cd_set_umask:

cd_set_umask.sh
***************

Script to set and revert a user's ``umask`` appropriately when moving
in and out of a particular directory (or one of its subdirectories).

.. _do_sh:

do.sh
*****

Execute a command multiple times, substituting a range of integer index
values for each execution. For example::

    do.sh 1 43 ln -s /blah/blah#/myfile#.ext ./myfile#.ext

will execute::

    ln -s /blah/blah1/myfile1.ext ./myfile1.ext
    ln -s /blah/blah2/myfile2.ext ./myfile2.ext
    ...
    ln -s /blah/blah43/myfile43.ext ./myfile43.ext

.. _cmpdirs:

cmpdirs.py
**********

Recursively compare contents of one directory against another.

Usage::

    cmpdirs.py [OPTIONS] DIR1 DIR2

Compare contents of ``DIR1`` against corresponding files and
directories in `DIR2`.

Files are compared using MD5 sums, symlinks using their targets.

Options:

.. cmdoption:: -n N_PROCESSORS

    specify number of cores to use

.. _cluster_load:

cluster_load.py
***************

Report current Grid Engine utilisation by wrapping the ``qstat``
utility.

Usage::

    cluster_load.py

Outputs a report of the form::

    6 jobs running (r)
    44 jobs queued (q)
    0 jobs suspended (S)
    0 jobs pending deletion (d)
    
    Jobs by queue:
        queue1.q    1 (0/0)
        queue2.q    5 (0/0)
	...

    Jobs by user:
                 	Total   r	q	S	d
            user1       2	1	1	0	0
            user2       15      1	14      0	0
            user3       32	4	28	0	0
            ...

    Jobs by node:
                 	Total   queue1.q        queue2.q
                             r (S/d)         r (S/d)
          node01    1        0 (0/0)         1 (0/0)
          node02    1        0 (0/0)         1 (0/0)
          ...

.. _makeBinsFromBed:

makeBinsFromBed.pl
******************

Utility to systematically and easily create feature ``bin`` files,
to be used in binning applications.

Example use cases include defining a region 500bp in front of the
TSS, and making a set of equally spaced intervals between the start
and end of a gene or feature.

Usage::

    makeBinsFromBed.pl [options] BED_FILE OUTPUT_FILE

Options:

.. cmdoption:: --marker [ midpoint | start | end | tss | tts ]

    On which component of feature to position the bin(s) (default midpoint).
 
    tss: transcription start site (using strand)
 
    tts: transcription termination site (using strand)	

.. cmdoption:: --binType [ centred | upstream | downstream ]

    How to position the bin relative to the feature (default centred).

    If marker is start/end, position is relative to chromosome. 

    If marker is tss/tts, position is relative to strand of feature	
        
.. cmdoption:: --offset n

    All bins are shifted by this many bases (default 0).

    If marker is start/end, n is relative to chromosome.

    If marker is tss/tts, n is relative to strand of feature

.. cmdoption:: --binSize n

    The size of the bins (default 200)
	
.. cmdoption:: --makeIntervalBins n

    ``n`` bins are made of equal size within the feature. 

    The bins begin, and are numbered from, the marker.

    If > 0, ignores binSize, offset and binType.

    Incompatible with ``--marker midpoint``

*Tips:*

* To create single bp of the tss, use::

     --marker tss  --binSize 1 --binType downstream
        
* To get a bin of 1000bp ending 500bp upstream of the tss, use::

     --marker tss  --binSize 1000 --binType upstream --offset -500
        
.. _makeRegularBinsFromGenomeTable:

makeRegularBinsFromGenomeTable.R
********************************

Make a bed file with bins of size ``[binSize]`` filling every chrom
specified in ``[Genome Table File]``

Usage::

    makeRegularBinsFromGenomeTable.R [Genome Table File] [binSize]

Arguments:

* ``Genome Table File``: name of a two-column tab-delimited file
  with chromosome name-start position information for each
  chromosome (i.e. the first two columns of the chromInfo table
  from UCSC).

* ``binSize``: integer size of each bin (in bp) in the output file

Outputs:

* ``Bed file``: same name as the genome table file with the
  extension ``<binSize>.bp.bin.bed``, with each chromosome divided
  into bins of the requested size.

.. _make_mock_solid_dir:

make_mock_solid_dir.py
**********************

Make a temporary mock SOLiD directory structure that can be used
for testing.

Usage::

    make_mock_solid_dir.py [OPTIONS]

Arguments:

.. cmdoption:: --paired-end

    Create directory structure for paired-end run

.. _manage_seqs:

manage_seqs.py
**************

Read sequences and names from one or more INFILEs (which can be a
mixture of FastQC 'contaminants' format and or Fasta format), check
for redundancy (i.e. sequences with multiple associated names) and
contradictions (i.e. names with multiple associated sequences).

Usage::

    manage_seqs.py OPTIONS FILE [FILE...]

Options:

.. cmdoption:: -o OUT_FILE

    write all sequences to ``OUT_FILE`` in FastQC 'contaminants'
    format

.. cmdoption:: -a APPEND_FILE

    append sequences to existing ``APPEND_FILE`` (not compatible
    with ``-o``)

.. cmdoption:: -d DESCRIPTION

    supply arbitrary text to write to the header of the output
    file

Intended to help create/update files with lists of "contaminant"
sequences to input into the ``FastQC`` program (using
``FastQC``'s ``--contaminants`` option).

To create a contaminants file using sequences from a FASTA file
do e.g.::

    manage_seqs.py -o custom_contaminants.txt sequences.fa

To append sequences to an existing contaminants file do e.g.::

    manage_seqs.py -a my_contaminantes.txt additional_seqs.fa

.. _md5checker:

md5checker.py
*************

Utility for checking files and directories using MD5 checksums.

Usage:

To generate MD5 sums for a directory::

    md5checker.py [ -o CHKSUM_FILE ] DIR

To generate the MD5 sum for a file::

    md5checker.py [ -o CHKSUM_FILE ] FILE

To check a set of files against MD5 sums stored in a file::

    md5checker.py -c CHKSUM_FILE

To compare the contents of source directory recursively against
the contents of a destination directory, checking that files in
the source are present in the target and have the same MD5
sums::

    md5checker.py --diff SOURCE_DIR DEST_DIR

To compare two files by their MD5 sums::

    md5checker.py --diff FILE1 FILE2

.. _symlink_checker:

symlink_checker.py
******************

Check and update symbolic links.

Usage::

    symlink_checker.py OPTIONS DIR

Recursively check and optionally update symlinks found under
directory DIR

Options:

.. cmdoption:: --broken

    report broken symlinks

.. cmdoption:: --find=REGEX_PATTERN

    report links where the destination matches the
    supplied ``REGEX_PATTERN``

.. cmdoption:: --replace=NEW_STRING

    update links found by ``--find`` option, by
    substituting ``REGEX_PATTERN`` with ``NEW_STRING``
