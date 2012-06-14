#!/bin/env python
#
# qc_report.py: generate report file for qc run
#
import sys
import os
import optparse

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
        self.__dirn = dirn
        self.__qc_dir = os.path.join(self.__dirn,'qc')
        self.__samples = []
        # Get primary data files
        primary_data = Pipeline.GetSolidDataFiles(self.__dirn)
        for data in primary_data:
            sample = os.path.splitext(data[0])[0]
            self.__samples.append(QCSample(sample,data[0],data[1]))
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

    def html(self):
        """Write the HTML report
        """
        fp = open(os.path.join(self.__qc_dir,'index.html'),'w')
        # QC plots etc
        for sample in self.__samples:
            fp.write("<h2>%s</h2>" % sample.name)
            fp.write("<table><tr>")
            # Boxplots
            fp.write("<td>")
            if sample.boxplots():
                fp.write("<h3>Boxplots</h3>")
                for b in sample.boxplots():
                    fp.write("<img src='%s' height=250 />\n" % b)
            else:
                fp.write("No boxplots found")
            fp.write("</td>")
            # Screens
            fp.write("<td>")
            if sample.screens():
                fp.write("<h3>Screens</h3>")
                for s in sample.screens():
                    fp.write("<img src='%s' height=250 />\n" % s)
            else:
                fp.write("No screens found")
            fp.write("</td>")
            fp.write("</tr></table>")
        fp.close()

class QCSample:

    def __init__(self,name,csfasta,qual):
        self.name = name
        self.csfasta = csfasta
        self.qual = qual
        self.__boxplots = []
        self.__screens = []

    def addBoxplot(self,boxplot):
        self.__boxplots.append(boxplot)

    def addScreen(self,screen):
        self.__screens.append(screen)

    def boxplots(self):
        """Return list of boxplots for a sample
        """
        return self.__boxplots

    def screens(self):
        """Return list of screens for a sample
        """
        return self.__screens

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
            QCReport(d).html()
    
