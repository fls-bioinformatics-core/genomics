import sys

# Fetch classes for analysing SOLiD directories
import SolidDataExtractor

def pretty_print_libraries(libraries):
    """Given a list of libraries, format for pretty printing.

    Examples:
    ['DR1', 'DR2', 'DR3', DR4'] -> 'DR1-4'
    """
    # Split each library name into prefix and numeric suffix
    ##print "pretty_print: input = "+str(libraries)
    s = []
    for lib in [l.name for l in libraries]:
        prefix = lib
        suffix = ''
        is_suffix = True
        while is_suffix and prefix:
            if prefix[-1].isdigit():
                suffix = prefix[-1]+suffix
                prefix = prefix[0:-1]
            else:
                is_suffix = False
        if suffix == '':
            index = None
        else:
            index = int(suffix.lstrip('0'))
        s.append([lib,prefix,suffix,index])
    # Sort this list on the index (i.e. last element)
    s = sorted(s, key=lambda s: (s[1],s[-1]))
    ##print "pretty_print: analysed & sorted = "+str(s)
    # Go through and group
    groups = []
    group = []
    last_index = None
    for lib in s:
        # Check if this is next in sequence
        this_index = lib[-1]
        try:
            if this_index == last_index+1:
                # Next in sequence
                group.append(lib)
                last_index = this_index
                continue
        except TypeError:
            # One or both of the indexes was None
            pass
        # Current lib is not next in previous sequence
        # Tidy up and start new group
        if group:
            groups.append(group)
        group = [lib]
        last_index = this_index
    # Capture last group
    if group:
        groups.append(group)
    ##print str(groups)
    # Pretty print
    out = []
    for group in groups:
        if len(group) == 1:
            # "group" of one
            out.append(group[0][0])
        else:
            # Group with at least two members
            out.append(group[0][0]+"-"+group[-1][2])
    # Concatenate and return
    return ', '.join(out)

if __name__ == "__main__":
    # Get solid directories
    if len(sys.argv) != 2:
        print "Usage: python %s <solid_run_dir>" % sys.argv[0]
        sys.exit()
    solid_dir_fc1 = sys.argv[1]
    solid_dir_fc2 = sys.argv[1]+"_2"
    solid_dirs = (solid_dir_fc1,solid_dir_fc2)

    # Get the run information
    solid_runs = []
    for solid_dir in solid_dirs:
        run = SolidDataExtractor.SolidRun(solid_dir)
        if not run:
            print "Error extracting run data for %s" % solid_dir
        else:
            solid_runs.append(run)

    # Store the project info for each run
    ##solid_projects = []

    # Report the data for each run
    for run in solid_runs:
        # Report overall slide layout
        slide_layout = ''
        if len(run.samples) == 1:
            slide_layout = "Whole slide"
        elif len(run.samples) == 4:
            slide_layout = "Quads"
        elif len(run.samples) == 8:
            slide_layout = "Octets"
        else:
            slide_layout = "Undefined layout"
        print "\nFC%s (%s)" % (str(run.run_info.flow_cell),
                               str(slide_layout))
        print "Date: %s" % (run.run_info.date)
        print "I.D.: %s" % (run.run_info.name)
        #
        # Report projects for each sample
        for sample in run.samples:
            for project in sample.projects:
                libraries = pretty_print_libraries(project.libraries)
                print "\nSample %s: (project %s): %s" % (sample,
                                                         project.name,
                                                         libraries)
                if run.run_info.is_barcoded_sample:
                    print "B/C samples: %d" % len(project.libraries)
                total_reads = 'not available'
                if sample.barcode_stats:
                    try:
                        total_reads = sample.barcode_stats.\
                            getDataByName("All Beads")[-1]
                    except IndexError:
                        pass
                # FIXME need to check that this total read info is
                # actually correct
                print "Total reads: %s *UNVERIFIED*" % str(total_reads)

