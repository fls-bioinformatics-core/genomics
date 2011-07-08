import sys
import os
import string

# Fetch classes for analysing SOLiD directories
import SolidDataExtractor

class SolidExperiment:
    """Class describing an experiment from a SOLiD run.

    An experiment in this context is a collection of libraries
    which might come from one or more samples, but which will
    be grouped together in a common analysis directory.
    """

    def __init__(self,project=None):
        """Create a new SolidExperiment instance

        Data about the experiment can be accessed via the object's
        properties, specifically:
        
        projects: a list of SolidProject objects
        
        Other data can be accessed via the object's methods.
        """
        self.projects = []
        if project:
            self.addProject(project)
        self.analysis_dir = ""

    def addProject(self,project):
        """Add a project to the experiment.

        project is a populated SolidProject object.
        """
        self.projects.append(project)

    def prefixes(self):
        """Return a list of prefixes from all libraries in the experiment.
        """
        prefixes = []
        for project in self.projects:
            for lib in project.libraries:
                if not lib.prefix in prefixes:
                    prefixes.append(lib.prefix)
        prefixes.sort()
        return prefixes

    def getExperimentName(self):
        """Return the name for the experiment.

        If all libraries in the experiment share a common prefix
        then the experiment name will be '<prefix>_expt'. Otherwise
        the initials of the experimenter are used: <initials>_expt.
        """
        if len(self.prefixes()) > 1:
            # Multiple prefixes, use the experimenter's name
            return self.projects[0].name+'_expt'
        elif len(self.prefixes()) == 1:
            # Single prefix, use that
            return self.prefixes()[0].strip("_")+'_expt'
        else:
            # No prefixes
            return "UNKNOWN_expt"

    def getAnalysisDir(self,suffix=''):
        """Return the name of the analysis directory for the experiment.

        The analysis directory name will be the name of the SOLiD run
        directory with '_analysis' appended. If a suffix is supplied then
        this will also be appended.

        If a suffix is not supplied then the last constructed directory
        name is returned.
        """
        # If an analysis directory was already set and
        # no suffix was specified then return it
        if self.analysis_dir and not suffix:
            return self.analysis_dir
        # Otherwise construct the name from scratch
        if self.projects:
            self.analysis_dir = os.path.join(self.projects[0].\
                                                 getRun().run_dir+'_analysis',
                                             self.getExperimentName())
            if suffix:
                self.analysis_dir += str(suffix)
            return self.analysis_dir
        else:
            return ''

    def getAnalysisFileName(self,filen):
        """Return the 'analysis' file name based on a source file name.

        Source file names are typically of the form:
        solid0127_20110419_FRAG_BC_<sample>_F3_<library>.csfasta

        The analysis file will be the same except:
        1. The <sample> name is removed, and
        2. If the <sample> name includes "_rpt" then append this
           to the filename.
        """
        # Construct new name by removing the sample name
        sample_name = ''
        if self.projects:
            sample_name = self.projects[0].getSample().name
        analysis_filen = replace_string(filen,sample_name)
        # If sample name contains "rpt" then append to the new file name
        if sample_name.find('_rpt') > -1:
            analysis_filen = os.path.split(analysis_filen)[0]+\
                '_rpt'+os.path.split(analysis_filen)[1]
        return analysis_filen

def replace_string(filen,replace_str,with_str='_'):
    try:
        i = filen.rindex(replace_str)
        slen = len(replace_str)
        filen1 = filen[0:i].strip('_')+str(with_str)+filen[i+slen:].strip('_')
    except ValueError:
        filen1 = filen
    return filen1

def report_run(solid_runs):
    """
    """
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

def get_experiments(solid_runs):
    """
    """
    # Organise projects into experiments
    experiments = []
    for run in solid_runs:
        for sample in run.samples:
            for project in sample.projects:
                # Create experiment for this project
                expt = SolidExperiment(project)
                # Have we seen something similar before?
                match_previous_expt = False
                for prev_expt in experiments:
                    if expt.prefixes() == prev_expt.prefixes():
                        # Combine these experiments
                        prev_expt.addProject(project)
                        match_previous_expt = True
                        break
                # No match
                if not match_previous_expt:
                    experiments.append(expt)

    # Set analysis directory names
    analysis_dirs = []
    for expt in experiments:
        # Analysis directory
        index = 1
        dirn = expt.getAnalysisDir()
        while os.path.basename(dirn) in analysis_dirs:
            index += 1
            dirn = expt.getAnalysisDir("_%s" % index)
        analysis_dirs.append(os.path.basename(dirn))

    # Finished
    return experiments

def suggest_analysis_layout(experiments):
    """
    """
    # Suggest an analysis directory and file naming scheme
    for expt in experiments:
        # Analysis directory
        index = 1
        dirn = expt.getAnalysisDir()
        print "\n"+dirn
        # Primary data files
        files = []
        for project in expt.projects:
            for library in project.libraries:
                ln_csfasta = expt.\
                    getAnalysisFileName(os.path.basename(library.csfasta))
                ln_qual = expt.\
                    getAnalysisFileName(os.path.basename(library.qual))
                print "* %s: %s" % (library,ln_csfasta)
                print "* %s: %s" % (library,ln_qual)
                if ln_csfasta in files or ln_qual in files:
                    print "*** WARNING duplicated file name! ***"
                files.append(ln_csfasta)
                files.append(ln_qual)

def pretty_print_libraries(libraries):
    """Given a list of libraries, format for pretty printing.

    Examples:
    ['DR1', 'DR2', 'DR3', DR4'] -> 'DR1-4'
    """
    # Split each library name into prefix and numeric suffix
    ##print "pretty_print: input = "+str(libraries)
    libs = sorted(libraries, key=lambda l: (l.prefix,l.index))
    ##print str(libs)
    # Go through and group
    groups = []
    group = []
    last_index = None
    for lib in libs:
        # Check if this is next in sequence
        try:
            if lib.index == last_index+1:
                # Next in sequence
                group.append(lib)
                last_index = lib.index
                continue
        except TypeError:
            # One or both of the indexes was None
            pass
        # Current lib is not next in previous sequence
        # Tidy up and start new group
        if group:
            groups.append(group)
        group = [lib]
        last_index = lib.index
    # Capture last group
    if group:
        groups.append(group)
    ##print str(groups)
    # Pretty print
    out = []
    for group in groups:
        if len(group) == 1:
            # "group" of one
            out.append(group[0].name)
        else:
            # Group with at least two members
            out.append(group[0].name+"-"+group[-1].index_as_string)
    # Concatenate and return
    return ', '.join(out)

if __name__ == "__main__":
    # Get solid directories
    if len(sys.argv) < 2:
        print "Usage: python %s [OPTIONS] <solid_run_dir>" % sys.argv[0]
        print "Options:"
        print "  --report: print a report of the SOLiD run"
        print "  --layout: suggest layout for analysis directories"
        sys.exit()

    # Solid run directories
    solid_dir_fc1 = sys.argv[-1]
    solid_dir_fc2 = sys.argv[-1]+"_2"
    solid_dirs = (solid_dir_fc1,solid_dir_fc2)

    # Other options
    do_report_run = False
    if "--report" in sys.argv[1:-1]:
        do_report_run = True

    do_suggest_layout = False
    if "--layout" in sys.argv[1:-1]:
        do_suggest_layout = True

    # Get the run information
    solid_runs = []
    for solid_dir in solid_dirs:
        run = SolidDataExtractor.SolidRun(solid_dir)
        if not run:
            print "Error extracting run data for %s" % solid_dir
        else:
            solid_runs.append(run)

    # Report the runs
    if do_report_run:
        report_run(solid_runs)

    # Suggest a layout
    if do_suggest_layout:
        experiments = get_experiments(solid_runs)
        suggest_analysis_layout(experiments)

                            

