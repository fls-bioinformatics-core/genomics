#!/usr/bin/env python
#
#     TabFile.py: classes for reading and manipulating tab-delimited data
#     Copyright (C) University of Manchester 2011-2012 Peter Briggs
#
########################################################################
#
# TabFile.py
#
#########################################################################

"""
Classes for working with generic tab-delimited data.

The TabFile module provides a TabFile class, which represents a tab-delimited
data file, and a TabDataLine class, which represents a line of data.

Creating a TabFile
------------------

TabFile objects can be initialised from existing files:

>>> data = TabFile('data.txt')

or an 'empty' TabFile can be created if no file name is specified.

Lines starting with '#' are ignored.

Accessing Data within a TabFile
-------------------------------

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
------------------------

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
--------------

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
------------

The 'sort' method offers a simple way of sorting the data lines within
a TabFile. The simplest example is sorting on a specific column:

>>> data.sort(lambda line: line['start'])

See the method documentation for more detail on using the 'sort' method.

Manipulating Data: whole column operations
------------------------------------------

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
---------------

Use the TabFile's 'write' method to output the content to a file:

>>> data.write('newfile.txt') # Writes all the data to newfile.txt

It's also possible to reorder the columns before writing out using
the 'reorderColumns' method.

Specifying Delimiters
---------------------

It's possible to use a different field delimiter than tabs, by explicitly
specifying the value of the 'delimiter' argument when creating a new
TabFile object, for example for a comma-delimited file:

>>> data = TabFile('data.txt',delimiter=',')

"""

__version__ = "0.2.8"

import logging

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

    It is possible to use a different field delimiter than tabs, by
    explicitly specifying the value of the 'delimiter' argument,
    e.g. for a comma-delimited line:

        line = TabDataLine("1,2,3",delimiter=',')

    Check if a line is empty:

        if not line: print "Blank line"
    
    """
    def __init__(self,line=None,column_names=None,delimiter='\t',lineno=None,
                 convert=True):
        """Create a new TabFileLine object

        Arguments:
          line: (optional) Tab-delimited line with data values
          column_names: (optional) tuple or list of column names
            to assign to each value.
          delimiter: (optional) delimiter character (defaults to tab)
          lineno: (optional) Line number
          convert: if True then convert values to the appropriate
            types; if False then all values will be converted to
            strings.
        """
        # Conversion function
        if convert:
            self.__convert = self.convert_to_type
        else:
            self.__convert = self.convert_to_str
        # Data
        self.data = []
        self.delimiter(delimiter)
        self.__lineno = None
        if line is not None:
            for value in line.split(self.__delimiter):
                self.data.append(self.__convert(value.rstrip('\n')))
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

    def __nonzero__(self):
        for item in self.data:
            if str(item).strip(): return True
        return False

    def convert_to_str(self,value):
        """Convert value to string

        """
        return str(value)

    def convert_to_type(self,value):
        """Internal: convert a value to the correct type

        Used to coerce input values into integers or floats
        if appropriate before storage in the TabDataLine
        object.
        """
        converted = value
        try:
            # Try integer
            converted = int(str(converted))
        except ValueError:
            # Not an integer, try float
            try:
                converted = float(str(converted))
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

    def delimiter(self,new_delimiter=None):
        """Set and get the delimiter for the line

        If 'new_delimiter' is not None then the field delimiter
        for the line will be updated to the supplied value. This
        affects how lines are represented via the __repr__
        built-in.

        Returns the current value of the delimiter.
        """
        if new_delimiter is not None:
            self.__delimiter = str(new_delimiter)
        return self.__delimiter

    def lineno(self):
        """Return the line number associated with the line

        NB The line number is set by the class or function which
        created the TabDataLine object, it is not guaranteed by
        the TabDataLine class itself.
        """
        return self.__lineno

    def __repr__(self):
        return self.__delimiter.join([str(x) for x in self.data])

class TabFile:
    """Class to get data from a tab-delimited file

    Loads data from the specified file into a data structure than can
    then be queried on a per line and per item basis.

    Data lines are represented by data line objects which must be
    TabDataLine-like.

    Example usage:

        data = TabFile(myfile)     # load initial data

        print '%s' % len(data)     # report number of lines of data

        print '%s' % data.header() # report header (i.e. column names)

        for line in data:
            ...                    # loop over lines of data

        myline = data[0]           # fetch first line of data
    """
    def __init__(self,filen=None,fp=None,column_names=None,skip_first_line=False,
                 first_line_is_header=False,tab_data_line=TabDataLine,
                 delimiter='\t',convert=True):
        """Create a new TabFile object

        If either of 'filen' or 'fp' arguments are given then the
        TabFile object will be populated with data from the specified
        file or stream. Otherwise an empty TabFile object is created.

        Arguments:
          filen (optional): name of tab-delimited file to load data
              from; ignored if fp is also specified
          fp: (optional) a file-like object which data can be loaded
              from like a file; used in preference to filen.
              Note that the calling program must close the stream in
              these cases.
          column_names: (optional) list of column names to assign to
              columns in the file. Overrides column names in the file
          skip_first_line: (optional) if True then ignore the first
              line of the input file
          first_line_is_header: (optional) if True then takes column
              names from the first line of the file (over-riding
              'column_names' argument if specified.
          tab_data_line: (optional) class to use for creating data
              line objects (defaults to TabDataLine).
          delimiter: (optional) delimiter character (defaults to tab)
          convert: (optional) if True then convert input values to
              the appropriate types (e.g. integer, float etc); if
              False then convert everything to strings
        """
        # Initialise
        self.__filen = filen
        self.__ncols = 0
        self.__header = []
        self.__delimiter = delimiter
        self.__data = []
        self.__convert = convert
        # Class to use for data lines
        self.__tabdataline = tab_data_line
        # Set up column names
        if column_names is not None:
            self.__setHeader(column_names)
        # Read in data
        if fp is None and filen is not None:
            # Open named file
            fp = open(self.__filen,'rU')
            close_fp = True
        else:
            close_fp = False
        if fp:
            self.__load(fp,skip_first_line=skip_first_line,
                        first_line_is_header=first_line_is_header)
        # Only close the stream if it was opened locally
        if close_fp: fp.close()

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
                self.__setHeader(line.strip().strip('#').split(self.__delimiter))
                first_line_is_header = False
                continue
            if line.lstrip().startswith('#'):
                # Skip commented line
                continue
            # Store data
            data_line = self.__tabdataline(line,column_names=self.header(),lineno=line_no,
                                           delimiter=self.__delimiter,
                                           convert=self.__convert)
            if self.__ncols > 0:
                if len(data_line) != self.__ncols:
                    # Inconsistent lines are an error
                    logging.error("Line %d has wrong number of data items" % line_no)
                    logging.error("Line: %s" % data_line)
                    logging.error("Expected %d, got %d" % (self.__ncols,len(data_line)))
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

    def append(self,data=None,tabdata=None,tabdataline=None):
        """Create and append a new data line

        Creates a new data line object and appends it to the end of
        the list of lines.

        Optionally the 'data' or 'tabdata' arguments can specify
        data items which will be used to populate the new line;
        alternatively 'tabdataline' can provide a TabDataLine-based
        object to be appended.

        If none of these are specified then a default blank
        TabDataLine-based object is created, appended and returned.

        Arguments:
          data: (optional) a list of data items
          tabdata: (optional) a string of tab-delimited data items
          tabdataline: (optional) a TabDataLine-based object

        Returns:
          Appended data line object.
        """
        if tabdataline:
            self.__data.append(tabdataline)
            return tabdataline
        if data:
            line = self.__delimiter.join([str(x) for x in data])
        elif tabdata:
            line = tabdata
        else:
            line = None
        data_line = self.__tabdataline(line=line,column_names=self.header(),
                                       delimiter=self.__delimiter,
                                       convert=self.__convert)
        self.__data.append(data_line)
        return data_line

    def insert(self,i,data=None,tabdata=None,tabdataline=None):
        """Create and insert a new data line at a specified index
 
        Creates a new data line object and inserts it into the list
        of lines at the specified index position 'i' (nb NOT a line
        number).

        Optionally the 'data' or 'tabdata' arguments can specify
        data items which will be used to populate the new line;
        alternatively 'tabdataline' can provide a TabDataLine-based
        object to be inserted.

        Arguments:
          i: index position to insert the line at
          data: (optional) a list of data items
          tabdata: (optional) a string of tab-delimited data items
          tabdataline: (optional) a TabDataLine-based object

        Returns:
          New inserted data line object.
        """
        if tabdataline:
            self.__data.insert(i,tabdataline)
            return tabdataline
        if data:
            line = '\t'.join([str(x) for x in data])
        elif tabdata:
            line = tabdata
        else:
            line = None
        data_line = self.__tabdataline(line=line,column_names=self.header())
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

        Returns:
          New TabFile object
        """
        reordered_tabfile = TabFile(column_names=new_columns,
                                    delimiter=self.__delimiter)
        for data in self.__data:
            reordered_tabfile.append(data.subset(*new_columns))
        return reordered_tabfile

    def transpose(self):
        """Transpose the contents of the file

        Returns:
          New TabFile object
        """
        transposed_tabfile = TabFile(delimiter=self.__delimiter)
        first_column = True
        for data in self.__data:
            transposed_tabfile.appendColumn(None)
            for i in range(len(data)):
                try:
                    transposed_tabfile[i][-1] = data[i]
                except IndexError:
                    transposed_tabfile.append()
                    transposed_tabfile[i][-1] = data[i]
        return transposed_tabfile

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
          column_name: name or index of column to write transformation
             result to
          compute_func: callable object that will be invoked to perform
            the computation
        """
        if column_name not in self.header():
            try:
                # Check to see if it's actually an integer index
                column_name = int(column_name)
            except ValueError:
                # Neither existing column name nor integer index
                self.appendColumn(column_name)
        for line in self:
            line[column_name] = compute_func(line)

    def sort(self,sort_func,reverse=False):
        """Sort data using arbitrary function

        Performs an in-place sort based on the suppled sort_func.

        sort_func should be a function object which takes a data line
        object as input and returns a single numerical value; the data
        lines will be sorted in ascending order of these values (or
        descending order if reverse is set to True).

        To sort on the value of a specific column use e.g.
        
        >>> tabfile.sort(lambda line: line['col'])

        Arguments:
          sort_func: function object taking a data line object as
            input and returning a single numerical value
          reverse: (optional) Boolean, either False (default) to sort
            in ascending order, or True to sort in descending order
        """
        self.__data = sorted(self.__data,key=sort_func,reverse=reverse)

    def write(self,filen=None,fp=None,include_header=False,no_hash=False,
              delimiter=None):
        """Write the TabFile data to an output file

        One of either the 'filen' or 'fp' arguments must be given,
        specifying the file name or stream to write the TabFile data to.

        Arguments:
          filen: (optional) name of file to write to; ignored if fp is
            also specified
          fp: (optional) a file-like object opened for writing; used in
            preference to filen if set to a non-null value
              Note that the calling program must close the stream in
              these cases.
          include_header: (optional) if set to True, the first
            line will be a 'header' line
          no_hash: (optional) if set to True and include_header is
            also True then don't put a hash character '#' at the
            start of the header line in the output file.
          delimiter: (optional) delimiter to use when writing data values
            to file (defaults to the delimiter specified on input)
        """
        if fp is None and filen is not None:
            # Open named file for writing
            fp = open(filen,'w')
            close_fp = True
        else:
            close_fp = False
        if include_header:
            if not no_hash:
                leading_hash = '#'
            else:
                leading_hash = ''
            if delimiter is None:
                delim = self.__delimiter
            else:
                delim = str(delimiter)
            fp.write("%s%s\n" % (leading_hash,delim.join(self.header())))
        # Update line delimiters for output if necessary
        if delimiter is not None and delimiter != self.__delimiter:
            for data in self.__data: data.delimiter(delimiter)
        # Write the data
        for data in self.__data:
            fp.write("%s\n" % data)
        # Reset line delimiters        
        if delimiter is not None and delimiter != self.__delimiter:
            for data in self.__data: data.delimiter(self.__delimiter)
        # Only close the stream if it was opened locally
        if close_fp: fp.close()

    def __getitem__(self,key):
        return self.__data[key]

    def __delitem__(self,key):
        del(self.__data[key])

    def __len__(self):
        return len(self.__data)

    def __repr__(self):
        return '\n'.join([str(x) for x in self.__data])
