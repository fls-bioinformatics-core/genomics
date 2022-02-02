#!/usr/bin/env python
#
#     fastq_strand.py: determine strandedness of fastq pair using STAR
#     Copyright (C) University of Manchester 2017-2022 Peter Briggs
#

#######################################################################
# Imports
#######################################################################

from builtins import str
from builtins import range
import sys
import os
import io
import argparse
import tempfile
import random
import subprocess
import shutil
import logging
from ..utils import find_program
from ..ngsutils import getreads
from ..ngsutils import getreads_subset
from ..qc.report import strip_ngs_extensions
from .. import get_version

#######################################################################
# Main script
#######################################################################

def fastq_strand(argv,working_dir=None):
    """
    Driver for fastq_strand

    Generate strandedness statistics for single FASTQ or
    FASTQ pair, by running STAR using one or more genome
    indexes
    """
    # Process command line
    p = argparse.ArgumentParser(
        description="Generate strandedness statistics "
        "for FASTQ or FASTQpair, by running STAR using "
        "one or more genome indexes")
    p.add_argument('--version',action='version',
                   version=get_version())
    p.add_argument("r1",metavar="READ1",
                   default=None,
                   help="R1 Fastq file")
    p.add_argument("r2",metavar="READ2",
                   default=None,
                   nargs="?",
                   help="R2 Fastq file")
    p.add_argument("-g","--genome",
                   dest="star_genomedirs",metavar="GENOMEDIR",
                   default=None,
                   action="append",
                   help="path to directory with STAR index "
                   "for genome to use (use as an alternative "
                   "to -c/--conf; can be specified multiple "
                   "times to include additional genomes)")
    p.add_argument("--subset",
                   type=int,
                   default=10000,
                   help="use a random subset of read pairs "
                   "from the input Fastqs; set to zero to "
                   "use all reads (default: 10000)")
    p.add_argument("-o","--outdir",
                   default=None,
                   help="specify directory to write final "
                   "outputs to (default: current directory)")
    p.add_argument("-c","--conf",metavar="FILE",
                   default=None,
                   help="specify delimited 'conf' file with "
                   "list of NAME and STAR index directory "
                   "pairs. NB if a conf file is supplied "
                   "then any indices specifed on the command "
                   "line will be ignored")
    p.add_argument("-n",
                   type=int,
                   default=1,
                   help="number of threads to run STAR with "
                   "(default: 1)")
    p.add_argument("--counts",
                   action="store_true",
                   help="include the count sums for "
                   "unstranded, 1st read strand aligned and "
                   "2nd read strand aligned in the output "
                   "file (default: only include percentages)")
    p.add_argument("--keep-star-output",
                   action="store_true",
                   help="keep the output from STAR (default: "
                   "delete outputs on completion)")
    args = p.parse_args(argv)
    # Print parameters
    print("READ1\t: %s" % args.r1)
    print("READ2\t: %s" % args.r2)
    # Check that STAR is on the path
    star_exe = find_program("STAR")
    if star_exe is None:
        logging.critical("STAR not found")
        return 1
    print("STAR\t: %s" % star_exe)
    # Gather genome indices
    genome_names = {}
    if args.conf is not None:
        print("Conf file\t: %s" % args.conf)
        star_genomedirs = []
        with io.open(args.conf,'rt') as fp:
            for line in fp:
                if line.startswith('#'):
                    continue
                name,star_genomedir = line.rstrip().split('\t')
                star_genomedirs.append(star_genomedir)
                # Store an associated name
                genome_names[star_genomedir] = name
    else:
        star_genomedirs = args.star_genomedirs
    if not star_genomedirs:
        logging.critical("No genome indices specified")
        return 1
    print("Genomes:")
    for genome in star_genomedirs:
        print("- %s" % genome)
    # Output directory
    if args.outdir is None:
        outdir = os.getcwd()
    else:
        outdir = os.path.abspath(args.outdir)
    if not os.path.exists(outdir):
        logging.critical("Output directory doesn't exist: %s" %
                         outdir)
        return 1
    # Output file
    outfile = "%s_fastq_strand.txt" % os.path.join(
        outdir,
        os.path.basename(strip_ngs_extensions(args.r1)))
    if os.path.exists(outfile):
        logging.warning("Removing existing output file '%s'" % outfile)
        os.remove(outfile)
    # Prefix for temporary output
    prefix = "fastq_strand_"
    # Working directory
    if working_dir is None:
        working_dir = os.getcwd()
    else:
        working_dir = os.path.abspath(working_dir)
        if not os.path.isdir(working_dir):
            raise Exception("Bad working directory: %s" % working_dir)
    print("Working directory: %s" % working_dir)
    # Make subset of input read pairs
    nreads = sum(1 for i in getreads(os.path.abspath(args.r1)))
    print("%d reads" % nreads)
    if args.subset == 0:
        print("Using all read pairs in Fastq files")
        subset = nreads
    elif args.subset > nreads:
        print("Actual number of read pairs smaller than requested subset")
        subset = nreads
    else:
        subset = args.subset
        print("Using random subset of %d read pairs" % subset)
    if subset == nreads:
        subset_indices = [i for i in range(nreads)]
    else:
        subset_indices = random.sample(range(nreads),subset)
    fqs_in = filter(lambda fq: fq is not None,(args.r1,args.r2))
    fastqs = []
    for fq in fqs_in:
        fq_subset = os.path.join(working_dir,
                                 os.path.basename(fq))
        if fq_subset.endswith(".gz"):
            fq_subset = '.'.join(fq_subset.split('.')[:-1])
        fq_subset = "%s.subset.fq" % '.'.join(fq_subset.split('.')[:-1])
        with io.open(fq_subset,'wt') as fp:
            for read in getreads_subset(os.path.abspath(fq),
                                        subset_indices):
                fp.write(u'\n'.join(read) + '\n')
        fastqs.append(fq_subset)
    # Make directory to keep output from STAR
    if args.keep_star_output:
        star_output_dir = os.path.join(outdir,
                                       "STAR.%s.outputs" %
                                       os.path.basename(
                                           strip_ngs_extensions(args.r1)))
        print("Output from STAR will be copied to %s" % star_output_dir)
        # Check if directory already exists from earlier run
        if os.path.exists(star_output_dir):
            # Move out of the way
            i = 0
            backup_dir = "%s.bak" % star_output_dir
            while os.path.exists(backup_dir):
                i += 1
                backup_dir = "%s.bak%s" % (star_output_dir,i)
            logging.warning("Moving existing output directory to %s" %
                            backup_dir)
            os.rename(star_output_dir,backup_dir)
        # Make the directory
        os.mkdir(star_output_dir)
    # Write output to a temporary file
    with tempfile.TemporaryFile(mode='w+t') as fp:
        # Iterate over genome indices
        for star_genomedir in star_genomedirs:
            # Basename for output for this genome
            try:
                name = genome_names[star_genomedir]
            except KeyError:
                name = star_genomedir
            # Build a command line to run STAR
            star_cmd = [star_exe]
            star_cmd.extend([
                '--runMode','alignReads',
                '--genomeLoad','NoSharedMemory',
                '--genomeDir',os.path.abspath(star_genomedir)])
            star_cmd.extend(['--readFilesIn',
                             fastqs[0]])
            if len(fastqs) > 1:
                star_cmd.append(fastqs[1])
            star_cmd.extend([
                '--quantMode','GeneCounts',
                '--outSAMtype','BAM','Unsorted',
                '--outSAMstrandField','intronMotif',
                '--outFileNamePrefix',prefix,
                '--runThreadN',str(args.n)])
            print("Running %s" % ' '.join(star_cmd))
            try:
                subprocess.check_output(star_cmd,cwd=working_dir)
            except subprocess.CalledProcessError as ex:
                raise Exception("STAR returned non-zero exit code: %s" %
                                ex.returncode)
            # Save the outputs
            if args.keep_star_output:
                # Make a subdirectory for this genome index
                genome_dir = os.path.join(star_output_dir,
                                          name.replace(os.sep,"_"))
                print("Copying STAR outputs to %s" % genome_dir)
                os.mkdir(genome_dir)
                for f in os.listdir(working_dir):
                    if f.startswith(prefix):
                        shutil.copy(os.path.join(working_dir,f),
                                    os.path.join(genome_dir,f))
            # Process the STAR output
            star_tab_file = os.path.join(working_dir,
                                         "%sReadsPerGene.out.tab" % prefix)
            if not os.path.exists(star_tab_file):
                raise Exception("Failed to find .out file: %s" % star_tab_file)
            sum_col2 = 0
            sum_col3 = 0
            sum_col4 = 0
            with io.open(star_tab_file,'rt') as out:
                for i,line in enumerate(out):
                    if i < 4:
                        # Skip first four lines
                        continue
                    # Process remaining delimited columns
                    cols = line.rstrip('\n').split('\t')
                    sum_col2 += int(cols[1])
                    sum_col3 += int(cols[2])
                    sum_col4 += int(cols[3])
            print("Sums:")
            print("- col2: %d" % sum_col2)
            print("- col3: %d" % sum_col3)
            print("- col4: %d" % sum_col4)
            if sum_col2 > 0.0:
                forward_1st = float(sum_col3)/float(sum_col2)*100.0
                reverse_2nd = float(sum_col4)/float(sum_col2)*100.0
            else:
                logging.warning("Sum of mapped reads is zero!")
                forward_1st = 0.0
                reverse_2nd = 0.0
            print("Strand percentages:")
            print("- 1st forward: %.2f%%" % forward_1st)
            print("- 2nd reverse: %.2f%%" % reverse_2nd)
            # Append to output file
            data = [name,
                    "%.2f" % forward_1st,
                    "%.2f" % reverse_2nd]
            if args.counts:
                data.extend([sum_col2,sum_col3,sum_col4])
            fp.write(u"%s\n" % "\t".join([str(d) for d in data]))
        # Finished iterating over genomes
        # Rewind temporary output file
        fp.seek(0)
        with io.open(outfile,'wt') as out:
            # Header
            out.write(u"#fastq_strand version: %s\t"
                      "#Aligner: %s\t"
                      "#Reads in subset: %s\n" % (get_version(),
                                                  "STAR",
                                                  subset))
            columns = ["Genome","1st forward","2nd reverse"]
            if args.counts:
                columns.extend(["Unstranded",
                                "1st read strand aligned",
                                "2nd read strand aligned"])
            out.write(u"#%s\n" % "\t".join(columns))
            # Copy content from temp to final file
            for line in fp:
                out.write(str(line))
    return 0

def main():
    # Start up
    print("Fastq_strand: version %s" % get_version())
    # Create a temporary working directory
    working_dir = tempfile.mkdtemp(suffix=".fastq_strand",
                                   dir=os.getcwd())
    try:
        retval = fastq_strand(sys.argv[1:],
                              working_dir=working_dir)
    except Exception as ex:
        logging.critical("Exception: %s" % ex)
        retval = 1
    # Clean up the working dir
    print("Cleaning up working directory")
    shutil.rmtree(working_dir)
    print("Fast_strand: finished")
    sys.exit(retval)
