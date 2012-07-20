#!/bin/env python
#
# qc_report.py: generate report file for qc run
#
import sys
import os
import optparse
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

class QCReport:

    def __init__(self,dirn):
        """Make a new QCReport instance
        """
        self.__dirn = os.path.abspath(dirn)
        self.__qc_dir = os.path.join(self.__dirn,'qc')
        self.__samples = []
        # Get primary data files
        primary_data = Pipeline.GetSolidDataFiles(self.__dirn)
        for data in primary_data:
            sample = os.path.splitext(data[0])[0]
            self.__samples.append(QCSample(sample,data[0],data[1]))
            print "Sample: %s" % sample
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
                if f.startswith(sample.name) or f.startswith(sample.qual):
                    if f.endswith('_boxplot.png'): sample.addBoxplot(f)
                # Screens
                if f.startswith(sample.name):
                    if f.endswith('_screen.png'): sample.addScreen(f)
        # Filtering stats
        stats_file = os.path.join(self.__dirn,"SOLiD_preprocess_filter.stats")
        if os.path.exists(stats_file):
            fp = open(stats_file,'rU')
            for line in fp:
                if line.startswith('#'): continue
                fields = line.rstrip().split('\t')
                sample_name = fields[0]
                for sample in self.__samples:
                    if sample_name == sample.name:
                        sample.addFilterStat('reads',fields[1])
                        sample.addFilterStat('reads_post_filter',fields[2])
                        sample.addFilterStat('diff_reads',fields[3])
                        sample.addFilterStat('percent_filtered',fields[4])
            fp.close()

    def write(self):
        """Write the report
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

        Arguments:
          inline_pngs: if set True then PNG image data will be inlined (report file
            will be more portable)
        """
        html = HTMLPageWriter("QC for %s" % os.path.basename(self.__dirn))
        # Title
        html.add("<h1>QC for %s</h1>" % os.path.basename(self.__dirn))
        # Add styles
        html.addCSSRule("h1 { background-color: grey; }")
        html.addCSSRule("h2 { background-color: lightgrey; display: inline-block; }")
        html.addCSSRule(".sample { margin: 10 10; border: solid 1px grey; padding: 5px; }")
        html.addCSSRule("table.summary { border: solid 1px grey; }")
        html.addCSSRule("table.summary th { background-color: grey; }")
        html.addCSSRule("td { vertical-align: top; }")
        # Index
        html.add("<p>Samples in %s</p>" % self.__dirn)
        html.add("<table class='summary'>")
        html.add("<tr><th>Sample</th><th>Reads</th><th>Reads (filtered)</th><th># filtered</th>"
                 "<th>% filtered</th></tr>")
        for sample in self.__samples:
            html.add("<tr>")
            html.add("<td><a href='#%s'>%s</a></td>" % (sample.name,sample.name))
            html.add("<td>%s</td>" % sample.filterStat('reads'))
            html.add("<td>%s</td>" % sample.filterStat('reads_post_filter'))
            html.add("<td>%s</td>" % sample.filterStat('diff_reads'))
            html.add("<td>%s</td>" % sample.filterStat('percent_filtered'))
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
                    html.add(html_content)
                    # Link to text files
                    screen_txt = os.path.splitext(s)[0] + '.txt'
                    html.add("<a href='qc/%s'>%s</a>" % (screen_txt,screen_txt))
            else:
                html.add("No screens found")
            html.add("</td>")
            html.add("</tr></table>")
            html.add("</div>")
        html.write(os.path.join(self.__dirn,'qc_report.html'))

    def zip(self):
        """Make a zip file containing the report and the images
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

class QCSample:

    def __init__(self,name,csfasta,qual):
        self.name = name
        self.csfasta = csfasta
        self.qual = qual
        self.__boxplots = []
        self.__screens = []
        self.__filter_stats = {}

    def addBoxplot(self,boxplot):
        self.__boxplots.append(boxplot)
        self.__boxplots.sort()

    def addScreen(self,screen):
        self.__screens.append(screen)
        self.__screens.sort()

    def addFilterStat(self,name,value):
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
        return self.__filter_stats[name]

class HTMLPageWriter:

    def __init__(self,title=''):
        self.__page_title = str(title)
        self.__content = []
        self.__css_rules = []
        self.__javascript = []

    def add(self,content):
        """Add content to page body
        """
        self.__content.append(str(content))

    def addCSSRule(self,css_rule):
        """Add CSS rule
        """
        self.__css_rules.append(str(css_rule))

    def addJavaScript(self,javascript):
        """Add JavaScript
        """
        self.__javascript.append(str(javascript))

    def write(self,filen):
        """Write the HTML content to a file
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

class PNGBase64Encoder:

    def encodePNG(self,pngfile):
        return base64.b64encode(open(pngfile,'rb').read())

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
            ##QCReport(d).write()
            ##QCReport(d).html(inline_pngs=True)
            QCReport(d).zip()
