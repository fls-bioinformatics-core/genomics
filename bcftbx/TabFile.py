#!/usr/bin/env python
#
#     TabFile.py: classes for reading and manipulating tab-delimited data
#     Copyright (C) University of Manchester 2011-2020 Peter Briggs
#
########################################################################
#
# TabFile.py
#
#########################################################################

"""
Legacy module providing classes for working with generic tab-delimited data.

The core functionality has been moved to the ``io.tabular`` module, which
now implements the ``TabFile``, ``TabLine`` and ``TabFileIterator`` classes,
and which are used within this module as a basis for the backwards-compatible
versions:

* ``TabFile``: represents a tab-delimited data file;
* ``TabDataLine``: represents a line of tab-delimited data;
* ``TabFileIterator``: simple iterator for tab-delimited data files.

The classes in this module are now deprecated and should not be used in new
code; they are likely to be removed in a future release.
"""


from .io import tabular
import logging


class TabDataLine(tabular.TabLine):
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

        if not line: print("Blank line")
    
    """
    def __init__(self,line=None,column_names=None,delimiter='\t',lineno=None,
                 convert=True,allow_underscores_in_numeric_literals=False,
                 line_number=None, convert_values=None):
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
          allow_underscores_in_numeric_literals: (optional) if True
            then treat numerical values with underscores as
            numbers according to PEP 15; if False (the default)
            then treat them as strings
        """
        if lineno is not None:
            line_number = lineno
        if convert is not None:
            convert_values = convert
        tabular.TabLine.__init__(self, line, column_names=column_names,
                                 delimiter=delimiter, convert_values=convert, line_number=line_number,
                                 allow_underscores_in_numeric_literals=allow_underscores_in_numeric_literals)

    def appendColumn(self,key,value):
        """Append keyed values to the data line

        This adds a new value along with a header name (i.e. key)
        """
        return self.append_column(key, value)

    def lineno(self):
        """Return the line number associated with the line

        NB The line number is set by the class or function which
        created the TabDataLine object, it is not guaranteed by
        the TabDataLine class itself.
        """
        return self.line_number()


class TabFile(tabular.TabFile):
    """Class to get data from a tab-delimited file

    Loads data from the specified file into a data structure than can
    then be queried on a per line and per item basis.

    Data lines are represented by data line objects which must be
    TabDataLine-like.

    Example usage:

        data = TabFile(myfile)      # load initial data

        print('%s' % len(data))     # report number of lines of data

        print('%s' % data.header()) # report header (i.e. column names)

        for line in data:
            ...                     # loop over lines of data

        myline = data[0]            # fetch first line of data
    """
    def __init__(self,filen=None,fp=None,column_names=None,skip_first_line=False,
                 first_line_is_header=False,tab_data_line=None,
                 delimiter='\t',convert=True,
                 allow_underscores_in_numeric_literals=False,
                 keep_commented_lines=False):
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
          tab_data_line: (optional) ignored (preserved for
              backwards-compatibility only)
          delimiter: (optional) delimiter character (defaults to tab)
          convert: (optional) if True then convert input values to
              the appropriate types (e.g. integer, float etc); if
              False then convert everything to strings
          allow_underscores_in_numeric_literals: (optional) if True
              then treat numerical values with underscores as
              numbers according to PEP 515; if False (the default)
              then treat them as strings
          keep_commented_lines: (optional) if True then don't
              remove commented lines
        """
        if tab_data_line is not None:
            logging.warning("TabFile: specified 'tab_data_line' ignored, "
                            "only TabDataLine is supported")
        tabular.TabFile.__init__(self,filen=filen,fp=fp,column_names=column_names,
                                 skip_first_line=skip_first_line,
                                 first_line_is_header=first_line_is_header,
                                 delimiter=delimiter,
                                 convert_values=convert,
                                 allow_underscores_in_numeric_literals=
                                 allow_underscores_in_numeric_literals,
                                 keep_commented_lines=keep_commented_lines)
    
    def nColumns(self):
        """Return the number of columns in the file

        If the file had a header then this will be the number of
        header columns; otherwise it will be the number of columns
        found in the first line of data
        """
        return self.ncols()

    def indexByLineNumber(self,n):
        """Return index of a data line given the file line number

        Given the line number n for a line in the original file,
        returns the index required to access the data for that
        line in the TabFile object.

        If no matching line is found then raises an IndexError.
        """
        return self.index_by_line_number(n)

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
            line = tabdataline
        elif data:
            line = data
        elif tabdata:
            line = tabdata
        else:
            line = None
        return tabular.TabFile.append(self, line)

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
            line = tabdataline
        elif data:
            line = data
        elif tabdata:
            line = tabdata
        else:
            line = None
        return tabular.TabFile.insert(self, i, line)

    def appendColumn(self,name,fill_value=''):
        """Append a new (empty) column

        Arguments:
          name: name for the new column
          fill_value: optional, value to insert into
            all rows in the new column
        """
        return self.append_column(name, fill_value=fill_value)

    def reorderColumns(self,new_columns):
        """Rearrange the columns in the file

        Arguments:
          new_columns: list of column names or indices in the
            new order

        Returns:
          New TabFile object
        """
        return self.reorder(new_columns)

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
        return self.transform(column_name, transform_func)

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
        return self.compute(column_name, compute_func)

    def _tabline(self, line, line_number=None):
        """
        Internal: wrap data in a TabLine object
        """
        return TabDataLine(line=line,
                           column_names=self._header,
                           delimiter=self._delimiter,
                           convert=self._convert_values,
                           allow_underscores_in_numeric_literals=
                           self._allow_underscores_in_numbers,
                           line_number=line_number)

    def _tabfile(self, *args, **kwargs):
        """
        Internal: return a TabFile object
        """
        return TabFile(*args, **kwargs)


class TabFileIterator(tabular.TabFileIterator):
    """
    Iterate through lines in a tab-delimited file

    Class to loop over all lines in a TSV file, returning a TabDataLine
    object for each record.
    """

    def __init__(self,filen=None,fp=None,column_names=None):
        """
        Create a new TabFileIterator

        The input file should be a tab-delimited text file, specified as
        either a file name (using the 'filen' argument), or a file-like
        object opened for line reading (using the 'fp' argument).

        Each iteration returns a TabDataLine populated with data from
        the file.

        Example usage:

        >>> for line in TabFileIterator(filen='data.tsv'):
        ...   print(line)

        Arguments:
          filen: name of the file to iterate through
          fp: file-like object opened for reading
          column_names: optional list of names to use as
            column headers in the returned TabDataLines

        """
        tabular.TabFileIterator.__init__(self,filen=filen,fp=fp,
                                         column_names=column_names)

    def _tabline(self, line):
        return TabDataLine(line=line,
                           column_names=self._column_names,
                           line_number=self._line_number)