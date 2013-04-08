#!/bin/env python
#
import os
import sys
import optparse
import IlluminaData
import FASTQFile
#
class BarcodeMatcher:

    def __init__(self,barcode):
        self.__barcode = barcode

    @property
    def barcode(self):
        return self.__barcode

    def match(self,test_barcode,max_mismatches=0):
        if test_barcode.startswith(self.__barcode):
            return True
        nmismatches = 0
        try:
            for i in range(len(self.__barcode)):
                if test_barcode[i] != self.__barcode[i]:
                    nmismatches += 1
                    if nmismatches > max_mismatches:
                        return False
        except IndexError:
            return False
        return True
#
def rebin_fastq_file(fastq_file,barcodes,nmismatches):
    # Start
    print "Processing %s" % fastq_file
    info = IlluminaData.IlluminaFastq(fastq_file)
    # Set up output files
    output_files = {}
    # Weed out barcodes that aren't associated with this lane
    local_barcodes = []
    for barcode in barcodes:
        if barcode['lane'] != info.lane_number:
            continue
        local_barcodes.append(barcode)
        output_file_name = "%s_%s_L%03d_R%d_%03d.fastq" % (barcode['name'],
                                                           barcode['index'],
                                                           info.lane_number,
                                                           info.read_number,
                                                           info.set_number)
        print "\t%s\t%s" % (barcode['index'],output_file_name)
        if os.path.exists(output_file_name):
            print "\t%s: already exists,exiting" % output_file_name
            sys.exit(1)
        output_files[barcode['index']] = open(output_file_name,'w')
    # Check if there's anything to do
    if len(local_barcodes) == 0:
        return
    # Also make a file for unbinned reads
    unbinned_file_name = "unbinned_L%03d_R%d_%03d.fastq" % (info.lane_number,
                                                            info.read_number,
                                                            info.set_number)
    if os.path.exists(unbinned_file_name):
        print "\t%s: already exists,exiting" % unbinned_file_name
        sys.exit(1)
    output_files['unbinned'] = open(unbinned_file_name,'w')
    # Process reads
    nreads = 0
    for read in FASTQFile.FastqIterator(fastq_file):
        nreads += 1
        matched_read = False
        this_barcode = read.seqid.index_sequence
        for barcode in local_barcodes:
            if barcode['matcher'].match(this_barcode,nmismatches):
                ##print "Matched %s against %s" % (this_barcode,barcodes[barcode]['name'])
                output_files[barcode['index']].write(str(read)+'\n')
                matched_read = True
                break
        # Put in unbinned if no match
        if not matched_read:
            output_files['unbinned'].write(str(read)+'\n')
        ##if nreads > 100: break
    # Close files
    for barcode in local_barcodes:
        output_files[barcode['index']].close()
    print "\tMatched %d reads for %s" % (nreads,os.path.basename(fastq_file))
#
if __name__ == "__main__":
    # Create command line parser
    p = optparse.OptionParser(usage="%prog OPTIONS undetermined_data_dir",
                              description="Reassign reads with undetermined index sequences "
                              "(i.e. barcodes).")
    p.add_option("--barcode",action="append",dest="barcode_info",default=[],
                 help="specify barcode sequence and corresponding sample name as BARCODE_INFO. "
                 "The syntax is '<name>:<barcode>:<lane>' e.g. --barcode=PB1:ATTAGA:3")
    p.add_option("--samplesheet",action="store",dest="sample_sheet",default=None,
                 help="specify SampleSheet.csv file to read barcodes, sample names and lane "
                 "assignments from (as an alternative to --barcode).")
    # Parse command line
    options,args = p.parse_args()
    # Get data directory name
    if len(args) != 1:
        p.error("expected one argument (location of undetermined index reads)")
    undetermined_dir = os.path.abspath(args[0])
    # Set up barcode data
    barcodes = []
    for barcode_info in options.barcode_info:
        name,barcode,lane = barcode_info.split(':')
        print "Assigning barcode '%s' in lane %s to %s" % (barcode,lane,name)
        barcodes.append({ 'name': name,
                          'index': barcode,
                          'matcher': BarcodeMatcher(barcode),
                          'lane': int(lane)})
    # Read from sample sheet (if supplied)
    if options.sample_sheet is not None:
        print "Reading data from sample sheet %s" % options.sample_sheet
        sample_sheet = IlluminaData.CasavaSampleSheet(options.sample_sheet)
        for line in sample_sheet:
            name = line['SampleID']
            barcode = line['Index'].rstrip('N').rstrip('-').rstrip('N')
            lane = line['Lane']
            print "Assigning barcode '%s' in lane %s to %s" % (barcode,lane,name)
            barcodes.append({ 'name': name,
                              'index': barcode,
                              'matcher': BarcodeMatcher(barcode),
                              'lane': int(lane) })
    if len(barcodes) < 1:
        p.error("need at least one --barcode and/or --samplesheet assignment")
    # Keep track of output files
    output_files = {}
    # Collect input files
    p = IlluminaData.IlluminaProject(undetermined_dir)
    # Loop over "samples" and match barcodes
    for s in p.samples:
        for fq in s.fastq:
            fastq = os.path.join(s.dirn,fq)
            rebin_fastq_file(fastq,barcodes,1)
            ##print "Processing %s" % fastq
            ##nreads = 0
            ##for read in FASTQFile.FastqIterator(fastq):
            ##    this_barcode = read.seqid.index_sequence
            ##    for barcode in barcodes:
            ##        if barcodes[barcode]['matcher'].match(this_barcode,1):
            ##            print "Matched %s against %s" % (this_barcode,barcodes[barcode]['name'])
            ##    nreads += 1
            ##    if nreads > 1000: break
    print "Finished"

