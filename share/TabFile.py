#!/bin/env python
#
#     TabFile.py: classes for reading and manipulating tab-delimited data
#     Copyright (C) University of Manchester 2011 Peter Briggs
#
########################################################################
#
# TabFile.py
#
#########################################################################

"""TabFile

Classes for working with generic tab-delimited data.

The TabFile module provides a TabFile class, which represents a tab-delimited
data file, and a TabDataLine class, which represents a line of data.

Creating a TabFile
==================

TabFile objects can be initialised from existing files:

>>> data = TabFile('data.txt')

or an 'empty' TabFile can be created if no file name is specified.

Lines starting with '#' are ignored.

Accessing Data within a TabFile
===============================

Within a TabFile object each line of data is represented by a TabDataLine
object. Lines of data are referenced using index notation, with the first
line of data being index zero:

>>> line = data[0]
>>> line = data[i]

Note that the index is not the same as the line number from the source file,
(if one was specified) - this can be obtained from the 'lineno' method of
each line:

>>> line_number = line.lineno()

len() gives the total number of lines of data in the TabFile object:

>>> len(data)

It is possible to iterate over the data lines in the object:

>>> for line in data:
>>>    ... do something with line ...

By default columns of data in the file are referenced by index notation, with
the first column being index zero:

>>> line = data[0]
>>> value = line[0]

If column headers are specified then these can also be used to reference
columns of data:

>>> data = TabFile('data.txt',column_names=['ex','why','zed'])
>>> line = data[0]
>>> ex = line['ex']
>>> line['why'] = 3.454

Headers can also be read from the first line of an input file:

>>> data = TabFile('data.txt',first_line_is_header=True)

A list of the column names can be fetched using the 'header' method:

>>> print data.headers()

Use the 'str' built-in to get the line as a tab-delimited string:

>>> str(line)

Adding and Removing Data
========================

New lines can be added to the TabFile object via the 'append' and 'insert'
methods:

>>> data.append()  # No data i.e. empty line
>>> data.append(data=[1,2,3]) # Provide data values as a list
>>> data.append(tabdata='1\t2\t3') # Provide values as tab-delimited string
>>> data.insert(1,data=[5,6,7]) # Inserts line of data at index 1

Type conversion is automatically performed when data values are assigned:

>>> line = data.append(data=['1',2,'3.4','pjb'])
>>> line[0]
1
>>> line[2]
3.4
>>> line[3]
'pjb'

Lines can also be removed using the 'del' built-in:

>>> del(data[0]) # Deletes first data line

New columns can be added using the 'appendColumn' method e.g.:

>>> data.appendColumn('new_col') # Creates a new empty column

Filtering Data
===============

The 'lookup' method returns a set of data lines where a key matches a
specific value:

>>> data = TabFile('data.txt',column_names=['chr','start','end'])
>>> chrom = data.lookup('chr','chrX')

Within a single data line the 'subset' method returns a list of values
for a set of column indices or column names:

>>> data = TabFile(column_names=['chr','start','end','strand'])
>>> data.append(data=['chr1',123456,234567,'+'])
>>> data[0].subset('chr1','start')
['chr1',123456]

Sorting Data
============

The 'sort' method offers a simple way of sorting the data lines within
a TabFile. The simplest example is sorting on a specific column:

>>> data.sort(lambda line: line['start'])

See the method documentation for more detail on using the 'sort' method.

Manipulating Data: whole column operations
==========================================

The 'transformColumn' and 'computeColumn' methods provide a way to
update all the values in a column with a single method call. In each
case the calling subprogram must supply a function object which is
used to update the values in a specific column.

The function supplied to 'transformColumn' must take a single
argument which is the current value of the column in that line. For
example: define a function to increment a supplied value by 1:

>>> def addOne(x):
>>> ...     return x+1

Then use this to add one to all values in the column 'start':

>>> data.transformColumn('start',addOne)

Alternatively a lambda can be used to avoid defining a new function:

>>> data.transformColumn('start',lambda x: x+1)

The function supplied to 'computeColumn' must take a single argument
which is the current line (i.e. a TabDataLine object) and return
a new value for the specified column. For example:

>>> def calculateMidpoint(line):
>>> ...   return (line['start'] + line['stop'])/2.0
>>> data.computeColumn('midpoint',calculateMidpoint)

Again a lambda expression can be used instead:

>>> data.computeColumn('midpoint',lambda line: line['stop'] - line['start'])

Writing to File
===============

Use the TabFile's 'write' method to output the content to a file:

>>> data.write('newfile.txt') # Writes all the data to newfile.txt

It's also possible to reorder the columns before writing out using
the 'reorderColumns' method.
"""

class TabFile:
    """Class to get data from a tab-delimited file

    Loads data from the specified file into a data structure than can
    then be queried on a per line and per item basis.

    Data lines are represented by TabDataLine objects.

    Example usage:

        data = TabFile(myfile)     # load initial data

        print '%s' % len(data)     # report number of lines of data

        print '%s' % data.header() # report header (i.e. column names)

        for line in data:
            ...                    # loop over lines of data

        myline = data[0]           # fetch first line of data
    """
    def __init__(self,filen=None,fp=None,column_names=None,skip_first_line=False,
                 first_line_is_header=False):
        """Create a new TabFile object

        If either of 'filen' or 'fp' arguments are given then the
        TabFile object will be populated with data from the specified
        file or stream. Otherwise an empty TabFile object is created.

        Arguments:
          filen (optional): name of tab-delimited file to load data
              from; ignored if fp is also specified
          fp: (optional) a file-like object which data can be loaded
              from like a file; used in preference to filen
          column_names: (optional) list of column names to assign to
              columns in the file. Overrides column names in the file
          skip_first_line: (optional) if True then ignore the first
              line of the input file
          first_line_is_header: (optional) if True then takes column
              names from the first line of the file (over-riding
              'column_names' argument if specified.
        """
        # Initialise
        self.__filen = filen
        self.__ncols = 0
        self.__header = []
        self.__data = []
        # Set up column names
        if column_names is not None:
            self.__setHeader(column_names)
        # Read in data
        if fp is None and filen is not None:
            # Open named file
            fp = open(self.__filen,'rU')
        if fp:
            self.__load(fp,skip_first_line=skip_first_line,
                        first_line_is_header=first_line_is_header)
            fp.close()

    def __load(self,fp,skip_first_line=False,first_line_is_header=False):
        """Load data into the object from file

        Lines starting with '#' are ignored (unless the first_line_is_header
        is set and the first line starts with '#').

        If a header is set then lines with fewer data items than header
        items raise an IndexError exception.

        Arguments:
          fp: file-like object to read data from
          skip_first_line: (optional) if True then ignore the first
              line of the input file
          first_line_is_header: (optional) if True then take column
              names from the first line of the file
        """
        line_no = 0
        for line in fp:
            line_no += 1
            if skip_first_line:
                # Skip first line
                skip_first_line = False
                continue
            elif first_line_is_header and len(self.header()) == 0:
                # Set up header from first line
                self.__setHeader(line.strip().strip('#').split('\t'))
                first_line_is_header = False
                continue
            if line.lstrip().startswith('#'):
                # Skip commented line
                continue
            # Store data
            data_line = TabDataLine(line,column_names=self.header(),lineno=line_no)
            if self.__ncols > 0:
                if len(data_line) != self.__ncols:
                    # Inconsistent lines are an error
                    raise IndexError, "wrong number of data items in line %d" % line_no
            else:
                # Set number of columns
                self.__ncols = len(data_line)
            self.__data.append(data_line)

    def __setHeader(self,column_names):
        """Set the names for columns of data

        Arguments:
          column_names: a tuple or list with names for each column in order.
        """
        assert(len(self) == 0)
        if len(self.__header) > 0:
            self.__header = []
        for name in column_names:
            self.__header.append(name)
        self.__ncols = len(self.__header)

    def header(self):
        """Return list of column names

        If no column names were set then this will be an empty list.
        """
        return self.__header
    
    def nColumns(self):
        """Return the number of columns in the file

        If the file had a header then this will be the number of
        header columns; otherwise it will be the number of columns
        found in the first line of data
        """
        return self.__ncols

    def filename(self):
        """Return the file name associated with the TabFile
        """
        return self.__filen
    
    def lookup(self,key,value):
        """Return lines where the key matches the specified value
        """
        result = []
        for line in self.__data:
            if line[key] == value:
                result.append(line)
        return result

    def indexByLineNumber(self,n):
        """Return index of a data line given the file line number

        Given the line number n for a line in the original file,
        returns the index required to access the data for that
        line in the TabFile object.

        If no matching line is found then raises an IndexError.
        """
        for idx in range(len(self.__data)):
            if self.__data[idx].lineno() == n:
                return idx
        raise IndexError,"No line number %d" % n

    def append(self,data=None,tabdata=None):
        """Create and append a new data line

        Creates a new TabDataLine and appends it to the end of the
        list of lines.

        Optionally the 'data' or 'tabdata' arguments can specify
        data items which will be used to populate the new line.

        Arguments:
          data: (optional) a list of data items
          tabdata: (optional) a string of tab-delimited data items

        Returns:
          Appended TabDataLine object.
        """
        if data:
            line = '\t'.join([str(x) for x in data])
        elif tabdata:
            line = tabdata
        else:
            line = None
        data_line = TabDataLine(line=line,column_names=self.header())
        self.__data.append(data_line)
        return data_line

    def insert(self,i,data=None,tabdata=None):
        """Create and insert a new data line at a specified index
 
        Creates a new TabDataLine and inserts it into the list of
        lines at the specified index position 'i' (nb NOT a line
        number).

        Optionally the 'data' or 'tabdata' arguments can specify
        data items which will be used to populate the new line.

        Arguments:
          i: index position to insert the line at
          data: (optional) a list of data items
          tabdata: (optional) a string of tab-delimited data items

        Returns:
          New inserted TabDataLine object.
        """
        if data:
            line = '\t'.join([str(x) for x in data])
        elif tabdata:
            line = tabdata
        else:
            line = None
        data_line = TabDataLine(line=line,column_names=self.header())
        self.__data.insert(i,data_line)
        return data_line

    def appendColumn(self,name):
        """Append a new (empty) column

        Arguments:
          name: name for the new column
        """
        for data in self.__data:
            data.appendColumn(name,'')
        self.__header.append(name)
        self.__ncols = len(self.__header)

    def reorderColumns(self,new_columns):
        """Rearrange the columns in the file

        Arguments:
          new_columns: list of column names or indices in the
            new order
        """
        reordered_tabfile = TabFile(column_names=new_columns)
        for data in self.__data:
            reordered_tabfile.append(data.subset(*new_columns))
        return reordered_tabfile

    def transformColumn(self,column_name,transform_func):
        """Apply arbitrary function to a column

        For each line of data the transformation function will be invoked
        with the value of the named column, with the result being written
        back to that column (overwriting the existing value).

        Arguments:
          column_name: name of column to write transformation result to
          transform_func: callable object that will be invoked to perform
            the transformation
        """
        for line in self:
            line[column_name] = transform_func(line[column_name])

    def computeColumn(self,column_name,compute_func):
        """Compute and store values in a new column
    
        For each line of data the computation function will be invoked
        with the line as the sole argument, and the result will be stored in
        a new column with the specified name.

        Arguments:
          column_name: name of column to write transformation result to
          compute_func: callable object that will be invoked to perform
            the computation
        """
        if column_name not in self.header():
            self.appendColumn(column_name)
        for line in self:
            line[column_name] = compute_func(line)

    def sort(self,sort_func,reverse=False):
        """Sort data using arbitrary function

        Performs an in-place sort based on the suppled sort_func.

        sort_func should be a function object which takes a TabDataLine
        object as input and returns a single numerical value; the
        data lines will be sorted in ascending order of these values
        (or descending order if reverse is set to True).

        To sort on the value of a specific column use e.g.
        
        >>> tabfile.sort(lambda line: line['col'])

        Arguments:
          sort_func: function object taking a TabDataLine as input and
            returning a single numerical value
          reverse: (optional) Boolean, either False (default) to sort
            in ascending order, or True to sort in descendin order
        """
        self.__data = sorted(self.__data,key=sort_func,reverse=reverse)

    def write(self,filen,include_header=False):
        """Write the TabFile data to an output file

        Arguments:
          filen: name of file to write to
          include_header: (optional) if set to True, the first
            line will be a 'header' line
        """
        fp = open(filen,'w')
        if include_header:
            fp.write("#%s\n" % '\t'.join(self.header()))
        for data in self.__data:
            fp.write("%s\n" % data)
        fp.close()

    def __getitem__(self,key):
        return self.__data[key]

    def __delitem__(self,key):
        del(self.__data[key])

    def __len__(self):
        return len(self.__data)

class TabDataLine:
    """Class to store a line of data from a tab-delimited file

    Values can be accessed by integer index or by column names (if
    set), e.g.

        line = TabDataLine("1\t2\t3",('first','second','third'))

    allows the 2nd column of data to accessed either via line[1] or
    line['second'].

    Values can also be changed, e.g.

        line['second'] = new_value

    Values are automatically converted to integer or float types as
    appropriate.

    Subsets of data can be created using the 'subset' method.

    Line numbers can also be set by the creating subprogram, and
    queried via the 'lineno' method.
    """
    def __init__(self,line=None,column_names=None,lineno=None):
        """Create a new TabFileLine object

        Arguments:
          line: (optional) Tab-delimited line with data values
          column_names: (optional) tuple or list of column names
            to assign to each value.
          lineno: (optional) Line number
        """
        # Data
        self.data = []
        self.__lineno = None
        if line is not None:
            for value in line.split('\t'):
                self.data.append(self.__convert(value.strip()))
        # Column names
        self.names = []
        if column_names:
            for name in column_names:
                self.names.append(name)
            while len(self.data) < len(column_names):
                self.data.append('')
        # Line number
        if lineno is not None:
            invalid_lineno = False
            try:
                lineno = int(lineno)
                if lineno < 0:
                    # Line number is less than zero
                    invalid_lineno = True
            except TypeError:
                # Can't convert to an integer
                invalid_lineno = True
            if invalid_lineno:
                raise ValueError,"invalid line number '%s'" % lineno
        self.__lineno = lineno

    def __getitem__(self,key):
        """Implement value = TabDataLine[key]

        'key' can be the name of a column or an integer index
        (starting from zero). Column names are checked first.

        WARNING there is potential ambiguity if any column "names"
        also happen to be integers. 
        """
        # See if key is a column name
        try:
            i = self.names.index(key)
            return self.data[i]
        except ValueError:
            # Not a column name
            # See if it's an integer index
            try:
                i = int(key)
            except ValueError:
                # Not an integer
                raise KeyError, "column '%s' not found" % key
            try:
                return self.data[i]
            except IndexError:
                # Integer but out of range
                raise IndexError, "integer index out of range for '%s'" % key

    def __setitem__(self,key,value):
        """Implement TabDataLine[key] = value

        'key' can be the name of a column or an integer index
        (starting from zero). Column names are checked first.

        WARNING there is potential ambiguity if any column "names"
        also happen to be integers. 
        """
        # Convert value to correct type
        converted_value = self.__convert(value)
        # See if key is a column name
        try:
            i = self.names.index(key)
            self.data[i] = converted_value
        except ValueError:
            # Not a column name
            # See if it's an integer index
            try:
                i = int(key)
            except ValueError:
                # Not an integer
                raise KeyError, "column '%s' not found" % key
            try:
                self.data[i] = converted_value
            except IndexError:
                # Integer but out of range
                raise IndexError, "integer index out of range for '%s'" % key

    def __len__(self):
        return len(self.data)

    def __convert(self,value):
        """Internal: convert a value to the correct type

        Used to coerce input values into integers or floats
        if appropriate before storage in the TabDataLine
        object.
        """
        converted = str(value)
        try:
            # Try integer
            converted = int(converted)
        except ValueError:
            # Not an integer, try float
            try:
                converted = float(converted)
            except ValueError:
                # Not a float, leave as input
                pass
        # Return value
        return converted

    def append(self,*values):
        """Append values to the data line

        Should only be used when creating new data lines.
        """
        for value in values:
            self.data.append(self.__convert(value))

    def appendColumn(self,key,value):
        """Append keyed values to the data line

        This adds a new value along with a header name (i.e. key)
        """
        self.names.append(key)
        self.data.append(self.__convert(value))

    def subset(self,*keys):
        """Return a subset of data items

        This method creates a new TabDataLine instance with a
        subset of data specified by the 'keys' argument, e.g.

            new_line = line.subset(2,1)

        returns an instance with only the 2nd and 3rd data values
        in reverse order.

        To access the items in a subset using index notation,
        use the same keys as those specified when the subset was
        created. For example, for

            s = line.subset("two","nine")

        use s["two"] and s["nine"] to access the data; while for

            s = line.subset(2,9)

        use s[2] and s[9].
        
        Arguments:
          keys: one or more keys specifying columns to include in
            the subset. Keys can be column indices, column names,
            or a mixture, and the same column can be referenced
            multiple times.
        """
        subset = TabDataLine()
        for key in keys:
            subset.appendColumn(key,self[key])
        return subset

    def lineno(self):
        """Return the line number associated with the line

        NB The line number is set by the class or function which
        created the TabDataLine object, it is not guaranteed by
        the TabDataLine class itself.
        """
        return self.__lineno

    def __repr__(self):
        return '\t'.join([str(x) for x in self.data])

########################################################################
#
# Tests
#
#########################################################################

import unittest
import cStringIO

class TestTabFile(unittest.TestCase):

    def setUp(self):
        # Make file-like object to read data in
        self.fp = cStringIO.StringIO(
"""#chr\tstart\tend\tdata
chr1\t1\t234\t4.6
chr1\t567\t890\t5.7
chr2\t1234\t5678\t6.8
""")

    def test_load_data(self):
        """Create and load new TabFile instance
        """
        tabfile = TabFile('test',self.fp)
        self.assertEqual(len(tabfile),3,"Input has 3 lines of data")
        self.assertEqual(tabfile.header(),[],"Header should be empty")
        self.assertEqual(str(tabfile[0]),"chr1\t1\t234\t4.6","Incorrect string representation")
        self.assertEqual(tabfile[2][0],'chr2',"Incorrect data")
        self.assertEqual(tabfile.nColumns(),4)
        self.assertEqual(tabfile.filename(),'test')

    def test_load_data_with_header(self):
        """Create and load Tabfile using first line as header
        """
        tabfile = TabFile('test',self.fp,first_line_is_header=True)
        self.assertEqual(len(tabfile),3,"Input has 3 lines of data")
        self.assertEqual(tabfile.header(),['chr','start','end','data'],"Wrong header")
        self.assertEqual(str(tabfile[0]),"chr1\t1\t234\t4.6","Incorrect string representation")
        self.assertEqual(tabfile[2]['chr'],'chr2',"Incorrect data")
        self.assertEqual(tabfile.nColumns(),4)

    def test_load_data_setting_explicit_header(self):
        """Create and load TabFile setting the header explicitly
        """
        tabfile = TabFile('test',self.fp,first_line_is_header=True,
                          column_names=('CHROM','START','STOP','VALUES'))
        self.assertEqual(len(tabfile),3,"Input has 3 lines of data")
        self.assertEqual(tabfile.header(),['CHROM','START','STOP','VALUES'],"Wrong header")
        self.assertEqual(str(tabfile[0]),"chr1\t1\t234\t4.6","Incorrect string representation")
        self.assertEqual(tabfile[2]['CHROM'],'chr2',"Incorrect data")
        self.assertEqual(tabfile.nColumns(),4)

    def test_lookup(self):
        """Look up data from a TabFile
        """
        tabfile = TabFile('test',self.fp,first_line_is_header=True)
        # Look for lines with 'chr1' in the chr column
        matching = tabfile.lookup('chr','chr1')
        self.assertEqual(len(matching),2)
        for m in matching:
            self.assertEqual(m['chr'],'chr1',"Lookup returned bad match: '%s'" % m)
        self.assertNotEqual(matching[0],matching[1])
        # Look for lines with 'chr2' in the chr column
        matching = tabfile.lookup('chr','chr2')
        self.assertEqual(len(matching),1)
        self.assertEqual(matching[0]['chr'],'chr2',"Lookup returned bad match: '%s'" % m)
        # Look for lines with 'bananas' in the chr column
        self.assertEqual(len(tabfile.lookup('chr','bananas')),0)

    def test_get_index_for_line_number(self):
        """Look up line numbers from a TabFile
        """
        tabfile = TabFile('test',self.fp)
        # Look for an existing line
        self.assertEqual(tabfile.indexByLineNumber(2),0)
        self.assertEqual(tabfile[tabfile.indexByLineNumber(2)].lineno(),2)
        # Look for the first line in the file (the commented header)
        self.assertRaises(IndexError,tabfile.indexByLineNumber,1)
        # Look for a generally non-existant line number
        self.assertRaises(IndexError,tabfile.indexByLineNumber,-12)
        # Look for a negative line number
        self.assertRaises(IndexError,tabfile.indexByLineNumber,99)

    def test_insert_empty_line(self):
        """Insert a blank line into a TabFile
        """
        tabfile = TabFile('test',self.fp)
        self.assertEqual(len(tabfile),3)
        line = tabfile.insert(2)
        self.assertEqual(len(tabfile),4)
        # Check new line is empty
        for i in range(len(line)):
            self.assertTrue(str(line[i]) == '')

    def test_insert_line_with_data(self):
        """Insert line into a TabFile populated with data
        """
        data = ['chr1',678,901,6.1]
        tabfile = TabFile('test',self.fp)
        self.assertEqual(len(tabfile),3)
        line = tabfile.insert(2,data=data)
        self.assertEqual(len(tabfile),4)
        # Check new line is correct
        for i in range(len(data)):
            self.assertTrue(line[i] == data[i])

    def test_insert_line_with_tab_data(self):
        """Insert line into a TabFile populated from tabbed data
        """
        data = 'chr1\t10000\t20000\t+'
        tabfile = TabFile('test',self.fp)
        self.assertEqual(len(tabfile),3)
        line = tabfile.insert(2,tabdata=data)
        self.assertEqual(len(tabfile),4)
        # Check new line is correct
        self.assertTrue(str(line) == data)

    def test_append_column(self):
        """Append new column to a Tabfile
        """
        tabfile = TabFile('test',self.fp,first_line_is_header=True)
        self.assertEqual(len(tabfile.header()),4)
        tabfile.appendColumn('new')
        self.assertEqual(len(tabfile.header()),5)
        self.assertEqual(tabfile.header()[4],'new')
        self.assertEqual(tabfile[0]['new'],'')

class TestUncommentedHeaderTabFile(unittest.TestCase):

    def setUp(self):
        # Make file-like object to read data in
        self.fp = cStringIO.StringIO(
"""chr\tstart\tend\tdata
chr1\t1\t234\t4.6
chr1\t567\t890\t5.7
chr2\t1234\t5678\t6.8
""")

    def test_expected_uncommented_header(self):
        """Test reading in a tab file with an expected uncommented header
        """
        tabfile = TabFile('test',self.fp,first_line_is_header=True)
        self.assertEqual(len(tabfile),3,"Input has 3 lines of data")
        self.assertEqual(tabfile.header(),['chr','start','end','data'],"Wrong header")
        self.assertEqual(str(tabfile[0]),"chr1\t1\t234\t4.6","Incorrect string representation")
        self.assertEqual(tabfile[2]['chr'],'chr2',"Incorrect data")
        self.assertEqual(tabfile.nColumns(),4)

    def test_unexpected_uncommented_header(self):
        """Test reading in a tab file with an unexpected uncommented header
        """
        tabfile = TabFile('test',self.fp)
        self.assertEqual(len(tabfile),4,"Input has 4 lines of data")
        self.assertEqual(tabfile.header(),[],"Wrong header")
        self.assertEqual(str(tabfile[0]),"chr\tstart\tend\tdata","Incorrect string representation")
        self.assertRaises(KeyError,tabfile[3].__getitem__,'chr')
        self.assertEqual(tabfile.nColumns(),4)

class TestEmptyTabFile(unittest.TestCase):

    def test_make_empty_tabfile(self):
        """Test creating an empty TabFile with no associated file
        """
        tabfile = TabFile()
        self.assertEqual(len(tabfile),0,"new TabFile should have zero length")

    def test_add_data_to_new_tabfile(self):
        """Test adding data as a list of items to a new empty TabFile
        """
        data = ['chr1',10000,20000,'+']
        tabfile = TabFile()
        tabfile.append(data=data)
        self.assertEqual(len(tabfile),1,"TabFile should now have one line")
        for i in range(len(data)):
            self.assertEqual(tabfile[0][i],data[i])

    def test_add_tab_data_to_new_tabfile(self):
        """Test adding data as a tab-delimited line to a new empty TabFile
        """
        data = 'chr1\t10000\t20000\t+'
        tabfile = TabFile()
        tabfile.append(tabdata=data)
        self.assertEqual(len(tabfile),1,"TabFile should now have one line")
        self.assertEqual(str(tabfile[0]),data)
        
class TestBadTabFile(unittest.TestCase):
    """Test with 'bad' input files
    """

    def setUp(self):
        # Make file-like object with "bad" data 
        self.fp = cStringIO.StringIO(
"""#chr\tstart\tend\tdata
chr1\t1\t234
chr1\t567\t890\t5.7\t4.6
chr2\t1234\t5678\t6.8
""")
    
    def test_ragged_input_file(self):
        """Deal with mismatched numbers of items on different lines
        """
        self.assertRaises(IndexError,TabFile,'test',self.fp,first_line_is_header=True)
    
    def test_ragged_input_file_no_header(self):
        """Deal with mismatched numbers of items on different lines
        """
        self.assertRaises(IndexError,TabFile,'test',self.fp)

class TestReorderTabFile(unittest.TestCase):
    """Test reordering of columns in TabFiles
    """
    def setUp(self):
        # Make file-like object to read data in
        self.fp = cStringIO.StringIO(
"""#chr\tstart\tend\tdata
chr1\t1\t234\t4.6
chr1\t567\t890\t5.7
chr2\t1234\t5678\t6.8
""")

    def test_reorder_columns(self):
        """Reorder columns in a TabFile
        """
        tabfile = TabFile('test',self.fp,first_line_is_header=True)
        # Check number of columns and header items
        self.assertEqual(tabfile.nColumns(),4)
        self.assertEqual(tabfile.header(),['chr','start','end','data'])
        # Reorder
        new_columns = ['chr','data','start','end']
        tabfile = tabfile.reorderColumns(new_columns)
        self.assertEqual(tabfile.nColumns(),4)
        self.assertEqual(tabfile.header(),new_columns)
        self.assertEqual(str(tabfile[0]),"chr1\t4.6\t1\t234")
        self.assertEqual(str(tabfile[1]),"chr1\t5.7\t567\t890")
        self.assertEqual(str(tabfile[2]),"chr2\t6.8\t1234\t5678")

    def test_reorder_columns_empty_cells(self):
        """Reorder columns where some lines have empty cells at the start
        """
        tabfile = TabFile('test',self.fp,first_line_is_header=True)
        # Check number of columns and header items
        self.assertEqual(tabfile.nColumns(),4)
        self.assertEqual(tabfile.header(),['chr','start','end','data'])
        # Reset some cells to empty
        tabfile[0]['chr'] = ''
        tabfile[2]['chr'] = ''
        # Reorder
        new_columns = ['chr','data','start','end']
        tabfile = tabfile.reorderColumns(new_columns)
        self.assertEqual(tabfile.nColumns(),4)
        self.assertEqual(tabfile.header(),new_columns)
        self.assertEqual(str(tabfile[0]),"\t4.6\t1\t234")
        self.assertEqual(str(tabfile[1]),"chr1\t5.7\t567\t890")
        self.assertEqual(str(tabfile[2]),"\t6.8\t1234\t5678")

class TestWholeColumnOperations(unittest.TestCase):
    """Test the transformColumn and computeColumn methods
    """

    def setUp(self):
        # Make file-like object to read data in
        self.fp = cStringIO.StringIO(
"""#chr\tstart\tend\tdata
chr1\t1\t234\t4.6
chr1\t567\t890\t5.7
chr2\t1234\t5678\t6.8
""")

    def test_set_column_to_constant_value(self):
        """Set a column to a constant value using transformColumn
        """
        tabfile = TabFile('test',self.fp,first_line_is_header=True)
        # Check number of columns and header items
        self.assertEqual(tabfile.nColumns(),4)
        self.assertEqual(tabfile.header(),['chr','start','end','data'])
        # Add a strand column
        tabfile.appendColumn('strand')
        self.assertEqual(tabfile.nColumns(),5)
        self.assertEqual(tabfile.header(),['chr','start','end','data','strand'])
        # Set all values to '+'
        tabfile.transformColumn('strand',lambda x: '+')
        for line in tabfile:
            self.assertEqual(line['strand'],'+')

    def test_apply_operation_to_column(self):
        """Divide values in a column by 10
        """
        tabfile = TabFile('test',self.fp,first_line_is_header=True)
        # Check number of columns and header items
        self.assertEqual(tabfile.nColumns(),4)
        self.assertEqual(tabfile.header(),['chr','start','end','data'])
        # Divide data column by 10
        tabfile.transformColumn('data',lambda x: x/10)
        results = [0.46,0.57,0.68]
        for i in range(len(tabfile)):
            self.assertEqual(tabfile[i]['data'],results[i])

    def test_compute_midpoint(self):
        """Compute the midpoint of the start and end columns
        """
        tabfile = TabFile('test',self.fp,first_line_is_header=True)
        # Check number of columns and header items
        self.assertEqual(tabfile.nColumns(),4)
        self.assertEqual(tabfile.header(),['chr','start','end','data'])
        # Compute midpoint of start and end
        tabfile.computeColumn('midpoint',lambda line: (line['end'] + line['start'])/2.0)
        self.assertEqual(tabfile.nColumns(),5)
        self.assertEqual(tabfile.header(),['chr','start','end','data','midpoint'])
        results = [117.5,728.5,3456]
        for i in range(len(tabfile)):
            self.assertEqual(tabfile[i]['midpoint'],results[i])
        
    def test_compute_and_overwrite_existing_column(self):
        """Compute new values for an existing column
        """
        tabfile = TabFile('test',self.fp,first_line_is_header=True)
        # Check number of columns and header items
        self.assertEqual(tabfile.nColumns(),4)
        self.assertEqual(tabfile.header(),['chr','start','end','data'])
        # Compute new values for data column
        tabfile.computeColumn('data',lambda line: line['end'] - line['start'])
        self.assertEqual(tabfile.nColumns(),4)
        self.assertEqual(tabfile.header(),['chr','start','end','data'])
        results = [233,323,4444]
        for i in range(len(tabfile)):
            self.assertEqual(tabfile[i]['data'],results[i])

class TestSortTabFile(unittest.TestCase):

    def setUp(self):
        # Make file-like object to read data in
        self.fp = cStringIO.StringIO(
"""#chr\tstart\tend\tdata
chr1\t567\t890\t5.7
chr1\t1\t234\t6.8
chr2\t1234\t5678\t3.4
""")

    def test_sort_on_column(self):
        """Sort data on a numerical column into (default) ascending order
        """
        tabfile = TabFile('test',self.fp,first_line_is_header=True)
        tabfile.sort(lambda line: line['data'])
        sorted_data = [3.4,5.7,6.8]
        for i in range(len(tabfile)):
            self.assertEqual(tabfile[i]['data'],sorted_data[i])

    def test_reverse_sort_on_column(self):
        """Sort data on a numerical column into (reverse) descending order
        """
        tabfile = TabFile('test',self.fp,first_line_is_header=True)
        tabfile.sort(lambda line: line['data'],reverse=True)
        sorted_data = [6.8,5.7,3.4]
        for i in range(len(tabfile)):
            self.assertEqual(tabfile[i]['data'],sorted_data[i])
        
class TestTabDataLine(unittest.TestCase):

    def test_new_line_no_data(self):
        """Create new data line with no data
        """
        line = TabDataLine()
        self.assertEqual(len(line),0,"Line should have zero length")
        self.assertEqual(str(line),"","String representation should be empty string")
        self.assertEqual(line.lineno(),None,"Line number should not be set")

    def test_new_line_header_no_data(self):
        """Create new data line with header but no data
        """
        line = TabDataLine(column_names=('one','two','three','four'))
        self.assertEqual(len(line),4,"Line should have 4 items")
        self.assertEqual(str(line),"\t\t\t","String representation should be 3 tabs")
        self.assertEqual(line.lineno(),None,"Line number should not be set")

    def test_new_line_data_no_header(self):
        """Create new data line with data but no header
        """
        input_data = "1.1\t2.2\t3.3\t4.4"
        line = TabDataLine(line=input_data)
        self.assertEqual(len(line),4,"Line should have 4 items")
        self.assertEqual(str(line),input_data)

    def test_new_line_no_header_empty_items(self):
        """Create new data line with no header and a line with empty items
        """
        input_data = "\t\t\t"
        line = TabDataLine(line=input_data)
        self.assertEqual(len(line),4,"Line should have 4 items")
        self.assertEqual(str(line),input_data,"String representation should match input")

    def test_new_line_no_header_leading_empty_item(self):
        """Create new data line with no header and a line with a leading empty item
        """
        input_data = "\t1.2\t3.4\t5.6"
        line = TabDataLine(line=input_data)
        self.assertEqual(len(line),4,"Line should have 4 items")
        self.assertEqual(str(line),input_data,"String representation should match input")

    def test_get_and_set_data(self):
        """Create new data line and do get and set operations
        """
        input_data = "1.1\t2.2\t3.3\t4.4"
        line = TabDataLine(line=input_data,column_names=('one','two','three','four'))
        self.assertEqual(len(line),4,"Line should have 4 items")
        self.assertEqual(str(line),input_data,"String representation should be same as input")
        # Test getting
        self.assertEqual(line[1],2.2,"Column 2 data is incorrect")
        self.assertEqual(line["two"],2.2,"Column 2 data is incorrect")
        # Test setting
        line["two"] = 4.4
        self.assertEqual(line[1],4.4,"Column 2 data is incorrect after set operation")
        self.assertEqual(line["two"],4.4,"Column 2 data is incorrect after set operation")
        
    def test_subsetting(self):
        """Create new data line and retrieve subset
        """
        input_data = "1.1\t2.2\t3.3\t4.4"
        line = TabDataLine(line=input_data,column_names=('one','two','three','four'))
        # Subset with integer indices
        subset = line.subset(2,3)
        self.assertEqual(len(subset),2,"Subset should have 2 items")
        self.assertEqual(str(subset),"3.3\t4.4","String representation should be last two columns")
        # Subset with keys
        subset = line.subset("three","four")
        self.assertEqual(len(subset),2,"Subset should have 2 items")
        self.assertEqual(str(subset),"3.3\t4.4","String representation should be last two columns")
        # Check key lookup still works
        self.assertEqual(subset["three"],3.3)

    def test_subsetting_no_header(self):
        """Create new data line with no header and retrieve subset
        """
        input_data = "1.1\t2.2\t3.3\t4.4"
        line = TabDataLine(line=input_data)
        # Subset with integer indices
        subset = line.subset(2,3)
        self.assertEqual(len(subset),2,"Subset should have 2 items")
        self.assertEqual(str(subset),"3.3\t4.4","String representation should be last two columns")
        # Check key lookup
        self.assertEqual(subset[2],3.3)

    def test_subsetting_leading_empty_items(self):
        """Create new data line with a leading empty items and retrieve subset
        """
        input_data = "\t2.2\t3.3\t4.4"
        line = TabDataLine(line=input_data,column_names=('one','two','three','four'))
        # Subset with integer indices
        subset = line.subset(2,3)
        self.assertEqual(len(subset),2,"Subset should have 2 items")
        self.assertEqual(str(subset),"3.3\t4.4","String representation should be last two columns")
        # Subset with keys
        subset = line.subset("three","four")
        self.assertEqual(len(subset),2,"Subset should have 2 items")
        self.assertEqual(str(subset),"3.3\t4.4","String representation should be last two columns")

    def test_line_number(self):
        """Create new data line with line number
        """
        line = TabDataLine(line="test",lineno=3)
        self.assertEqual(line.lineno(),3,"Line number should be three")

    def test_invalid_line_numbers(self):
        """Attempt to create new data lines with invalid line numbers
        """
        self.assertRaises(ValueError,TabDataLine,lineno=-3)
        self.assertRaises(ValueError,TabDataLine,lineno="three")

    def test_iteration_over_items(self):
        """Iterate over the data items in a data line
        """
        input_data = "1.1\t2.2\t3.3\t4.4"
        line = TabDataLine(line=input_data)
        try:
            # This should work
            for item in line:
                pass
        except Exception,ex:
            # It hasn't worked
            self.fail("Iteration test exception: '%s'" % ex)

class TestTabDataLineTypeConversion(unittest.TestCase):

    def test_convert_integers(self):
        """Load string data which should be converted to integers
        """
        test_values = [12,34,56]
        input_data = '\t'.join([str(x) for x in test_values])
        line = TabDataLine(line=input_data)
        for i in range(len(test_values)):
            self.assertEqual(line[i],test_values[i])

    def test_convert_floats(self):
        """Load string data which should be converted to floats
        """
        test_values = [1.2,3.4,5.6]
        input_data = '\t'.join([str(x) for x in test_values])
        line = TabDataLine(line=input_data)
        for i in range(len(test_values)):
            self.assertEqual(line[i],test_values[i])

    def test_convert_append_items(self):
        """Append items as strings and check type conversions
        """
        test_values = ['chr1',2,3.4]
        line = TabDataLine()
        for value in test_values:
            line.append(str(value))
        for i in range(len(test_values)):
            self.assertEqual(line[i],test_values[i])

    def test_convert_set_items(self):
        """Set items as strings and check type conversions
        """
        test_values = ['chr1',2,3.4]
        line = TabDataLine(line="x\ty\tz")
        for i in range(len(test_values)):
            line[i] = str(test_values[i])
        for i in range(len(test_values)):
            self.assertEqual(line[i],test_values[i])
        
########################################################################
#
# Main: test runner
#
#########################################################################
if __name__ == "__main__":
    # Run tests
    unittest.main()
