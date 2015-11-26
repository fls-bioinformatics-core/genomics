#!/usr/bin/env python
#
#     merge_regions.py: find and report overlapped peaks in timeseries data
#     Copyright (C) University of Manchester 2014-2015 Peter Briggs, Tom Dzida
#
########################################################################

__version__ = '2.0.0'

"""
merge_regions.py

Program that discovers overlapping regions (aka peaks) for time series
data supplied in a tab delimited file, and reports the sets of overlapped
regions.

Depending on the mode it also reports either a "merged" region (i.e. a
region that is large enough to encompass all the overlapped peaks), or
a "best" region (i.e. the peak in the set which has the highest
normalized tag count).

Usage:

    merge_regions.py [--mode MODE] [OPTIONS] PEAKS_FILE THRESHOLD ATTR

where MODE can be one of 'merge', 'merge_hybrid' or 'best'.

PEAKS_FILE in a tab delimited input file with one region per line,
with the following columns:

CHR START END PEAK_ID STRAND TAG_COUNT ... TIME_POINT

where:

CHR   = chromomsome
START = start position
END   = end position
PEAK_ID = name for each peak
STRAND = strand (+ or -)
TAG_COUNT = normalized tag count

The last column should be the time point index.

Output in 'merge' mode is:

CHR START END N_OVERLAPS FLAG PEAK_LIST

In 'merge_hybrid' it is:

CHR START END SCORE N_OVERLAPS FLAG PEAK_LIST

In 'best' mode it is:

CHR START END N_OVERLAPS FLAG BEST_PEAK PEAK_LIST

FLAG is either 'no_overlap' (the peak didn't overlap any others),
'normal' (overlaps with no more than one peak from each time point),
or 'time_split_full' (overlaps with more than one peak for a single
time point).

"""
import optparse
import numpy as np
import os
import operator
import sys

########################################################################
# Functions
#########################################################################

def get_chromosomes(peaks):
    """
    Return list of chromosome names

    """
    return np.unique(peaks[:,0])

def sort_peak_data(peaks,col_time_point=None):
    """
    Order peaks by chromosome, start, end and time-point

    Returns the supplied list of peaks sorted by
    chromosome, start and end position and time-point
    respectively.

    'peaks' is an ndarray holding information on a set of
    peaks. The columns are:

    0: chromosome
    1: start position
    2: end position

    There can be other columns present. The function
    assumes that the time-point data is in the last column
    of the array unless an index is explicitly supplied via
    the 'col_time_point' argument.
    
    """
    # Set time point column
    if col_time_point is None:
        # Assume last column
        col_time_point = peaks.shape[1]-1

    # Convert chromosome strings to integer indices
    chrcolumndict={}
    for index, i in enumerate(get_chromosomes(peaks)): 
        chrcolumndict[i] = index + 1

    # Create subarray for sorting
    subarray = peaks[:,[0,1,2,col_time_point]]

    # Map string chromosome names into arbitrary integer indices
    subarray[:,0] = map(lambda x: chrcolumndict[x], subarray[:,0])

    # Convert array elements to int
    subarray = np.array(subarray, int)

    # Do the sort so that columns are sorted chr, start, end, and time
    # respectively
    return peaks[np.lexsort((subarray[:,3],
                             subarray[:,2],
                             subarray[:,1],
                             subarray[:,0]))]

def find_overlapping_peaks(start_peak,peaks,threshold,percent=False):
    """
    Find peaks that overlap in a list

    Given a 'seed' peak and an list of peaks, returns tuple with the
    list of peaks that overlap each other and those which don't.

    The input list of peaks should have been sorted into ascending
    order of start position.

    Peaks are rejected if the overlap region is too small, as defined
    by the 'threshold'. If percent is True then the overlap must be
    greater than this percentage of the peak width to be counted; if
    percentage is False then the threshold is the absolute number of
    bases.

    """
    # ** Note on peak widths **
    # There is a slight inconsistency in this function about whether or
    # not the last base in a region is included when calculating widths
    # The width of an overlap *does* include the last base; the width of
    # peaks does not.
    # For edge cases this may make a difference
    start = int(start_peak[1])
    end = int(start_peak[2])
    width = end - start
    overlapping = [start_peak]
    discarded = []
    for i,peak in enumerate(peaks):
        peak_start = int(peak[1])
        # Assume that peaks are ordered by start position
        # so we only need to check whether the start position
        # is within the region of interest
        if peak_start <= end:
            peak_end = int(peak[2])
            # Determine overlap width
            overlap_width = end - peak_start + 1
            # Check if it meets the threshold criteria
            if percent:
                is_overlap = float(overlap_width)/float(max(width,peak_end-peak_start)) \
                             >= threshold
            else:
                is_overlap = overlap_width >= threshold
            if is_overlap:
                overlapping.append(peak)
                # Update the upper limit of the region
                if peak_end > end:
                    end = peak_end
                    # Update the width to be the last peak
                    width = peak_end - peak_start
            else:
                # Not an overlapping peak
                discarded.append(peak)
        else:
            # Encountered a peak that is out-of-range
            # All subsequent peaks must also be out-of-range
            discarded = discarded + [peaks[j] for j in xrange(i,len(peaks))]
            # Jump out of the loop and return
            break
    # No more overlaps detected
    return (overlapping,discarded)

def merge_regions(mode,peaks_file,out_file,threshold=0,percent=True,
                  col_time_point=None):
    """
    Merge regions read from input file and write to output.

    Reads region data from a tab-delimited 'peaks_file', which
    should have the following columns:

    CHR START END PEAK_ID STRAND SCORE ... TIME_POINT

    Regions are merged or selected depending on the 'mode' and
    the results are written to 'out_file'.

    Overlaps must pass a threshold test: the size of the overlap
    area must be greater than 'threshold' bases (if 'percent' is
    False) or greater than 'threshold' % of the previous peak
    (if 'percent' is True).

    If the time-point column is not the last column in the input
    file then 'col_time_point' should be set to the index of the
    actual column position (counting from zero). 

    'mode' can be one of 'merge', 'merge_hybrid' or 'best'.

    For 'merge': overlapping regions are merged together into a
    single region which covers all regions in the overlap.
    In this mode the output fields are:

    CHR START END N_OVERLAPS FLAG PEAK_LIST

    For 'best': only the region with the highest score of all
    those in the overlapping set is kept.
    In this mode the output fields are:

    CHR START END N_OVERLAPS FLAG BEST_PEAK PEAK_LIST

    For 'merge_hybrid': same as 'merge', but the highest score
    from the overlapping set is also output.
    In this mode the output fields are:
    
    CHR START END SCORE N_OVERLAPS FLAG PEAK_LIST
    
    N_OVERLAPS is the number of overlapping peaks (zero if there
    were no overlaps).

    FLAG can be 'no_overlap' (region didn't overlap any others),
    'normal' (overlaps with no more than one peak per time point)
    or 'time_split_full' (overlaps with more than one peak for
    a single time point).

    PEAK_LIST is a comma-delimited list of region ids.

    """

    # Load the peak data from the input file
    print "Loading data from %s" % peaks_file
    all_peaks = np.loadtxt(peaks_file, dtype = str)
    print "Read %d lines of data" % all_peaks.shape[0]

    # Determine the position of the last column (=time point)
    if col_time_point is None:
        col_time_point = all_peaks.shape[1]-1

    # Open output file
    print "Output will be written to %s" % out_file
    fp_out = open(out_file,"w")
    
    # Sort the data before using it
    all_peaks = sort_peak_data(all_peaks,col_time_point)

    # Loop over peaks in each chromosome and find overlapping subsets
    for chrom in get_chromosomes(all_peaks):
        # Get subset for this chromosome
        peaks = map(list,all_peaks[all_peaks[:,0]==chrom])
        while peaks:
            peak = peaks[0]
            overlaps,peaks = find_overlapping_peaks(peak,peaks[1:],
                                                    threshold=threshold,
                                                    percent=percent)
            n_overlaps = len(overlaps)
            if n_overlaps == 1:
                # Only one peak so actually no overlaps
                n_overlaps = 0
                flag = 'no_overlap'
            else:
                # Multiple peaks
                flag = 'normal'
                # Determine if any time point occurs more than once
                # and update flag if necessary
                time_points = []
                for peak in overlaps:
                    if peak[col_time_point] in time_points:
                        flag = 'time_split_full'
                        break
                    time_points.append(peak[col_time_point])
            overlap_list = ','.join([x[3] for x in overlaps])
            if mode == 'merge':
                # Merge peaks i.e. report region that encloses all merged peaks
                start = overlaps[0][1]
                end = overlaps[-1][2]
                # Output
                fp_out.write("%s\n" % '\t'.join([str(x) for x in [chrom,start,end,
                                                                  n_overlaps,
                                                                  flag,
                                                                  overlap_list,
                                                                  []]]))
            elif mode == 'merge_hybrid':
                # Merge peaks but take the highest score from
                # the merged peaks
                start = overlaps[0][1]
                end = overlaps[-1][2]
                # Score is assumed to be in column 6
                score = max([x[5] for x in overlaps])
                # Output
                fp_out.write("%s\n" % '\t'.join([str(x) for x in [chrom,start,end,
                                                                  score,
                                                                  n_overlaps,
                                                                  flag,
                                                                  overlap_list,
                                                                  []]]))
            elif mode == 'best':
                # Pick the 'best' peak i.e. highest score
                # Score is assumed to be in column 6
                best = overlaps[0]
                for peak in overlaps[1:]:
                    if peak[5] > best[5]:
                        best = peak
                # Output
                fp_out.write("%s\n" % '\t'.join([str(x) for x in [best[0],
                                                                  best[1],
                                                                  best[2],
                                                                  n_overlaps,
                                                                  flag,
                                                                  best[3],
                                                                  overlap_list,
                                                                  []]]))
            else:
                raise Exception("Unrecognised mode: '%s'" % mode)

    # Close the output file
    fp_out.close()

########################################################################
# Main program
#########################################################################

if __name__ == '__main__':

    # Process command line
    p = optparse.OptionParser(usage="%prog PEAKS_FILE THRESHOLD ATTR",
                              version="%prog "+__version__,
                              description="Determine overlapping regions from PEAKS_FILE. "
                              "THRESHOLD_ATTR can be either 'percent' or 'base'.")
    p.add_option('--mode',type='choice',action='store',dest='mode',
                 choices=['merge','merge_hybrid','best'],default='merge',
                 help="set mode, must be one of: 'merge' (default: output merged region "
                 "for each overlapping set i.e. covers all regions in the set); "
                 "'merge_hybrid' (output merged region with additional column giving "
                 "the highest score from the merged regions); 'best' (output region with "
                 "highest score/tag count)")
    p.add_option('-o',action='store',dest='out_file',default=None,
                 help="specify name for output file")
    options,args = p.parse_args()

    # Assign arguments
    if len(args) != 3:
        p.error("incorrect arguments")
    peaks_file, threshold, thresh_atrib = args

    # Threshold
    if thresh_atrib == 'percent':
        percent = True
    elif thresh_atrib == 'base' :
        percent = False
    else:
        p.error('bad value for THRESHOLD ATTR (must be either ''percent'' or ''base''')
    threshold = float(threshold)

    # Mode
    mode = options.mode
    if mode == 'merge':
        print "Operating in MERGE mode"
    if mode == 'merge_hybrid':
        print "Operating in MERGE_HYBRID mode"
    elif mode == 'best':
        print "Operating in BEST mode"
    else:
        p.error("Unrecognised mode: %s" % mode)

    # Output file
    if options.out_file is None:
        out_file = os.path.splitext(os.path.basename(peaks_file))[0]+'_%s.txt' % mode
    else:
        out_file = options.out_file

    # Perform the merging operations
    merge_regions(mode,peaks_file,out_file,threshold,percent,
                  col_time_point=None)
