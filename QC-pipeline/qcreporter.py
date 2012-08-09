#!/bin/env python
#
#     qcreporter.py: generate report file for NGS qc runs
#     Copyright (C) University of Manchester 2012 Peter Briggs
#
########################################################################
#
# qcreporter.py
#
#########################################################################

"""qcreporter

Generate HTML reports for an NGS QC pipeline runs.
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
    import TabFile
except ImportError, ex:
    print "Error importing modules: %s" % ex
    print "Check PYTHONPATH"
    sys.exit(1)

# Configure logging output
logging.basicConfig(format="[%(levelname)s] %(message)s")

#######################################################################
# Base class definitions
#######################################################################

class QCReporter:
    """Base class for reporting QC runs

    This is a general class for reporting runs of the FLS NGS QC
    pipelines. QC reporters specific to particular pipelines should be
    subclassed from QCReporter and need to implement the 'report'
    method to generate the HTML output.
    """
    def __init__(self,dirn):
        """Create a new QCReporter instance

        Arguments:
          dirn: top-level directory for the run
        """
        # Basic information
        self.__dirn = os.path.abspath(dirn)
        self.__qc_dir = os.path.join(self.__dirn,'qc')
        if not os.path.isdir(self.__qc_dir):
            raise OSError, "QC dir %s not found" % self.qc_dir
        # List of samples
        self.__samples = []
        # HTML document
        self.__html = self.__init_html()

    @property
    def dirn(self):
        """Return top-level directory containing data
        """
        return self.__dirn

    @property
    def qc_dir(self):
        """Return directory holding QC outputs
        """
        return self.__qc_dir

    @property
    def samples(self):
        """Return list of samples
        """
        return self.__samples

    @property
    def html(self):
        """Return HTMLPageWriter instance for the report
        """
        return self.__html

    def addSample(self,sample):
        """Add a QCSample class or subclass to the sample list
        """
        # Add sample to list
        self.__samples.append(sample)
        # Sort sample list on name
        self.__samples.sort(lambda s1,s2: cmp_samples(s1.name,s2.name))

    def __init_html(self):
        """Internal: initialise and populate the HTMLPageWriter
        """
        # Set up HTML document
        html = HTMLPageWriter("QC for %s" % os.path.basename(self.dirn))
        # Title
        html.add("<h1>QC for %s</h1>" % os.path.basename(self.dirn))
        # Add CSS rules
        html.addCSSRule("h1 { background-color: #42AEC2;\n"
                        "     color: white;\n"
                        "     padding: 5px 10px; }")
        html.addCSSRule("h2 { background-color: #8CC63F;\n"
                        "     color: white;\n"
                        "     display: inline-block;\n"
                        "     padding: 5px 15px;\n"
                        "     margin: 0;\n"
                        "     border-top-left-radius: 20;\n"
                        "     border-bottom-right-radius: 20; }")
        html.addCSSRule(".sample { margin: 10 10;\n"
                        "          border: solid 2px #8CC63F;\n"
                        "          padding: 0;\n"
                        "          background-color: #ffe;\n"
                        "          border-top-left-radius: 25;\n"
                        "          border-bottom-right-radius: 25; }")
        html.addCSSRule("table.summary { border: solid 1px grey;\n"
                        "                background-color: white;\n"
                        "                font-size: 90% }")
        html.addCSSRule("table.summary th { background-color: grey;\n"
                        "                   color: white;"
                        "                   padding: 2px 5px; }")
        html.addCSSRule("table.summary td { text-align: right; \n"
                        "                   padding: 2px 5px;\n"
                        "                   border-bottom: solid 1px lightgray; }")
        html.addCSSRule("td { vertical-align: top; }")
        html.addCSSRule("img { background-color: white; }")
        html.addCSSRule("p { font-size: 85%;\n"
                        "    color: #808080; }")
        return html

    def report(self):
        """Generate a HTML report

        This method must be implemented by the subclass.
        """
        raise NotImplementedError,"Subclass must implement 'report' method"

    def zip(self):
        """Make a zip file containing the report and the images

        Generate the 'qc_report.html' file and make a zip file
        'qc_report.zip' which contains the report plus the
        associated image files etc. The archive can then be unpacked
        elsewhere for viewing.
        """
        # Generate the HTML report
        self.report()
        # Move to the top-level directory
        cwd = os.getcwd()
        os.chdir(self.dirn)
        # Create the zip file
        try:
            z = zipfile.ZipFile('qc_report.zip','w')
            z.write('qc_report.html')
            for sample in self.samples:
                for f in sample.zip_includes():
                    # Check if we're adding a file or a whole directory
                    if os.path.isfile(f):
                        # Add a file
                        z.write(f)
                    elif os.path.isdir(f):
                        # Recursively add directory and all its contents
                        add_dir_to_zip(f)
        except Exception, ex:
            print "Exception creating zip archive: %s" % ex
        os.chdir(cwd)

class QCSample:
    """Base class for reporting QC for a single sample

    This is a general class for reporting the QC outputs associated
    with a single sample. It attempts to find all possible associated
    QC products for the given sample name.

    Specific pipelines should subclass QCSample and implement the
    'report' method, which can call the 'report_*' methods to produce
    HTML code specific to the pipeline in question.
    """

    def __init__(self,name,qc_dir):
        """Create a new QCSample instance

        Note that the sample name is used as the base name for
        identifying the associated output files.

        Arguments:
          name: name for the sample
          qc_dir: path to QC directory
        """
        self.name = name
        self.qc_dir = qc_dir
        self.__screens = []
        self.__boxplots = []
        self.__fastqc = None
        self.__zip_includes = []
        # Populate with data
        qc_files = os.listdir(self.qc_dir)
        qc_files.sort()
        # Associate QC outputs with sample names
        sample_name_underscore = self.name+'_'
        sample_name_dot = self.name+'.'
        for f in qc_files:
            # Screens
            if f.startswith(sample_name_underscore):
                if f.endswith('_screen.png'):
                    self.addScreen(f)
            # Boxplots
            if f.endswith('_boxplot.png'):
                if f.startswith(sample_name_dot) or f.startswith(sample_name_underscore):
                    self.addBoxplot(f)
                else:
                    # Try removing "_QV" from names to see if we can match
                    if f.replace('_QV','').startswith(sample_name_underscore) or \
                            f.replace('_QV','').startswith(sample_name_dot):
                        self.addBoxplot(f)
            # FastQC
            if f == "%sfastqc" % sample_name_underscore:
                self.addFastQC(f)

    def screens(self):
        """Return list of screens for a sample
        """
        return self.__screens

    def addScreen(self,screen):
        """Associate a fastq_screen with the sample

        Arguments:
          screen: fastq_screen file name
        """
        # Add to the list and resort
        self.__screens.append(screen)
        self.__screens.sort()
        # Add to the list of files to archive
        self.__zip_includes.append(os.path.join('qc',screen))
        self.__zip_includes.append(os.path.join('qc',os.path.splitext(screen)[0]+'.txt'))

    def addBoxplot(self,boxplot):
        """Associate a boxplot with the sample

        Arguments:
          boxplot: boxplot file name
        """
        # Add to the list and resort
        self.__boxplots.append(boxplot)
        self.__boxplots.sort(cmp_boxplots)
        # Add to the list of files to archive
        self.__zip_includes.append(os.path.join('qc',boxplot))

    def boxplots(self):
        """Return list of boxplots for a sample
        """
        return self.__boxplots

    def addFastQC(self,fastqc_dir):
        """Associate a FastQC output directory with the sample
        """
        self.__fastqc = fastqc_dir
        # Add to the list of files to archive
        self.__zip_includes.append(os.path.join('qc',fastqc_dir))

    def fastqc(self):
        """Return name of FastQC run dir
        """
        return self.__fastqc

    def report_screens(self,html):
        """Write HTML code reporting the fastq screens

        Arguments:
          html: HTMLPageWriter instance to add the generated HTML to
        """
        html.add("<h3>Screens</h3>")
        if self.screens():
            for s in self.screens():
                # Get name/description
                for screen_name in ('model_organisms','other_organisms','rRNA'):
                    try:
                        s.index(screen_name)
                        description = screen_name.replace('_',' ').title()
                    except ValueError:
                        pass
                html.add("<p>%s:</p>" % description)
                # Add Images
                pngdata = PNGBase64Encoder().encodePNG(os.path.join(self.qc_dir,s))
                html_content="<a href='qc/%s'><img src='data:image/png;base64,%s' height=250 /></a>" % (s,pngdata)
                html.add(html_content)
                # Link to text files
                screen_txt = os.path.splitext(s)[0] + '.txt'
                html.add("<p>(See original data for <a href='qc/%s'>%s</a>)</p>" % \
                             (screen_txt,description))
        else:
            html.add("No screens found")

    def report_boxplots(self,html,paired_end=False):
        """Write HTML code reporting the boxplots

        Arguments:
          html: HTMLPageWriter instance to add the generated HTML to
        """
        html.add("<h3>Boxplots</h3>")
        if self.boxplots():
            for b in self.boxplots():
                # Get name/description
                try:
                    # Indicate whether it's pre- or post-filtering
                    b.index('_T_F3')
                    description = "After quality filtering"
                except ValueError:
                    description = "Before quality filtering"
                if paired_end:
                    try:
                        b.index('_F5')
                        description += " (F5)"
                    except ValueError:
                        description += " (F3)"
                html.add("<p>%s:</p>" % description)
                # Add images
                pngdata = PNGBase64Encoder().encodePNG(os.path.join(self.qc_dir,b))
                html_content=\
                    "<a href='qc/%s''><img src='data:image/png;base64,%s' height=250 /></a>" \
                    % (b,pngdata)
                html.add(html_content)
        else:
            html.add("No boxplots found")

    def report_fastqc(self,html):
        """Write HTML code reporting the results from FastQC

        Arguments:
          html: HTMLPageWriter instance to add the generated HTML to
        """
        html.add("<h3>FastQC</h3>")
        if self.__fastqc:
            # Link to the FastQC report HTML
            fastqc_report = os.path.join('qc',self.__fastqc,'fastqc_report.html')
            # Add summary table
            fastqc_summary = os.path.join(self.qc_dir,self.__fastqc,'summary.txt')
            if os.path.exists(fastqc_summary):
                html.add("<table class='fastqc_summary summary'>")
                html.add("<tr><th>FastQC test</th><th>Outcome</th></tr>")
                test_id = 0
                for line in open(fastqc_summary,'rU'):
                    fields = line.split('\t')
                    test_name = fields[1]
                    test_link = fastqc_report + "#M%d" % test_id
                    test_outcome = fields[0]
                    html.add("<tr><td><a href='%s'>%s</a></td><td class='%s'>%s</td></tr>" % \
                                 (test_link,test_name,test_outcome,test_outcome))
                    test_id += 1
                html.add("</table>")
                # Direct link to full report
                html.add("<p><a href='%s'>Full FastQC report for %s</a></p>" % (fastqc_report,
                                                                                self.name))
        else:
            html.add("No FastQC report found")

    def report(self):
        """Generate a HTML report

        This method must be implemented by the subclass.
        """
        raise NotImplementedError,"Subclass must implement 'report' method"


    def zip_includes(self):
        """Return list of files and directories to archive
        """
        return self.__zip_includes
    
def add_dir_to_zip(z,dirn):
    """Recursively add a directory and its contents to a zip archive

    z is a zipfile.ZipFile object already opened for reading; this
    function adds all files in directory dirn and its subdirectories
    to z.
    """
    for f in os.listdir(dirn):
        f1 = os.path.join(dirn,f)
        logging.debug("%s" % f1)
        if os.path.isdir(f1):
            add_dir_to_zip(z,f1)
        else:
            z.write(f1)

#######################################################################
# Illumina-specific class definitions
#######################################################################

class IlluminaQCReporter(QCReporter):
    """Class for reporting QC run on Illumina data

    IlluminaQCReporter assembles the data associated with a QC run for a set
    of Illumina data and generates a HTML document which summarises the
    results for quick review.
    """
    
    def __init__(self,dirn):
        # Initialise base class
        QCReporter.__init__(self,dirn)
        # Locate input fastq.gz files
        primary_data = Pipeline.GetFastqGzFiles(self.dirn)
        for data in primary_data:
            sample = rootname(data[0])
            self.addSample(IlluminaQCSample(sample,self.qc_dir))
            print "Sample: '%s'" % sample
        # Summarise data from fastqc
        self.__stats = TabFile.TabFile(column_names=('Sample',
                                                     'Reads',
                                                     'FastQC Failures',
                                                     'FastQC Warnings'))
        for sample in self.samples:
            self.__stats.append(data=(sample.name,))
            if sample.fastqc():
                # Get the number of reads
                # This is printed in the fastqc_data.txt file, e.g.:
                #Total Sequences	25706792
                fastqc_data_file = os.path.join(self.qc_dir,sample.fastqc(),"fastqc_data.txt")
                reads = '?'
                for line in open(fastqc_data_file,'rU'):
                    if line.startswith('Total Sequences'):
                        reads = line.split('\t')[1]
                        break
                self.__stats[-1]['Reads'] = reads
                # Count warnings and failures from FastQC
                # These are summarised in the summary.txt file, e.g.:
                #PASS	Sequence Length Distribution	ZJ1.fastq.gz
                #WARN	Sequence Duplication Levels	ZJ1.fastq.gz
                #...
                summary_file = os.path.join(self.qc_dir,sample.fastqc(),"summary.txt")
                fastqc_failures = 0
                fastqc_warnings = 0
                for line in open(summary_file,'rU'):
                    status = line.split('\t')[0]
                    if status == 'WARN':
                        fastqc_warnings += 1
                    elif status == 'FAIL':
                        fastqc_failures += 1
                if fastqc_failures == 0: fastqc_failures = '&nbsp;'
                if fastqc_warnings == 0: fastqc_warnings = '&nbsp;'
                self.__stats[-1]['FastQC Failures'] = fastqc_failures
                self.__stats[-1]['FastQC Warnings'] = fastqc_warnings
            else:
                # No fastqc results
                logging.warning("%s: no FastQC results found" % sample.name)
                self.__stats[-1]['Reads'] = '?'
                self.__stats[-1]['FastQC Failures'] = 'No FastQC data'
                self.__stats[-1]['FastQC Warnings'] = '&nbsp;'
            # Check for fastq_screens
            if len(sample.screens()) != 3:
                logging.warning("%s: wrong number of screens" % sample.name)

    def report(self):
        """Write the HTML report

        Writes a HTML document 'qc_report.html' to the top-level
        analysis directory.
        """
        # Add Illumina-specific CSS rules
        self.html.addCSSRule("table.fastqc_summary td.PASS { font-weight: bold;\n"
                             "                               color: green; }")
        self.html.addCSSRule("table.fastqc_summary td.WARN { font-weight: bold;\n"
                             "                               color: orange; }")
        self.html.addCSSRule("table.fastqc_summary td.FAIL { font-weight: bold;\n"
                             "                               color: red; }")
        # Index
        self.html.add("<p>%d samples in %s</p>" % (len(self.samples),self.dirn))
        self.html.add("<table class='summary'>")
        self.html.add("<tr><th>Sample</th><th>Reads</th><th>FastQC Failures</th>"
                      "<th>FastQC Warnings</th></tr>")
        for sample in self.__stats:
            self.html.add("<tr>")
            self.html.add("<td><a href='#%s'>%s</a></td>" % (sample['Sample'],sample['Sample']))
            self.html.add("<td>%s</td>" % sample['Reads'])
            self.html.add("<td>%s</td>" % sample['FastQC Failures'])
            self.html.add("<td>%s</td>" % sample['FastQC Warnings'])
            self.html.add("</tr>")
        self.html.add("</table>")
        # Detailed data for each sample
        for sample in self.samples:
            sample.report(self.html)
        self.html.write(os.path.join(self.dirn,'qc_report.html'))

    def zip(self):
        """Make a zip file containing the report and the images

        Generate the 'qc_report.html' file and make a zip file
        'qc_report.zip' which contains the report plus the
        associated image files, which can be unpacked elsewhere
        for viewing.
        """
        self.report()
        cwd = os.getcwd()
        os.chdir(self.dirn)
        try:
            z = zipfile.ZipFile('qc_report.zip','w')
            z.write('qc_report.html')
            for sample in self.samples:
                for screen in sample.screens():
                    # Add screen files
                    z.write(os.path.join('qc',screen))
                    z.write(os.path.join('qc',os.path.splitext(screen)[0]+'.txt'))
                if sample.fastqc():
                    # Add all files in fastqc dir
                    add_dir_to_zip(z,os.path.join('qc',sample.fastqc()))
        except Exception, ex:
            print "Exception creating zip archive: %s" % ex
        os.chdir(cwd)

class IlluminaQCSample(QCSample):
    """Class for holding QC data for an Illumina sample

    An Illumina QC run typically conists of contamination screens
    and output from FastQC.
    """

    def __init__(self,name,qc_dir):
        """Create a new IlluminaQCSample instance

        Note that the sample name is used as the base name for
        identifying the associated output files.

        Arguments:
          name: name for the sample
          fastq: associated FASTQ file
        """
        # Initialise base class
        QCSample.__init__(self,name,qc_dir)

    def report(self,html):
        """Write HTML report for this sample
        """
        html.add("<div class='sample'>")
        html.add("<a name='%s'><h2>%s</h2></a>" % (self.name,self.name))
        html.add("<table><tr>")
        # FastQC
        html.add("<td>")
        self.report_fastqc(html)
        html.add("</td>")
        # Screens
        html.add("<td>")
        self.report_screens(html)
        html.add("</td>")
        html.add("</tr></table>")
        html.add("</div>")

#######################################################################
# SOLiD-specific class definitions
#######################################################################

class SolidQCReporter(QCReporter):
    """Class for reporting QC run on SOLiD data

    SolidQCReporter assembles the data associated with a QC run for a set
    of SOLiD data and generates a HTML document which summarises the
    results for quick review.
    """

    def __init__(self,dirn):
        """Make a new SolidQCReporter instance

        The SolidQCReporter class checks the contents of the supplied
        directory looking for SOLiD data sets corresponding to samples,
        and collects the associated QC outputs (boxplots, screens and
        filtering statistics).

        Arguments:
          dirn: top-level directory holding the QC run outputs
        """
        # Initialise base class
        QCReporter.__init__(self,dirn)
        self.__paired_end = False
        # Locate stats file and determine if we have paired end data
        stats_file = os.path.join(self.dirn,"SOLiD_preprocess_filter.stats")
        if not os.path.exists(stats_file):
            stats_file = os.path.join(self.dirn,"SOLiD_preprocess_filter_paired.stats")
            if os.path.exists(stats_file):
                self.__paired_end = True
            else:
                stats_file = None
                logging.error("Can't find stats file in %s" % self.dirn)
        # Get primary data files
        if not self.__paired_end:
            primary_data = Pipeline.GetSolidDataFiles(self.dirn)
        else:
            primary_data = Pipeline.GetSolidPairedEndFiles(self.dirn)
        for data in primary_data:
            sample = rootname(data[0])
            if self.__paired_end:
                # Strip trailing "_F3" from names
                sample = sample.replace('_F3','')
            self.addSample(SolidQCSample(sample,self.qc_dir,self.__paired_end))
            print "Sample: '%s'" % sample
        # Filtering stats
        if os.path.exists(stats_file):
            self.__stats = TabFile.TabFile(stats_file,first_line_is_header=True)
            # Fix sample names for paired-end data
            if self.__paired_end:
                for line in self.__stats: line['File'] = line['File'].replace('_paired','')
        else:
            logging.error("Can't find stats file %s" % stats_file)
        # Check on boxplots and screens
        for sample in self.samples:
            if self.__paired_end:
                if len(sample.boxplots()) != 4:
                    logging.warning("%s: wrong number of boxplots" % sample.name)
            else:
                if len(sample.boxplots()) != 2:
                    logging.warning("%s: wrong number of boxplots" % sample.name)
            if len(sample.screens()) != 3:
                logging.warning("%s: wrong number of screens" % sample.name)

    def report(self):
        """Write the HTML report

        Writes a HTML document 'qc_report.html' to the top-level
        analysis directory.
        """
        # Index
        self.html.add("<p>%d samples in %s</p>" % (len(self.samples),self.dirn))
        self.html.add("<table class='summary'>")
        if not self.__paired_end:
            self.html.add("<tr><th>Sample</th><th>Reads</th><th>Reads after filter</th>"
                          "<th># removed</th><th>% removed</th></tr>")
        else:
            self.html.add("<tr><th colspan=2>&nbsp;</th>"
                          "<th colspan=3>Lenient filtering</th>"
                          "<th colspan=3>Strict filtering</th></tr>")
            self.html.add("<tr><th>Sample</th><th>Reads</th><th>Reads after filter</th>"
                          "<th># removed</th><th>% removed</th>"
                          "<th>Reads after filter</th>"
                          "<th># removed</th><th>% removed</th></tr>")
        for sample in self.samples:
            stats = self.__stats.lookup('File',sample.name)[0]
            self.html.add("<tr>")
            self.html.add("<td><a href='#%s'>%s</a></td>" % (sample.name,sample.name))
            self.html.add("<td>%s</td>" % stats['Reads'])
            self.html.add("<td>%s</td>" % stats[2])
            self.html.add("<td>%s</td>" % stats[3])
            self.html.add("<td>%s</td>" % stats[4])
            if self.__paired_end:
                self.html.add("<td>%s</td>" % stats[5])
                self.html.add("<td>%s</td>" % stats[6])
                self.html.add("<td>%s</td>" % stats[7])
            self.html.add("</tr>")
        self.html.add("</table>")
        if self.__paired_end:
            # Add explanation of lenient and strict for paired end
            self.html.add("<p>Number of reads are the sum of F3 and F5 reads</p>")
            self.html.add("<p>&quot;Lenient filtering&quot; filters each F3/F5 read pair only "
                          "on the quality of the F3 reads</p>")
            self.html.add("<p>&quot;Strict filtering&quot; filters each F3/F5 read pair on the "
                          "quality of both F3 and F5 reads</p>")
        # QC plots etc
        for sample in self.samples:
            sample.report(self.html)
        self.html.write(os.path.join(self.dirn,'qc_report.html'))

class SolidQCSample(QCSample):
    """Class for holding QC data for a SOLiD sample

    A SOLiD QC run typically conists of filtered and unfiltered
    boxplots, quality filtering stats, and contamination screens.
    """

    def __init__(self,name,qc_dir,paired_end):
        """Create a new SolidQCSample instance

        Note that the sample name is used as the base name for
        identifying the associated output files.

        Arguments:
          name: name for the sample
          qc_dir: path to QC directory
          paired_end: indicate if data is paired-end
        """
        QCSample.__init__(self,name,qc_dir)
        self.__paired_end = paired_end

    def report(self,html):
        """Write HTML report for this sample
        """
        html.add("<div class='sample'>")
        html.add("<a name='%s'><h2>%s</h2></a>" % (self.name,self.name))
        html.add("<table><tr>")
        # Boxplots
        html.add("<td>")
        self.report_boxplots(html,paired_end=self.__paired_end)
        html.add("</td>")
        # Screens
        html.add("<td>")
        self.report_screens(html)
        html.add("</td>")
        html.add("</tr></table>")
        html.add("</div>")
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

def cmp_samples(s1,s2):
    """Compare the names of two samples for sorting purposes
    """
    # Split names into leading part plus trailing number
    l1,t1 = split_sample_name(s1)
    l2,t2 = split_sample_name(s2)
    if l1 != l2:
        # Return string comparison
        return cmp(s1,s2)
    else:
        # Compare trailing numbers
        return cmp(t1,t2)

def rootname(name):
    """Remove all extensions from name
    """
    try:
        i = name.index('.')
        return name[0:i]
    except ValueError:
        # No dot
        return name

def split_sample_name(name):
    """Split name into leading part plus trailing number

    Returns (start,number)
    """
    i = len(name)
    while i > 0 and name[i-1].isdigit(): i -= 1
    if i > 0 and i < len(name):
        leading = name[:i]
        trailing = int(name[i:])
    else:
        leading = name
        trailing = None
    return (leading,trailing)

#######################################################################
# Main program
#######################################################################

if __name__ == "__main__":
    # Set up command line parser
    p = optparse.OptionParser(usage="%prog [options] DIR [ DIR ...]",
                              description=
                              "Generate QC report for each directory DIR which contains the "
                              "outputs from a QC script (either SOLiD or Illumina). Creates "
                              "a 'qc_report.html' in DIR plus an archive 'qc_report.zip' "
                              "which contains the HTML plus all the necessary files for "
                              "unpacking and viewing elsewhere.")

    # Deal with command line
    options,arguments = p.parse_args()

    # Check arguments
    if len(arguments) < 1:
        p.error("Takes at least one argument (one or more directories)")

    # Identify platform and run the appropriate reporter
    for d in arguments:
        platform = None
        print "Generating report for %s" % d
        try:
            os.path.abspath(d).index('solid')
            platform = 'solid'
        except ValueError:
            try:
                os.path.abspath(d).index('ILLUMINA')
                platform = 'illumina'
            except ValueError:
                pass
        if platform is None:
            logging.error("Unable to identify platform for %s" % d)
        elif platform == 'solid':
            SolidQCReporter(d).zip()
        elif platform == 'illumina':
            IlluminaQCReporter(d).zip()
        else:
            logging.error("Unknown platform '%s'" % platform)
            
