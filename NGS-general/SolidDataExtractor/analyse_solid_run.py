import sys
import os
import string

# Fetch classes for analysing SOLiD directories
import SolidDataExtractor
        
def extract_prefix(library):
    """Given a library name, extract the prefix.

    The prefix is the library name with any trailing numbers
    removed."""
    return str(library).rstrip(string.digits)

def replace_string(filen,replace_str,with_str='_'):
    try:
        i = filen.index(replace_str)
        slen = len(replace_str)
        filen1 = filen[0:i].strip('_')+str(with_str)+filen[i+slen:].strip('_')
    except ValueError:
        filen1 = filen
    return filen1

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
    #
    # Suggest an analysis directory scheme
    print "Constructing suggested analysis directory scheme..."
    #
    experiments = []
    for run in solid_runs:
        for sample in run.samples:
            for project in sample.projects:
                # Get project prefixes
                prefixes = []
                for library in project.libraries:
                    prefix = extract_prefix(library)
                    if not prefix in prefixes:
                        prefixes.append(prefix)
                prefixes.sort()
                # Data structure for experiment
                expt = {'prefixes': prefixes,
                        'projects': [{ 'project': project,
                                       'sample': sample,
                                       'run': run }]}
                # Have we seen something similar before?
                match_previous_expt = False
                for i in range(0,len(experiments)):
                    prev_expt = experiments[i]
                    # Look for matching prefix list
                    if prefixes == prev_expt['prefixes']:
                        # Combine these experiments
                        projects = prev_expt['projects']
                        projects.append(expt['projects'][0])
                        experiments[i] = { 'prefixes': prefixes,
                                           'projects': projects }
                        match_previous_expt = True
                        break
                # No match
                if not match_previous_expt:
                    experiments.append(expt)
    # Report
    for expt in experiments:
        print str(expt)
    #
    # Now unpack the analysis scheme
    names = []
    for expt in experiments:
        # Directory and name
        if len(expt['prefixes']) > 1:
            # Multiple prefixes, use the experimenter's name
            name = expt['projects'][0]['project'].name+'_expt'
        else:
            # Single prefix, use that
            name = expt['prefixes'][0].strip("_")+'_expt'
        # Check this name not already used
        if name in names:
            name += "_2"
        names.append(name)
        dirn = os.path.join(expt['projects'][0]['run'].run_dir+'_analysis',
                            name)
        print "\n"+dirn
        # Data
        files = []
        for sub_expt in expt['projects']:
            for library in sub_expt['project'].libraries:
                # Construct new name by removing the sample name
                csfasta = os.path.basename(library.csfasta)
                qual = os.path.basename(library.qual)
                sample_name = sub_expt['sample'].name
                ln_csfasta = replace_string(csfasta,sample_name)
                ln_qual = replace_string(qual,sample_name)
                # If sample name contains "rpt" then transfer
                # this to the new file name
                if sample_name.find('_rpt') > -1:
                    ln_csfasta = replace_string(ln_csfasta,library.name,
                                                '_'+library.name+'_rpt')
                    ln_qual = replace_string(ln_qual,library.name,
                                             '_'+library.name+'_rpt')
                print "* %s: %s" % (library,ln_csfasta)
                print "* %s: %s" % (library,ln_qual)
                if ln_csfasta in files or ln_qual in files:
                    print "*** WARNING duplicated file name! ***"
                files.append(ln_csfasta)
                files.append(ln_qual)
                            

