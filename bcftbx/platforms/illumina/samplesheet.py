#!/usr/bin/env python3
#
#     platforms.illumina.samplesheet.py: handle Illumina sample sheets
#     Copyright (C) University of Manchester 2011-2025 Peter Briggs
#
########################################################################
#
# platforms.illumina.samplesheet.py
#
#########################################################################

"""
Provides classes for handling sample sheet files used for BCL-to-Fastq
generation from Illumina sequencing runs.

The core class is:

* SampleSheet: provides an interface to 'CASAVA' and 'bcl2fastq2'
  style sample sheets

This enables extraction and manipulation of header information
and data for individual sample lines within the relevant sections,
plus sanity-checking and format conversion.

Additionally there is a class for predicting the outputs of
BCL-to-Fastq from a sample sheet:

* SampleSheetPredictor: predict sample sheet outputs

This has a number of supporting classes:

* SampleSheetProject: predictor for "projects" from sample sheet
* SampleSheetSample: predictor for "samples"

The module also provides the following utility function:

* samplesheet_index_sequence: extract index sequence from sample
  sheet line
"""

#######################################################################
# Imports
#######################################################################

import os
import sys
import logging
from ... import TabFile
from ...utils import OrderedDictionary
from ...utils import extract_prefix
from ...utils import extract_index
from .exceptions import IlluminaError

# Module specific logger
logger = logging.getLogger(__name__)

#######################################################################
# Data
#######################################################################

SAMPLESHEET_ILLEGAL_CHARS = u"?()[]/\\=+<>:;\"',*^|&. \t"

#######################################################################
# Classes
#######################################################################


class SampleSheet:
    """
    Class for handling Illumina sample sheets

    This is a general class which tries to handle and convert
    between older (i.e. 'CASAVA'-style) and newer (IEM-style) sample
    sheet files for Illumina sequencers, in a transparent manner.

    Experimental Manager (IEM) sample sheet format
    ----------------------------------------------

    The Experimental Manager (IEM) samplel sheets are text files
    with data delimited by '[...]' lines e.g. '[Header]', '[Reads]'
    etc.

    The 'Header' section consists of comma-separated key-value pairs
    e.g. 'Application,HiSeq FASTQ Only'.

    The 'Reads' section consists of values (one per line) (possibly
    number of bases per read?) e.g. '101'.

    The 'Settings' section consists of comma-separated key-value
    pairs e.g. 'Adapter,CTGTCTCTTATACACATCT'.

    The 'Manifests' section consists of comma-separated key-filename
    pairs e.g. 'A,TruSeqAmpliconManifest-1.txt'.

    The 'Data' section contains the data about the lanes, samples
    and barcode indexes. It consists of lines of comma-separated
    values, with the first line being a 'header', and the remainder
    being values for each of those fields.

    CASAVA-style sample sheet format
    --------------------------------

    This older style of sample sheet is used by CASAVA and bcl2fastq
    v1.8.*. It consists of lines of comma-separated values, with the
    first line being a 'header' and the remainder being values for
    each of the fields:

    - FCID: flow cell ID
    - Lane: lane number (integer from 1 to 8)
    - SampleID: ID (name) for the sample
    - SampleRef: reference used for alignment for the sample
    - Index: index sequences (multiple index reads are separated by a
      hyphen e.g. ACCAGTAA-GGACATGA
    - Description: Description of the sample
    - Control: Y indicates this lane is a control lane, N means sample
    - Recipe: Recipe used during sequencing
    - Operator: Name or ID of the operator
    - SampleProject: project the sample belongs to

    Although the CASAVA-style sample sheet looks much like the IEM
    'Data' section, note that it has different fields and field
    names.

    Basic usage
    -----------

    To load data from an IEM-format file:

    >>> iem = SampleSheet('SampleSheet.csv')

    To access 'header' items:

    >>> iem.header_items
    ['IEMFileVersion','Date',..]
    >>> iem.header['IEMFileVersion']
    '4'

    To access 'reads' data:

    >>> iem.reads
    ['101','101']

    To access 'settings' items:

    >>> iem.settings_items
    ['ReverseComplement',...]
    >>> iem.settings['ReverseComplement']
    '0'

    To access 'manifests' items:

    >>> iem.manifests_items
    ['A',...]
    >>> iem.manifests['A']
    'TruSeqAmpliconManifest-1.txt'

    To access 'data' (the actual sample sheet information):

    >>> iem.data.header()
    ['Lane','Sample_ID',...]
    >>> iem.data[0]['Lane']
    1

    etc.

    To load data from a CASAVA style sample sheet:

    >>> casava = SampleSheet('SampleSheet.csv')

    To access the data use the 'data' property:

    >>> casava.data.header()
    ['Lane','SampleID',...]
    >>> casava.data[0]['Lane']
    1

    Accessing data directly
    -----------------------

    The data in the 'Data' section can be accessed directly
    from the SampleSheet instance, e.g.

    >>> iem[0]['Lane']

    is equivalent to

    >>> iem.data[0]['Lane']

    It is also possible to set new values for data items using
    this notation.

    The data lines can be iterated over using:

    >>> for line in iem:
    >>> ...

    To find the number of lines that are stored:

    >>> len(iem)

    To append a new line:

    >>> new_line = iem.append(...)

    Checking and clean-up methods
    -----------------------------

    A number of methods are available to check and fix common
    problems, specifically:

    - detect and replace 'illegal' characters in sample and project
      names
    - detect and fix duplicated sample name, project and lane
      combinations
    - detect blank sample and project names

    Sample sheet reconstruction
    ---------------------------

    Data is loaded it is also subjected to some basic cleaning
    up, including stripping of unnecessary commas and white space.
    The 'show' method returns a reconstructed version of the
    original sample sheet after the cleaning operations were
    performed.

    Arguments:
      sample_sheet (str): path to a sample file to load
        data from
      fp (File): File-like object opened for reading; if
        this is not None then the SampleSheet object will
        be populated from this even if a file is also
        specified
    """
    def __init__(self, sample_sheet=None, fp=None):
        # Input sample sheet
        self.sample_sheet = sample_sheet
        # Format-specific settings
        self._format = None
        self._sample_id = None
        self._sample_name = None
        self._sample_project = None
        # Sections for IEM-format sample sheets
        self._header = OrderedDictionary()
        self._reads = list()
        self._settings = OrderedDictionary()
        self._manifests = OrderedDictionary()
        # Store raw data
        self._data = None
        # Read in file contents
        if fp is None:
            if self.sample_sheet is not None:
                with open(self.sample_sheet, "rt") as fp:
                    self._read_sample_sheet(fp)
        elif fp is not None:
            self._read_sample_sheet(fp)

    def __getitem__(self, key):
        """
        Implement __getitem__ built-in: read 'data' directly
        """
        return self._data[key]

    def __setitem__(self, key, value):
        """
        Implement __setitem__ built-in: write 'data' directly
        """
        self._data[key] = value

    def __delitem__(self, key):
        """
        Implement __delitem__ built-in: delete from 'data' directly
        """
        del(self._data[key])

    def __iter__(self):
        """
        """
        return iter(self._data)

    def __len__(self):
        """
        Implement len() built-in: returns number of lines of data

        """
        if self._data is not None:
            return len(self._data)
        else:
            return 0

    def append(self, *args):
        """
        Create and return a new line of data in the sample sheet

        """
        return self._data.append(*args)

    def _read_sample_sheet(self,fp):
        """
        Internal: consumes and stores sample sheet data

        Arguments:
          fp (File): File-like object for the sample sheet
            that has been opened for reading

        """
        # Assume that initial section is 'Data'
        section = 'Data'
        for i,line in enumerate(fp):
            line = line.rstrip()
            logger.debug(line)
            if not line:
                # Skip blank lines
                continue
            if line.startswith('['):
                # New section
                try:
                    ii = line.index(']')
                    section = line[1:ii]
                    if i == 0:
                        self._format = 'IEM'
                    continue
                except ValueError:
                    raise IlluminaError("Bad section line (#%d): %s" %
                                        (i+1,line))
            if section == 'Data':
                # Store data in TabFile object
                if self._data is None:
                    # Initialise TabFile using this first line
                    # to set the header
                    self._data = TabFile.TabFile(column_names=line.split(','),
                                                 delimiter=',')
                    # If this is the first line then assume CASAVA
                    if i == 0:
                        self._format = 'CASAVA'
                else:
                    self._data.append(tabdata=line)
            elif section == 'Header':
                # Header lines are comma-separated PARAM,VALUE lines
                self._set_section_param_value(line,self._header)
            elif section == 'Reads':
                # Read lines are one value per line
                value = line.rstrip(',')
                if value:
                    self._reads.append(value)
            elif section == 'Settings':
                # Settings lines are comma-separated PARAM,VALUE lines
                self._set_section_param_value(line,self._settings)
            elif section == 'Manifests':
                # Manifests lines are comma-separated PARAM,VALUE lines
                self._set_section_param_value(line,self._manifests)
            elif section is None:
                raise IlluminaError("Not a valid sample sheet?")
            else:
                raise IlluminaError(f"'{section}': unrecognised section "
                                    f" (not a valid IEM sample sheet?)")
        # Clean up data
        if self._data is not None:
            # Remove surrounding whitespace and double quotes from values
            for line in self._data:
                for item in self._data.header():
                    try:
                        line[item] = str(line[item]).strip('"').strip()
                    except AttributeError:
                        pass
            # Remove lines that appear to be commented (after quote removal)
            for i,line in enumerate(self._data):
                if str(line).startswith('#'):
                    del(self._data[i])
            # Remove empty trailing lines
            while len(self._data):
                if ''.join([str(x) for x in self._data[-1]]):
                    break
                del(self._data[-1])
        # Guess the format if not already set
        if self._format is None:
            if not self._header and \
               not self._reads and \
               not self._settings:
                format_ = 'CASAVA'
            else:
                format_ = 'IEM'
        # Set the column names
        self._set_column_names()

    def _set_column_names(self):
        """
        Internal: determine and store the sample id, name and project columns
        """
        if self._data is not None:
            column_names = self.column_names
            if 'SampleID' in column_names:
                self._sample_id = 'SampleID'
            elif 'Sample_ID' in column_names:
                self._sample_id = 'Sample_ID'
            else:
                raise IlluminaError("Unable to locate sample id "
                                    "field in sample sheet header")
            if 'SampleProject' in column_names:
                self._sample_project = 'SampleProject'
            elif 'Sample_Project' in column_names:
                self._sample_project = 'Sample_Project'
            else:
                raise IlluminaError("Unable to locate sample project "
                                    "field in sample sheet header")
            if 'Sample_Name' in column_names:
                self._sample_name = 'Sample_Name'

    def _set_section_param_value(self,line,d):
        """
        Internal: process a 'key,value' line

        This method determines the value associated with
        a parameter (aka 'key') from the supplied line, and
        assigns the value to the parameter in the supplied
        dictionary.

        It is assumed that the line consists of a key-value
        pair separated by a comma, and any additional
        trailing comma characters are discarded.

        One execption is if the value is double-quoted and
        also contains one or more comma characters; in this
        case the whole of the double-quoted value will be
        retained (including the quotes).

        """
        fields = line.split(",")
        param = fields[0]
        try:
            value = fields[1]
        except IndexError:
            # No delimiter i.e. line consists only of 'key'
            value = ""
        # Handle quoted value containing commas
        if value.startswith('"'):
            for f in fields[2:]:
                if value.endswith('"'):
                    break
                else:
                    value += f",{f}"
        if param:
            d[param] = value

    @property
    def format(self):
        """
        Return format for sample sheet

        Returns:
          String: 'CASAVA', 'IEM' or None.
        """
        return self._format

    @property
    def has_lanes(self):
        """
        Indicates whether 'Lane' column is defined

        Returns:
          Boolean: True if 'Lane' is present, False if not.
        """
        return ('Lane' in self.column_names)

    @property
    def sample_id_column(self):
        """
        Return name of column with sample ID

        Returns:
          String: column label e.g. 'SampleID'.
        """
        return self._sample_id

    @property
    def sample_name_column(self):
        """
        Return name of column with sample name

        Returns:
          String: column label e.g. 'Sample_Name'.
        """
        return self._sample_name

    @property
    def sample_project_column(self):
        """
        Return name of column with sample project name

        Returns:
          String: column label e.g. 'SampleProject'.
        """
        return self._sample_project

    @property
    def header_items(self):
        """
        Return list of items listed in the '[Header]' section

        If the sample sheet didn't contain a '[Header]' section
        then returns an empty list.

        Returns:
          List of item names.
        """
        return self._header.keys()

    @property
    def header(self):
        """Return ordered dictionary for the '[Header]' section

        If the sample sheet didn't contain a '[Header]' section
        then returns an empty OrderedDictionary.

        Returns:
          OrderedDictionary where keys are data items.
        """
        return self._header

    @property
    def reads(self):
        """
        Return list of values from the '[Reads]' section

        If the sample sheet didn't contain a '[Reads]' section
        then returns an empty list.
        
        Returns:
          List of values.
        """
        return self._reads

    @property
    def settings_items(self):
        """
        Return list of items listed in the '[Settings]' section

        If the sample sheet didn't contain a '[Settings]' section
        then returns an empty list.

        Returns:
          List of item names.

        """
        return self._settings.keys()

    @property
    def settings(self):
        """
        Return ordered dictionary for the '[Settings]' section

        If the sample sheet didn't contain a '[Settings]' section
        then returns an empty OrderedDictionary.

        Returns:
          OrderedDictionary where keys are data items.

        """
        return self._settings

    @property
    def manifests_items(self):
        """
        Return list of keys listed in the '[Manifests]' section

        If the sample sheet didn't contain a '[Manifests]' section
        then returns an empty list.

        Returns:
          List of item names.

        """
        return self._manifests.keys()

    @property
    def manifests(self):
        """
        Return ordered dictionary for the '[Manifests]' section

        If the sample sheet didn't contain a '[Manifests]' section
        then returns an empty OrderedDictionary.

        Returns:
          OrderedDictionary where keys are data items.

        """
        return self._manifests

    @property
    def data(self):
        """
        Return TabFile object for the sample information

        This returns the per-sample data from '[Data]' section (if
        the original sample sheet was in IEM format), or the
        entire file (if it was in CASAVA format).

        Returns:
          TabFile object.

        """
        return self._data

    @property
    def column_names(self):
        """
        Return list of column names for the data section

        Returns:
           List.

        """
        if self._data is not None:
            return [x for x in self._data.header()]
        else:
            return []

    @property
    def duplicated_names(self):
        """
        List duplicate samples within a project

        Returns a list where each item is another list with a group
        of lines from the sample sheet which together consitute a set
        of duplicates.

        If there is no 'Data' section in the sample sheet then an
        empty list is returned.

        """
        if self._data is None: return []
        samples = {}
        for line in self._data:
            try:
                index = line['Index']
            except KeyError:
                try:
                    index = "%s-%s" % (line['index'],line['index2'])
                except KeyError:
                    try:
                        index = line['index']
                    except KeyError:
                        # No index columns
                        index = None
            try:
                lane = line['Lane']
            except KeyError:
                lane = None
            name = ((line[self._sample_id],
                     line[self._sample_project],
                     index,lane))
            if name not in samples:
                samples[name] = [line]
            else:
                samples[name].append(line)
        duplicates = [s for s in [samples[name] for name in samples]
                      if len(s) > 1]
        return duplicates

    @property
    def illegal_names(self):
        """
        List lines with illegal characters in sample names or projects

        Returns a list of lines where the sample names and/or sample project
        names contain illegal characters.

        If there is no 'Data' section in the sample sheet then an
        empty list is returned.

        """
        if self._data is None: return []
        illegal_names = []
        for line in self._data:
            for c in SAMPLESHEET_ILLEGAL_CHARS:
                illegal = (str(line[self._sample_id]).count(c) > 0) \
                          or (str(line[self._sample_project]).count(c) > 0)
                if not illegal and self._sample_name is not None:
                    illegal = str(line[self._sample_name]).count(c) > 0
                if illegal:
                    illegal_names.append(line)
                    break
        return illegal_names

    @property
    def empty_names(self):
        """List lines with blank sample or project names

        Returns a list of lines with blank sample or project names.

        If there is no 'Data' section in the sample sheet then an
        empty list is returned.

        """
        if self._data is None: return []
        empty_names = []
        for line in self._data:
            if str(line[self._sample_id]).strip() == '' \
               or str(line[self._sample_project]).strip() == '':
                empty_names.append(line)
        return empty_names

    def fix_duplicated_names(self):
        """
        Rename samples to remove duplicated sample names within a project

        Appends a numeric index to sample names in the duplicated lines
        in order to remove the duplication.

        """
        for duplicate in self.duplicated_names:
            for i in range(0,len(duplicate)):
                duplicate[i][self._sample_id] = "%s_%d" % \
                                                (duplicate[i][self._sample_id],
                                                 i+1)

    def fix_illegal_names(self):
        """
        Replace illegal characters in sample and project name pairs

        Replaces any illegal characters with underscores.

        """
        for line in self.illegal_names:
            for c in SAMPLESHEET_ILLEGAL_CHARS:
                line[self._sample_id] = \
                    str(line[self._sample_id]).strip().replace(c,'_').strip('_')
                line[self._sample_project] = \
                    str(line[self._sample_project]).strip().replace(c,'_').strip('_')
                if self._sample_name is not None:
                    line[self._sample_name] = \
                        str(line[self._sample_name]).strip().replace(c,'_').strip('_')

    def show(self,fmt=None):
        """
        Reconstructed version of original sample sheet

        Return a string containing a reconstructed version of
        the original sample sheet, after any cleaning operations
        (e.g. removal of unnecessary commas and whitespace) have
        been applied.

        The format of the output will be the same as that of the
        input, unless explicitly reset using the 'fmt' option.

        Arguments:
           fmt (str): optional, explicitly set the format for
             the output. Can be either 'CASAVA' or 'IEM'.

        Returns:
          String with the reconstructed sample sheet contents.

        """
        # Set output format
        if fmt is None:
            format_ = self._format
        else:
            format_ = str(fmt)
        # Reconstruct the sample sheet
        s = []
        if format_ == 'IEM':
            s.append('[Header]')
            for param in self._header:
                s.append('%s,%s' % (param,self._header[param]))
            s.append('')
            s.append('[Reads]')
            for value in self._reads:
                s.append(value)
            s.append('')
            s.append('[Settings]')
            for param in self._settings:
                s.append('%s,%s' % (param,self._settings[param]))
            if self._data is not None:
                s.append('')
                s.append('[Data]')
                s.append(','.join(self._data.header()))
                for line in self._data:
                    s.append(str(line))
        else:
            header = ('FCID','Lane','SampleID','SampleRef','Index',
                      'Description','Control','Recipe','Operator',
                      'SampleProject')
            s.append(','.join(header))
            for line in self._data:
                values = []
                for item in header:
                    try:
                        values.append(str(line[item]))
                    except KeyError:
                        if item == 'FCID':
                            values.append('FC0001')
                        elif item == 'Lane':
                            values.append('1')
                        elif item == 'SampleID':
                            values.append(line['Sample_ID'])
                        elif item == 'Index':
                            try:
                                values.append("%s-%s" %
                                              (line['index'].strip(),
                                               line['index2'].strip()))
                            except KeyError:
                                # Assume not dual-indexed (no index2)
                                try:
                                    values.append(line['index'].strip())
                                except KeyError:
                                    # No index
                                    values.append('')
                        elif item == 'SampleProject':
                            values.append(line['Sample_Project'])
                        else:
                            values.append('')
                s.append(','.join([str(x) for x in values]))
        return '\n'.join(s)

    def write(self,filen=None,fp=None,fmt=None):
        """
        Output the sample sheet data to file or stream

        The format of the output will be the same as that of the
        input, unless explicitly reset using the 'fmt' option.

        Arguments:
          filen: (optional) name of file to write to; ignored if fp is
            also specified
          fp: (optional) a file-like object opened for writing; used in
            preference to filen if set to a non-null value
            Note that the calling program must close the stream in
            these cases.
          fmt (str): optional, explicitly set the format for
            the output. Can be either 'CASAVA' or 'IEM'.

        """
        if fp is None:
            if filen is None:
                fp = sys.stdout
            else:
                fp = open(filen, "wt")
        fp.write("%s\n" % self.show(fmt=fmt))
        if filen is not None:
            fp.close()

    def predict_output(self, fmt="CASAVA"):
        """
        Predict the expected outputs from the sample sheet content

        Constructs and returns a simple dictionary-based data structure
        which predicts the output data structure that will produced by
        running the bcl2fastq conversion software using the sample sheet
        data.

        The return structure depends on the format specified via the
        ``fmt`` argument, either:

        - 'CASAVA': reproduce the structure when running either
          CASAVA or the bcl2fastq v1.8.* software, or
        - 'bcl2fastq2': reproduce the structure from bcl2fastq v2.

        For 'CASAVA' formatted output the returned structure is:

        { 'project_1': {
                         'sample_1': [ name1, name2, ... ],
                         'sample_2': [ ... ],
                         ... }
          'project_2': {
                         'sample_3': [ ... ],
                         ... }
          ... }

        For 'bcl2fastq2' formatted output it is:

        { 'project_1': [ name1, name2, ...],
          'project_2': [ name1, name2, ...],
          ... }

        or:

        { 'project_1': [ dir/name1, dir/name2, ...],
          'project_2': [ name1, name2, ...],
          ... }

        if some samples will be written will be written to
        subdirectories according to the sample sheet.

        """
        projects = {}
        if str(fmt).upper() == "CASAVA":
            # CASAVA/bcl2fastq v1.8.*-style output
            for line in self.data:
                # Sample and project names
                project = "Project_%s" % line[self._sample_project]
                sample = "Sample_%s" % line[self._sample_id]
                if project not in projects:
                    samples = {}
                else:
                    samples = projects[project]
                if sample not in samples:
                    samples[sample] = []
                # Index sequence
                indx = samplesheet_index_sequence(line)
                if not indx:
                    indx = "NoIndex"
                # Lane
                try:
                    lane = line['Lane']
                except KeyError:
                    lane = 1
                # Construct base name
                samples[sample].append("%s_%s_L%03d" % (line[self._sample_id],
                                                        indx,lane))
                projects[project] = samples
        elif fmt == "bcl2fastq2":
            # bcl2fastq v2-style output
            sample_names = []
            for line in self.data:
                project = str(line[self._sample_project])
                if self._sample_name:
                    name = str(line[self._sample_name])
                else:
                    name = None
                id_ = str(line[self._sample_id])
                prefix = ''
                if name:
                    sample = name
                    if id_ != name:
                        prefix = '%s/' % id_
                else:
                    sample = id_
                if self.has_lanes:
                    lane_id = "_L%03d" % line['Lane']
                else:
                    lane_id = ""
                if project not in projects:
                    fqs = []
                else:
                    fqs = projects[project]
                try:
                    i = sample_names.index(sample) + 1
                except ValueError:
                    sample_names.append(sample)
                    i = len(sample_names)
                # Construct fastq basename
                fqs.append("%s%s_S%d%s" % (prefix,sample,i,lane_id))
                projects[project] = fqs
        else:
            # Unknown format
            raise IlluminaError(f"'{fmt}': unknown format")
        return projects


class SampleSheetPredictor:
    """
    Class to predict outputs of a sample sheet file

    Supplied with a sample sheet file, or the contents of a
    sample sheet, this class can predict the expected output
    projects, sample names and Fastq file names according to
    the bcl-to-fastq conversion software that is used and the
    type of data that is present.

    By default the predicted outputs are for single-ended data
    converted using 'bcl2fastq2' with no lane information. The
    `set` method can be invoked to predict outputs for other
    configurations.

    It uses two additional helper classes `SampleSheetProject`
    and `SampleSheetSample`, which hold information about
    the predicted projects and samples.

    Example usage: create a new predictor object:

    >>> predictor = SampleSheetPredictor(sample_sheet_file="SampleSheet.txt")

    To get a list of the expected project names:

    >>> project_names = predictor.project_names

    To get a `SampleSheetProject` corresponding to a project
    name:

    >>> predicted_project = predictor.get_project("MyProject")

    To loop over the `SampleSheetSamples` in the project
    corresponding to the expected samples and get a list of the
    expected Fastqs:

    >>> for predicted_sample in predicted_project.samples:
    ...    for fq in predicted_sample.fastqs:
    ...       print("Predicted Fastq: %s" % fq)

    To predict Fastqs for paired-end data:

    >>> predictor.set(paired_end=True)
    >>> for p in predictor.projects:
    ...    for s in p.samples:
    ...       for fq in s.fastqs:
    ...          print(fq)

    (See also the `SampleSheetProject` and `SampleSheetSample`)

    Available properties:

    - projects: list of the associated SampleSheetProjects
    - nprojects: number of predicted projects
    - project_names: list of the predicted project names

    Available methods:

    - get_project: fetch SampleSheetProject for project name
    - set: configure the predictor for different bcl-to-fastq
        software, conversion options, and data endedness

    Arguments:
      sample_sheet (SampleSheet): a SampleSheet instance to use
        for prediction (if None then must provide a file via
        the `sample_sheet_file` argument; if both are provided
        then `sample_sheet` takes precedence)
      sample_sheet_file (str): path to a sample sheet file, if
        `sample_sheet` argument is None
    """
    def __init__(self, sample_sheet=None, sample_sheet_file=None):
        # Initialise
        self.projects = []
        self._predict_for_package = "bcl2fastq2"
        self._predict_paired_end = False
        self._predict_no_lane_splitting = False
        self._predict_for_lanes = None
        self._predict_for_reads = None
        self._include_index_reads = False
        self._force_sample_dir = False
        # Read in data
        if sample_sheet is None:
            sample_sheet = SampleSheet(sample_sheet_file)
        # Put data into lane order (if lanes specified)
        if sample_sheet.has_lanes:
            sample_sheet.data.sort(lambda line: line['Lane']
                                   if line['Lane'] != '' else 99999)
        s_index = 0
        for line in sample_sheet:
            # Get project and sample info
            project_name = str(line[sample_sheet.sample_project_column])
            sample_id = str(line[sample_sheet.sample_id_column])
            try:
                sample_name = str(line[sample_sheet.sample_name_column])
            except TypeError:
                sample_name = sample_id
            if not sample_id:
                sample_id = None
            if not sample_name:
                sample_name = None
            project = self.add_project(project_name)
            sample = project.add_sample(sample_id,
                                        sample_name=sample_name)
            # Fetch barcode and lane
            index_seq = samplesheet_index_sequence(line)
            if index_seq is None:
                index_seq = "NoIndex"
            if sample_sheet.has_lanes:
                lane = line['Lane']
            else:
                lane = None
            sample.add_barcode(index_seq,lane=lane)
            # Sample index
            if sample.s_index is None:
                s_index += 1
                sample.s_index = s_index

    @property
    def nprojects(self):
        """
        Return number of projects
        """
        return len(self.projects)

    @property
    def project_names(self):
        """
        Return list of project names stored in the predictor
        """
        return sorted([str(p) for p in self.projects])

    def get_project(self,project_name):
        """
        Fetch a SampleSheetProject by name

        Raises KeyError if the named project isn't found
        """
        for project in self.projects:
            if project.name == project_name:
                return project
        raise KeyError("%s: project not found" % project_name)

    def add_project(self,project_name):
        """
        Add a new project

        Creates a new SampleSheetProject object for
        project_name, or returns an existing one if it exists
        for this name

        Arguments:
          project_name (str): name for project to add

        Returns:
          SampleSheetProject: SampleSheetProject for the
            supplied project name
        """
        try:
            return self.get_project(project_name)
        except KeyError:
            project = SampleSheetProject(project_name)
            self.projects.append(project)
            return project

    def set(self,package=None,paired_end=None,
            no_lane_splitting=None,lanes=None,
            reads=None,include_index_reads=None,
            force_sample_dir=None):
        """
        Configure settings for prediction

        - package: target bcl to fastq conversion package
          (can be 'bcl2fastq2' or 'casava')
        - paired_end: if True then predict outputs as if
          data is paired end (i.e. R1 and R2 pairs)
          (NB ignored if 'reads' argument is set)
        - no_lane_splitting: if True then predict outputs
          as if --no-lane-splitting was used for bcl2fastq
        - lanes: if set then should be a list of lane
          numbers that will be used when generating Fastq
          names
        - reads: if set then should be a list or other
          iterable with the reads to include in the
          prediction (e.g. ('R1','R2','I1','R3'))
        - include_index_reads: if True then includes
          index reads (i.e. I1,...) in prediction
          (NB ignored if 'reads' argument is set)
        - force_sample_dir: if True then force insertion
          of a 'sample name' directory for IEM4 sample
          sheets where sample name and ID are the same
        """
        if package is not None:
            self._predict_for_package = package
        if paired_end is not None:
            self._predict_paired_end = paired_end
        if no_lane_splitting is not None:
            self._predict_no_lane_splitting = no_lane_splitting
        self._predict_for_lanes = lanes
        if reads is not None:
            self._predict_for_reads = reads
        if include_index_reads is not None:
            self._include_index_reads = include_index_reads
        if force_sample_dir is not None:
            self._force_sample_dir = force_sample_dir
        # Configure projects with same settings
        for project in self.projects:
            project.set(package=package,
                        paired_end=paired_end,
                        no_lane_splitting=no_lane_splitting,
                        lanes=lanes,
                        reads=reads,
                        include_index_reads=include_index_reads,
                        force_sample_dir=force_sample_dir)


class SampleSheetProject:
    """
    Class describing a project from a sample sheet file

    This class describes a predicted project from a
    samplesheet. It is normally created, managed and
    returned by a `SampleSheetPredictor` instance, rather
    than being created directly.

    The predicted samples within the project are
    described by a set of SampleSheetSample instances.

    Available properties:

    - name: project name
    - samples: list of associated SampleSheetSamples
    - sample_ids: list of associated sample IDs
    - dir_name: predicted subdirectory name for the
        project

    Available methods:

    - get_sample: fetch SampleSheetSample by sample ID
    - set: configure the predictor for different bcl-to-fastq
        software, conversion options, and data endedness  

    Arguments:
      project_name (str): name for the project  
    """
    def __init__(self, project_name):
        self.name = project_name
        self.samples = []
        self._predict_for_package = "bcl2fastq2"
        self._predict_paired_end = False
        self._predict_no_lane_splitting = False
        self._predict_for_lanes = None
        self._predict_for_reads = None
        self._include_index_reads = False
        self._force_sample_dir = False

    @property
    def sample_ids(self):
        """
        Return a list of sample ID's in the project
        """
        return sorted([s.sample_id for s in self.samples],
                      key=lambda x: (extract_prefix(x),
                                     extract_index(x)))

    @property
    def dir_name(self):
        """
        Predict subdirectory name for project
        """
        if self._predict_for_package == "casava":
            if self.name:
                return "Project_%s" % self.name
            else:
                return self.name
        elif self._predict_for_package == "bcl2fastq2":
            return self.name

    def get_sample(self, sample_id):
        """
        Fetch a SampleSheetSample by name

        Raises KeyError if the specified sample id isn't found
        """
        for sample in self.samples:
            if sample.sample_id == sample_id:
                return sample
        raise KeyError("%s: sample not found" % sample_id)

    def add_sample(self, sample_id, sample_name=None, s_index=None):
        """
        Add a new sample

        Creates a new SampleSheetSampleProject object for
        sample_id, or returns an existing one if it exists for
        this id.

        Arguments:
          sample_id (str): id for the sample
          sample_name (str): (optional) corresponding sample
            name
          s_index (integer): (optional) the bcl2fastq sample
            index

        Returns:
          SampleSheetProject: SampleSheetProject for the
            supplied project name
        """
        if sample_id is None:
            # Special case: no ID defined, use name instead
            sample_id = sample_name
        elif sample_name is not None and sample_id != sample_name:
            # Special case when ID and name differ, then swap
            # over names
            sample_id,sample_name = sample_name,sample_id
        try:
            return self.get_sample(sample_id)
        except KeyError:
            sample = SampleSheetSample(sample_id,
                                       sample_name=sample_name)
            self.samples.append(sample)
            return sample

    def set(self,package=None,paired_end=None,
            no_lane_splitting=None,lanes=None,
            reads=None,include_index_reads=None,
            force_sample_dir=None):
        """
        Configure settings for prediction

        - package: target bcl to fastq conversion package
          (can be 'bcl2fastq2' or 'casava')
        - paired_end: if True then predict outputs as if
          data is paired end (i.e. R1 and R2 pairs)
          (NB ignored if 'reads' argument is set)
        - no_lane_splitting: if True then predict outputs
          as if --no-lane-splitting was used for bcl2fastq
        - lanes: if set then should be a list of lane
          numbers that will be used when generating Fastq
          names
        - reads: if set then should be a list or other
          iterable with the reads to include in the
          prediction (e.g. ('R1','R2','I1','R3'))
        - include_index_reads: if True then includes
          index reads (i.e. I1,...) in prediction
          (NB ignored if 'reads' argument is set)
        - force_sample_dir: if True then force insertion
          of a 'sample name' directory for IEM4 sample
          sheets where sample name and ID are the same
        """
        if package is not None:
            self._predict_for_package = package
        if paired_end is not None:
            self._predict_paired_end = paired_end
        if no_lane_splitting is not None:
            self._predict_no_lane_splitting = no_lane_splitting
        self._predict_for_lanes = lanes
        if reads is not None:
            self._predict_for_reads = reads
        if include_index_reads is not None:
            self._include_index_reads = include_index_reads
        if force_sample_dir is not None:
            self._force_sample_dir = force_sample_dir
        # Cascade the settings to child samples
        for sample in self.samples:
            sample.set(package=package,
                       paired_end=paired_end,
                       no_lane_splitting=no_lane_splitting,
                       lanes=lanes,
                       reads=reads,
                       include_index_reads=include_index_reads,
                       force_sample_dir=force_sample_dir)

    def __repr__(self):
        # Implement repr built-in
        return str(self.name)


class SampleSheetSample:
    """
    Class describing a sample from a sample sheet file

    This class describes a predicted sample from a
    samplesheet. It is normally created, managed and
    returned by a `SampleSheetProject` instance, rather
    than being created directly.

    Available properties and data:

    - sample_id: sample ID
    - sample_name: sample name
    - s_index: index number for the sample, for bcl2fastq
    - barcode_seqs: list of barcode sequences associated
      with the sample
    - barcodes: dictionary mapping barcodes to lists of
      lanes for the sample
    - dir_name: predicted subdirectory name for the sample

    Available methods:

    - lanes: list lanes associated with the sample, or with a
      specific barcode
    - fastqs: list of predicted Fastq files for the sample
    - set: configure the predictor for different bcl-to-fastq
      software, conversion options, and data endedness

    Arguments:
      sample_id (str): id for the sample
      sample_name (str): (optional) corresponding sample
        name
      s_index (integer): (optional) the bcl2fastq sample
        index
    """
    def __init__(self, sample_id, sample_name=None, s_index=None):
        self.sample_id = sample_id
        self.sample_name = sample_name
        self.s_index = s_index
        self.barcodes = {}
        self._predict_for_package = "bcl2fastq2"
        self._predict_paired_end = False
        self._predict_no_lane_splitting = False
        self._predict_for_lanes = None
        self._predict_for_reads = None
        self._include_index_reads = False
        self._force_sample_dir = False

    @property
    def barcode_seqs(self):
        """
        Return a list of barcode (index) sequences for the sample
        """
        return sorted([b for b in self.barcodes.keys()])

    @property
    def dir_name(self):
        """
        Predict subdirectory name for sample fastqs
        """
        if self._predict_for_package == "casava":
            return "Sample_%s" % self.sample_id
        elif self._predict_for_package == "bcl2fastq2":
            if (self.sample_id != self.sample_name) or \
               self._force_sample_dir:
                return self.sample_name
            else:
                return None
        
    def add_barcode(self,barcode_seq,lane=None):
        """
        Associate a barcode sequence with a sample

        Arguments:
          barcode_seq (str): barcode sequence to add
          lane (int): lane to associate with the barcode
            (None if no lane information is available)
        """
        if barcode_seq not in self.barcodes:
            self.barcodes[barcode_seq] = []
        if lane and lane not in self.barcodes[barcode_seq]:
            self.barcodes[barcode_seq].append(int(lane))

    def lanes(self,barcode_seq="NoIndex"):
        """
        Fetch the lanes associated with the barcode
        """
        return sorted(self.barcodes[barcode_seq])

    def fastqs(self):
        """
        Return list of predicted Fastq names

        The predicted Fastq names are paths for the Fastq
        files relative to the 'sample' directory, and are
        constructed according to the settings supplied
        via the 'set' method.
        """
        predicted_fastqs = []
        if self._predict_for_reads:
            base_reads = sorted([r for r in self._predict_for_reads])
        elif self._predict_paired_end:
            base_reads = ["R1","R2"]
        else:
            base_reads = ["R1",]
        include_index_reads = (self._include_index_reads and
                               self._predict_for_reads is None)
        if self._predict_for_package == "bcl2fastq2":
            for barcode_seq in self.barcode_seqs:
                # Add index reads?
                if include_index_reads and barcode_seq:
                    index_reads = ["I%d" % (i+1)
                                   for i in range(len(barcode_seq.split('-')))]
                    reads = index_reads + base_reads
                else:
                    reads = base_reads
                # Check if we need to split lanes
                if self._predict_no_lane_splitting:
                    # No lanes
                    for read in reads:
                        fastq = "%s_S%d_%s_001.fastq.gz" % \
                                (self.sample_id,
                                 self.s_index,
                                 read)
                        predicted_fastqs.append(fastq)
                else:
                    # Output with lane information
                    if self._predict_for_lanes:
                        lanes = self._predict_for_lanes
                    elif self.lanes(barcode_seq):
                        lanes = self.lanes(barcode_seq)
                    else:
                        lanes = (1,)
                    for lane in lanes:
                        for read in reads:
                            fastq = "%s_S%d_L%03d_%s_001.fastq.gz" % \
                                    (self.sample_id,
                                     self.s_index,
                                     lane,
                                     read)
                            predicted_fastqs.append(fastq)
        elif self._predict_for_package == "casava":
            reads = base_reads
            for barcode_seq in self.barcode_seqs:
                if self._predict_for_lanes:
                    lanes = self._predict_for_lanes
                elif self.lanes(barcode_seq):
                    lanes = self.lanes(barcode_seq)
                else:
                    lanes = (1,)
                for lane in lanes:
                    for read in reads:
                        fastq = "%s_%s_L%03d_%s_001.fastq.gz" % \
                                (self.sample_id,
                                 barcode_seq,
                                 lane,read)
                        predicted_fastqs.append(fastq)
        # Return predicted Fastqs
        return predicted_fastqs

    def set(self,package=None,paired_end=None,
            no_lane_splitting=None,lanes=None,
            reads=None,include_index_reads=None,
            force_sample_dir=None):
        """
        Configure settings for prediction

        - package: target bcl to fastq conversion package
          (can be 'bcl2fastq2' or 'casava')
        - paired_end: if True then predict outputs as if
          data is paired end (i.e. R1 and R2 pairs)
          (NB ignored if 'reads' argument is set)
        - no_lane_splitting: if True then predict outputs
          as if --no-lane-splitting was used for bcl2fastq
        - lanes: if set then should be a list of lane
          numbers that will be used when generating Fastq
          names
        - reads: if set then should be a list or other
          iterable with the reads to include in the
          prediction (e.g. ('R1','R2','I1','R3'))
        - include_index_reads: if True then includes
          index reads (i.e. I1,...) in prediction
          (NB ignored if 'reads' argument is set)
        - force_sample_dir: if True then force insertion
          of a 'sample name' directory for IEM4 sample
          sheets where sample name and ID are the same
        """
        if package is not None:
            self._predict_for_package = package
        if paired_end is not None:
            self._predict_paired_end = paired_end
        if no_lane_splitting is not None:
            self._predict_no_lane_splitting = no_lane_splitting
        self._predict_for_lanes = lanes
        if reads is not None:
            self._predict_for_reads = reads
        if include_index_reads is not None:
            self._include_index_reads = include_index_reads
        if force_sample_dir is not None:
            self._force_sample_dir = force_sample_dir


#######################################################################
# Functions
#######################################################################


def samplesheet_index_sequence(line):
    """
    Return the index sequence for a sample sheet line

    Arguments:
      line (TabDataLine): line from a SampleSheet instance

    Returns:
      String: barcode sequence, or 'None' if not defined.

    """
    # Index sequence
    try:
        # Try dual-indexed IEM4 format
        if not line['index2'].strip():
            # Blank index2, raise exception to break
            raise KeyError
        return "%s-%s" % (line['index'].strip(),
                          line['index2'].strip())
    except KeyError:
        pass
    # Try single indexed IEM4 (no index2)
    try:
        if not line['index'].strip():
            # Blank index, raise exception to break
            raise KeyError
        return line['index'].strip()
    except KeyError:
        pass
    # Try CASAVA format
    try:
        indx = line['Index'].strip()
    except KeyError:
        indx = ''
    if not indx:
        indx = None
    return indx
