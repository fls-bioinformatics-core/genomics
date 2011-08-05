import sys,os
import SolidDataExtractor

class Experiment:
    def __init__(self):
        self.name = None
        self.type = None
        self.sample = None
        self.library = None

def match(pattern,word):
    """Check if word matches pattern"""
    if not pattern or pattern == '*':
        # No pattern/wildcard, matches everything
        return True
    # Only simple patterns considered now
    if pattern.endswith('*'):
        # Match the start
        return word.startswith(pattern[:-1])
    else:
        # Match the whole word exactly
        return (word == pattern)

def getLinkName(filen,sample_name):
    """Return the 'analysis' file name based on a source file name.
    
    Source file names are typically of the form:
    solid0127_20110419_FRAG_BC_<sample>_F3_<library>.csfasta
    
    The analysis file will be the same except:
    1. The <sample> name is removed, and
    2. If the <sample> name includes "_rpt" then append this
       to the filename.

    Note that the sample name must be explicitly provided
    as a single SolidExperiment may be made up of multiple
    projects with libraries from different projects.
    
    Arguments:
      filen: name of the source file
      sample_name: sample name that the source file comes from

    Returns:
    Name for the analysis file.
    """
    # Construct new name by removing the sample name
    link_filen = replace_string(os.path.basename(filen),sample_name+'_')
    # If sample name contains "rpt" then append to the new file name
    if sample_name.find('_rpt') > -1:
        link_filen = os.path.splitext(link_filen)[0]+\
            '_rpt'+os.path.splitext(link_filen)[1]
    return link_filen

def replace_string(s,replace_substr,with_str=''):
    """Do query/replace on a string

    Arguments:
      s: original string
      replace_substr: substring in s to be replaced
      with_str: (optional) string to substitute replace_substring by

    Returns:
      Modified string
    """
    s1 = s
    slen = len(replace_substr)
    while True:
        try:
            i = s1.rindex(replace_substr)
            s1 = s1[0:i]+str(with_str)+s1[i+slen:]
        except ValueError:
            return s1

def mkdir(dirn):
    """Make a directory"""
    ##print "Making %s" % dirn
    if not os.path.isdir(dirn):
        os.mkdir(dirn)

def mklink(target,link_name):
    """Make a symbolic link"""
    ##print "Linking to %s from %s" % (target,link_name)
    os.symlink(target,link_name)

if __name__ == "__main__":
    print """ build_analysis_dir.py [--dry-run]
                --name=<user> [--type=<expt_type>] --source=<sample>/<library>
                [--source=...]
                [--name=<user> ... ]
                <solid_run_dir>

Build analysis directory structure and populate with links to primary data.

<name> is an identifier (typically the user's initials) e.g. 'PB'
<expt_type> is e.g. 'reseq', 'ChIP-seq', 'RNAseq', 'miRNA'...

The links will be written in a directory '<name>_<expt_type>' e.g.
'PB_ChIP-seq'. (If no <expt_type> is supplied then just the name is used.)

<sample>/<library> specify the names for primary data files e.g.
'PB_JB_pool/PB*'

Both <sample> and <library> can include a trailing wildcard character (i.e. *)
to match multiple names. */* will match all primary data files
"""
    # List of experiment definitions
    expts = []
    # Dry run flag
    dry_run = False
    # Process command line
    solid_run_dir = sys.argv[-1]
    for arg in sys.argv[1:-1]:
        print str(arg)
        if arg.startswith('--name='):
            expts.append(Experiment())
            expt = expts[-1]
            expt.name = arg.split('=')[1]
        elif arg.startswith('--type='):
            try:
                expt = expts[-1]
            except IndexError:
                print "No experiment defined for --type!"
                sys.exit(1)
            if not expt.type:
                expt.type = arg.split('=')[1]
            else:
                print "Type already defined for experiment!"
                sys.exit(1)
        elif arg.startswith('--source='):
            try:
                expt = expts[-1]
            except IndexError:
                print "No experiment defined for --source!"
                sys.exit(1)
            if expt.sample:
                # Duplicate the previous experiment
                expts.append(Experiment())
                expt_copy = expts[-1]
                expt_copy.name = expt.name
                expt_copy.type = expt.type
                expt = expt_copy
            # Extract sample and library
            source = arg.split('=')[1]
            try:
                i = source.index('/')
                expt.sample = source.split('/')[0]
                expt.library = source.split('/')[1]
            except ValueError:
                expt.sample = source
        elif arg == '--dry-run':
            dry_run = True
        else:
            # Unrecognised argument
            print "Unrecognised argument"
            sys.exit(1)
            
    # Report
    print "%d experiments" % len(expts)
    for expt in expts:
        print "Name   : %s" % expt.name
        print "Type   : %s" % expt.type
        print "Sample : %s" % expt.sample
        print "Library: %s" % expt.library

    # # Get the run information
    solid_runs = []
    for solid_dir in (solid_run_dir,solid_run_dir+"_2"):
        run = SolidDataExtractor.SolidRun(solid_dir)
        if not run:
            print "Error extracting run data for %s" % solid_dir
            sys.exit(1)
        else:
            solid_runs.append(run)

    # For each experiment, make a directory
    for expt in expts:
        if expt.type:
            expt_dir = '_'.join((expt.name,expt.type))
        else:
            expt_dir = expt.name
        print "Dir %s" % expt_dir
        if not dry_run:
            mkdir(expt_dir)
        # Locate the primary data
        for run in solid_runs:
            for sample in run.samples:
                if match(expt.sample,sample.name):
                    # Found the sample
                    for library in sample.libraries:
                        if match(expt.library,library.name):
                            # Found a matching library
                            print "Located sample and library: %s" % library.name
                            # Look up primary data
                            print "Primary data:"
                            print "\t%s" % getLinkName(library.csfasta,
                                                       sample.name)
                            print "\t%s" % getLinkName(library.qual,
                                                       sample.name)
                            # Make symbolic links
                            if not dry_run:
                                mklink(library.csfasta,
                                       os.path.join(expt_dir,
                                                    getLinkName(library.csfasta,
                                                                sample.name)))
                                mklink(library.qual,
                                       os.path.join(expt_dir,
                                                    getLinkName(library.qual,
                                                                sample.name)))
        
        
        
