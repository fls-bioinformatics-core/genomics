#!/bin/env python
#
#     qc_report.py: generate report file for NGS qc runs
#     Copyright (C) University of Manchester 2012 Peter Briggs
#
########################################################################
#
# qc_report.py
#
#########################################################################

"""qc_report

Generate a HTML report for an NGS QC pipeline run.
"""

#######################################################################
# Import modules that this module depends on
#######################################################################
#
import sys
import os
import optparse
import logging
import base64
import zipfile

# Put ../share onto Python search path for modules
SHARE_DIR = os.path.abspath(
    os.path.normpath(
        os.path.join(os.path.dirname(sys.argv[0]),'..','share')))
sys.path.append(SHARE_DIR)
try:
    import Pipeline
except ImportError, ex:
    print "Error importing modules: %s" % ex
    print "Check PYTHONPATH"
    sys.exit(1)

#######################################################################
# Class definitions
#######################################################################

class SolidQCReport:
    """Class for reporting QC run on SOLiD data

    SolidQCReport assembles the data associated with a QC run for a set
    of SOLiD data and generates a HTML document which summarises the
    results for quick review.
    """

    def __init__(self,dirn):
        """Make a new SolidQCReport instance

        The SolidQCReport class checks the contents of the supplied
        directory looking for SOLiD data sets corresponding to samples,
        and collects the associated QC outputs (boxplots, screens and
        filtering statistics).

        Arguments:
          dirn: top-level directory holding the QC run outputs
        """
        self.__dirn = os.path.abspath(dirn)
        self.__qc_dir = os.path.join(self.__dirn,'qc')
        self.__samples = []
        self.__paired_end = False
        # Locate stats file and determine if we have paired end data
        stats_file = os.path.join(self.__dirn,"SOLiD_preprocess_filter.stats")
        if not os.path.exists(stats_file):
            stats_file = os.path.join(self.__dirn,"SOLiD_preprocess_filter_paired.stats")
            if os.path.exists(stats_file):
                self.__paired_end = True
            else:
                stats_file = None
                logging.error("Can't find stats file in %s" % self.__dirn)
        # Get primary data files
        if not self.__paired_end:
            primary_data = Pipeline.GetSolidDataFiles(self.__dirn)
        else:
            primary_data = Pipeline.GetSolidPairedEndFiles(self.__dirn)
        for data in primary_data:
            sample = os.path.splitext(data[0])[0]
            if self.__paired_end:
                # Strip trailing "_F3" from names
                sample = sample.replace('_F3','')
            self.__samples.append(SolidQCSample(sample,data[0],data[1]))
            print "Sample: '%s'" % sample
        self.__samples.sort()
        # Get QC files
        if not os.path.isdir(self.__qc_dir):
            print "%s not found" % self.__qc_dir
            return
        qc_files = os.listdir(self.__qc_dir)
        # Associate QC outputs with sample names
        for sample in self.__samples:
            for f in qc_files:
                # Boxplots
                sample_name_underscore = sample.name+'_'
                sample_name_dot = sample.name+'.'
                if f.startswith(sample_name_dot) or f.startswith(sample_name_underscore) or \
                        f.startswith(sample.qual):
                    if f.endswith('_boxplot.png'): sample.addBoxplot(f)
                # Screens
                if f.startswith(sample_name_underscore):
                    if f.endswith('_screen.png'): sample.addScreen(f)
        # Filtering stats
        if os.path.exists(stats_file):
            fp = open(stats_file,'rU')
            for line in fp:
                if line.startswith('#'): continue
                fields = line.rstrip().split('\t')
                sample_name = fields[0]
                if self.__paired_end: sample_name = sample_name.replace('_paired','')
                for sample in self.__samples:
                    if sample_name == sample.name:
                        sample.addFilterStat('reads',fields[1])
                        sample.addFilterStat('reads_post_filter',fields[2])
                        sample.addFilterStat('diff_reads',fields[3])
                        sample.addFilterStat('percent_filtered',fields[4])
                        if self.__paired_end:
                            sample.addFilterStat('reads_post_filter2',fields[5])
                            sample.addFilterStat('diff_reads2',fields[6])
                            sample.addFilterStat('percent_filtered2',fields[7])
                        break
            fp.close()
        else:
            logging.error("Can't find stats file %s" % stats_file)

    def write(self):
        """Write a summary of the QC report

        Deprecated: writes a summary of the QC run to stdout.
        """
        for sample in self.__samples:
            print "Sample: %s" % sample
            # Boxplots
            boxplots = sample.boxplots()
            if boxplots:
                print "\tBoxplots:"
                for b in boxplots:
                    print "\t\t%s" % b
            else:
                print "\tNo boxplots found"
            # Screens
            screens = sample.screens()
            if screens:
                print "\tScreens:"
                for s in screens:
                    print "\t\t%s" % s
            else:
                print "\tNo screens found"

    def html(self,inline_pngs=False):
        """Write the HTML report

        Writes a HTML document 'qc_report.html' to the top-level
        analysis directory.

        Arguments:
          inline_pngs: if set True then PNG image data will be inlined
            (report file will be more portable)
        """
        html = HTMLPageWriter("QC for %s" % os.path.basename(self.__dirn))
        # Title
        html.add("<h1>QC for %s</h1>" % os.path.basename(self.__dirn))
        # Add styles
        html.addCSSRule("h1 { background-color: #42AEC2;\n"
                        "     color: white; }")
        html.addCSSRule("h2 { background-color: #8CC63F;\n"
                        "     color: white;\n"
                        "     display: inline-block;\n"
                        "     padding: 5px 5px;\n"
                        "     margin: 0;\n"
                        "     border-top-left-radius: 20; }")
        html.addCSSRule(".sample { margin: 10 10;\n"
                        "          border: solid 2px #8CC63F;\n"
                        "          padding: 0;\n"
                        "          background-color: #ffe;\n"
                        "          border-top-left-radius: 25; }")
        html.addCSSRule("table.summary { border: solid 1px grey;\n"
                        "                font-size: 90% }")
        html.addCSSRule("table.summary th { background-color: grey;\n"
                        "                   color: white; }")
        html.addCSSRule("table.summary td { text-align: right; \n"
                        "                   padding: 2px 5px;\n"
                        "                   border-bottom: solid 1px lightgray; }")
        html.addCSSRule("td { vertical-align: top; }")
        html.addCSSRule("img { background-color: white; }")
        # Index
        html.add("<p>Samples in %s</p>" % self.__dirn)
        html.add("<table class='summary'>")
        if not self.__paired_end:
            html.add("<tr><th>Sample</th><th>Reads</th><th>Reads (filtered)</th>"
                     "<th># filtered</th><th>% filtered</th></tr>")
        else:
            html.add("<tr><th>Sample</th><th>Reads</th><th>Reads (filtered, lenient)</th>"
                     "<th># filtered (lenient)</th><th>% filtered (lenient)</th>"
                     "<th>Reads (filtered, strict)</th>"
                     "<th># filtered (strict)</th><th>% filtered (strict)</th></tr>")
        for sample in self.__samples:
            html.add("<tr>")
            html.add("<td><a href='#%s'>%s</a></td>" % (sample.name,sample.name))
            html.add("<td>%s</td>" % sample.filterStat('reads'))
            html.add("<td>%s</td>" % sample.filterStat('reads_post_filter'))
            html.add("<td>%s</td>" % sample.filterStat('diff_reads'))
            html.add("<td>%s</td>" % sample.filterStat('percent_filtered'))
            if self.__paired_end:
                html.add("<td>%s</td>" % sample.filterStat('reads_post_filter2'))
                html.add("<td>%s</td>" % sample.filterStat('diff_reads2'))
                html.add("<td>%s</td>" % sample.filterStat('percent_filtered2'))
            html.add("</tr>")
        html.add("</table>")
        # QC plots etc
        for sample in self.__samples:
            html.add("<div class='sample'>")
            html.add("<a name='%s'><h2>%s</h2></a>" % (sample.name,sample.name))
            html.add("<table><tr>")
            # Boxplots
            html.add("<td>")
            if sample.boxplots():
                html.add("<h3>Boxplots</h3>")
                for b in sample.boxplots():
                    if not inline_pngs:
                        html_content="<a href='qc/%s'><img src='%s' height=250 /></a>" % (b,b)
                    else:
                        pngdata = PNGBase64Encoder().encodePNG(os.path.join(self.__qc_dir,b))
                        html_content="<a href='qc/%s''><img src='data:image/png;base64,%s' height=250 /></a>" % (b,pngdata)
                    html.add(html_content)
            else:
                html.add("No boxplots found")
            html.add("</td>")
            # Screens
            html.add("<td>")
            if sample.screens():
                html.add("<h3>Screens</h3>")
                for s in sample.screens():
                    # Images
                    if not inline_pngs:
                        html_content="<a href='qc/%s'><img src='%s' height=250 /></a>" % (s,s)
                    else:
                        pngdata = PNGBase64Encoder().encodePNG(os.path.join(self.__qc_dir,s))
                        html_content="<a href='qc/%s'><img src='data:image/png;base64,%s' height=250 /></a>" % (s,pngdata)
                    html.add(html_content+"<br />")
                    # Link to text files
                    screen_txt = os.path.splitext(s)[0] + '.txt'
                    html.add("<a href='qc/%s'>%s</a><br />" % (screen_txt,screen_txt))
            else:
                html.add("No screens found")
            html.add("</td>")
            html.add("</tr></table>")
            html.add("</div>")
        html.write(os.path.join(self.__dirn,'qc_report.html'))

    def zip(self):
        """Make a zip file containing the report and the images

        Generate the 'qc_report.html' file and make a zip file
        'qc_report.zip' which contains the report plus the
        associated image files, which can be unpacked elsewhere
        for viewing.
        """
        self.html(inline_pngs=True)
        cwd = os.getcwd()
        os.chdir(self.__dirn)
        try:
            z = zipfile.ZipFile('qc_report.zip','w')
            z.write('qc_report.html')
            for sample in self.__samples:
                for boxplot in sample.boxplots():
                    z.write(os.path.join('qc',boxplot))
                for screen in sample.screens():
                    z.write(os.path.join('qc',screen))
                    z.write(os.path.join('qc',os.path.splitext(screen)[0]+'.txt'))
        except Exception, ex:
            print "Exception creating zip archive: %s" % ex
        os.chdir(cwd)

class SolidQCSample:
    """Class for holding QC data for a SOLiD sample

    A SOLiD QC run typically conists of filtered and unfiltered
    boxplots, quality filtering stats, and contamination screens.
    """

    def __init__(self,name,csfasta,qual):
        """Create a new SolidQCSample instance

        Note that the sample name is used as the base name for
        identifying the associated output files.

        Arguments:
          name: name for the sample
          csfasta: associated CSFASTA file
          qual: associated QUAL file
        """
        self.name = name
        self.csfasta = csfasta
        self.qual = qual
        self.__boxplots = []
        self.__screens = []
        self.__filter_stats = {}

    def addBoxplot(self,boxplot):
        """Associate a boxplot with the sample

        Arguments:
          boxplot: boxplot file name
        """
        self.__boxplots.append(boxplot)
        self.__boxplots.sort(cmp_boxplots)

    def addScreen(self,screen):
        """Associate a fastq_screen with the sample

        Arguments:
          screen: fastq_screen file name
        """
        self.__screens.append(screen)
        self.__screens.sort()

    def addFilterStat(self,name,value):
        """Associate a filtering statistic with the sample

        Arguments:
          name: name for the statistic
          value: the value of the statistic
        """
        self.__filter_stats[name] = value

    def boxplots(self):
        """Return list of boxplots for a sample
        """
        return self.__boxplots

    def screens(self):
        """Return list of screens for a sample
        """
        return self.__screens

    def filterStat(self,name):
        """Return value associated with a statistic
        """
        try:
            return self.__filter_stats[name]
        except KeyError:
            return None

# 
class HTMLPageWriter:
    """Generic HTML generation class

    HTMLPageWriter provides basic operations for writing HTML
    files.

    Example usage:

    >>> p = HTMLPageWriter("Example page")
    >>> p.add("This is some text")
    >>> p.write("example.html")
    """

    def __init__(self,title=''):
        """Create a new HTMLPageWriter instance

        Arguments:
          title: optional title for the HTML document
        """
        self.__page_title = str(title)
        self.__content = []
        self.__css_rules = []
        self.__javascript = []

    def add(self,content):
        """Add content to page body

        Note that the supplied content is added to the HTML
        document as-is; no escaping is performed so the content
        can include arbitrary HTML tags. Note also that no
        validation is performed.

        Arguments:
          content: text to add to the HTML document body
        """
        self.__content.append(str(content))

    def addCSSRule(self,css_rule):
        """Add CSS rule

        Defines a CSS rule that will be inlined into a
        "style" tag in the HTML head when the document is
        written out.

        The rule text is added as-is, e.g.:

        >>> p = HTMLPageWriter("Example page")
        >>> p.addCSSRule("body { color: blue; }")

        No checking or validation is performed.

        Arguments:
          css_rule: text defining CSS rule
        """
        self.__css_rules.append(str(css_rule))

    def addJavaScript(self,javascript):
        """Add JavaScript

        Defines a line of Javascript code that will be
        inlined into a "script" tag in the HTML head when
        the document is written out.

        The code is added as-is, no checking or validation
        is performed.

        Arguments:
          javascript: Javascript code
        """
        self.__javascript.append(str(javascript))

    def write(self,filen):
        """Write the HTML document to file

        Generates a HTML document based on the content, styles
        etc that have been defined by calls to the object's
        methods.

        Arguments:
          filen: name of the file to write the document to
        """
        fp = open(filen,'w')
        fp.write("<html>\n")
        # Header
        fp.write("<head>\n")
        fp.write("<title>%s</title>\n" % self.__page_title)
        # CSS rules
        if self.__css_rules:
            fp.write("<style type=\"text/css\">\n")
            fp.write('\n'.join(self.__css_rules))
            fp.write("</style>\n")
        # JavaScript
        if self.__javascript:
            fp.write("<script language='javascript' type='text/javascript'><!--\n")
            fp.write('\n'.join(self.__javascript))
            fp.write("\n--></script>\n")
        fp.write("<head>\n")
        # Body and content
        fp.write("<body>\n")
        fp.write('\n'.join(self.__content))
        fp.write("</body>\n")
        # Finish
        fp.write("</html>\n")
        fp.close()

# Utility class to encode PNGs for embedding in HTML
class PNGBase64Encoder:
    """Utility class to encode PNG file into a base64 string

    Base64 encoded PNGs can be embedded in HTML <img> tags.

    To use:

    >>> p = PNGBase64Encoder.encodePNG("image.png")
    """

    def encodePNG(self,pngfile):
        """Return base64 string encoding a PNG file.
        """
        return base64.b64encode(open(pngfile,'rb').read())

#######################################################################
# Functions
#######################################################################

def cmp_boxplots(b1,b2):
    """Compare the names of two boxplots for sorting purposes
    """
    b1_is_filtered = (os.path.basename(b1).rfind('T_F3') > -1)
    b2_is_filtered = (os.path.basename(b2).rfind('T_F3') > -1)
    if b1_is_filtered and not b2_is_filtered:
        return 1
    elif not b1_is_filtered and b2_is_filtered:
        return -1
    else:
        return cmp(b1,b2)

#######################################################################
# Main program
#######################################################################

if __name__ == "__main__":
    # Set up command line parser
    p = optparse.OptionParser(usage="%prog [options] DIR [ DIR ...]",
                              description=
                              "Generate QC report for each directory DIR.")

    # Deal with command line
    options,arguments = p.parse_args()

    # Check arguments
    if len(arguments) < 1:
        p.error("Takes at least one argument (one or more directories)")
    else:
        for d in arguments:
            print "Generating report for %s" % d
            SolidQCReport(d).zip()
