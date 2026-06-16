#!/usr/bin/env python3
#
#     tabular.py: classes for reading and manipulating tab-delimited data
#     Copyright (C) University of Manchester 2026 Peter Briggs
#


"""
The TabFile module provides a TabFile class, which represents a tab-delimited
data file, a TabLine class, which represents a line of tabular data, and a
TabFileIterator class, which provides a lightweight interface to iterate through
tab-delimiter data files.

It can also be used to interact with files (such as CSV) by creating TabFile
instances with an appropriate delimiter (for example, a comma).

Creating a TabFile
------------------

TabFile objects can be initialised from existing files:

>>> data = TabFile("data.txt")

or an 'empty' TabFile can be created if no file name is specified.

Lines starting with '#' are ignored.

Accessing Data within a TabFile
-------------------------------

Within a TabFile object each line of data is represented by a TabLine
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

>>> data = TabFile("data.txt", column_names=["ex", "why", "zed"])
>>> line = data[0]
>>> ex = line["ex"]
>>> line["why"] = 3.454

Headers can also be read from the first line of an input file:

>>> data = TabFile("data.txt", first_line_is_header=True)

A list of the column names can be fetched using the 'header' method:

>>> print(data.header())

Use the 'str' built-in to get the line as a tab-delimited string:

>>> str(line)

Adding and Removing Data
------------------------

New lines can be added to the TabFile object via the 'append' and 'insert'
methods:

>>> data.append()  # No data i.e. empty line
>>> data.append([1,2,3]) # Provide data values as a list
>>> data.append("1\t2\t3") # Provide values as tab-delimited string
>>> data.insert(1, [5,6,7]) # Inserts line of data at index 1

Type conversion is automatically performed when data values are assigned:

>>> line = data.append(["1", "2", "3.4", "pjb"])
>>> line[0]
1
>>> line[2]
3.4
>>> line[3]
'pjb'

Lines can also be removed using the 'del' built-in:

>>> del(data[0]) # Deletes first data line

New columns can be added using the 'append_column' method:

>>> data.append_column("new_col") # Creates a new empty column

Filtering Data
--------------

The 'lookup' method returns a set of data lines where a key matches a
specific value:

>>> data = TabFile("data.txt", column_names=["chr", "start", "end"])
>>> chrom = data.lookup("chr", "chrX")

Within a single data line the 'subset' method returns a list of values
for a set of column indices or column names:

>>> data = TabFile(column_names=["chr", "start", "end", "strand"])
>>> data.append(["chr1", 123456, 234567, "+"])
>>> data[0].subset("chr1", "start")
['chr1', 123456]

Sorting Data
------------

The 'sort' method offers a simple way of sorting the data lines within
a TabFile. The simplest example is sorting on a specific column:

>>> data.sort(lambda line: line['start'])

See the method documentation for more detail on using the 'sort' method.

Manipulating Data: whole column operations
------------------------------------------

The 'transform' and 'compute' methods provide a way to
update all the values in a column with a single method call. In each
case the calling subprogram must supply a function object which is
used to update the values in a specific column.

The function supplied to 'transform' must take a single
argument which is the current value of the column in that line. For
example to increment all values in column "start" by 1:

>>> data.transform("start", lambda x: x+1)

The function supplied to 'compute' must take a single argument
which is the current line (i.e. a TabLine object) and return
a new value for the specified column. For example:

>>> data.compute('midpoint', lambda line: (line['stop'] - line['start'])/2.0)

Writing to File
---------------

Use the TabFile's 'write' method to output the content to a file:

>>> data.write('newfile.txt') # Writes all the data to newfile.txt

It's also possible to reorder the columns before writing out using
the 'reorder' method.

Specifying Delimiters
---------------------

It's possible to use a different field delimiter than tabs, by explicitly
specifying the value of the 'delimiter' argument when creating a new
TabFile object, for example for a comma-delimited file:

>>> data = TabFile("data.txt", delimiter=',')

TabFileIterator: iterating through a tab-delimited file
-------------------------------------------------------

The ``TabFileIterator`` provides a light-weight alternative to
``TabFile`` in situations where it is only necessary to iterate
through each line in a tab-delimited file:

>>> for line in TabFileIterator(filen="data.tsv"):
...   print(line)

Each line is returned as a ``TabLine`` instance, so the
methods available that class can be used on the data.
"""


from collections.abc import Iterator
import logging

# Module specific logger
logger = logging.getLogger(__name__)


class TabFile:
    """
    Class to get data from a tab-delimited file

    Loads data from the specified file into a data structure than can
    then be queried on a per line and per item basis.

    Data lines are represented by data line objects which must be
    TabDataLine-like.

    Example usage:

    >>> data = TabFile(myfile)      # load initial data
    >>> print('%s' % len(data))     # report number of lines of data
    >>> print('%s' % data.header()) # report header (i.e. column names)
    >>> for line in data:           # loop over lines of data
    ...
    >>> myline = data[0]            # fetch first line of data

    If either of 'filen' or 'fp' arguments are given then the
    TabFile object will be populated with data from the specified
    file or stream. Otherwise an empty TabFile object is created.

    Arguments:
        filen (str): name of tab-delimited file to load data
            from; ignored if fp is also specified
        fp (File): a file-like object which data can be loaded
            from like a file; used in preference to filen.
            Note that the calling program must close the stream in
            these cases.
        column_names (list): (optional) list of column names to
            assign to columns in the file. Overrides column names
             in the file
        skip_first_line (bool): (optional) if True then ignore the
            first line of the input file
        first_line_is_header (bool): (optional) if True then takes
            column names from the first line of the file
            (over-riding 'column_names' argument if specified)
        delimiter (str): (optional) delimiter character (defaults to
            tab)
        convert_values (bool): (optional) if True then convert input
            values to the appropriate types (e.g. integer, float etc);
            if False then convert everything to strings
        allow_underscores_in_numeric_literals (bool): (optional) if
            True then treat numerical values with underscores as
            numbers according to PEP 515; if False (the default)
            then treat them as strings
        keep_commented_lines (bool): (optional) if True then don't
            remove commented lines
    """
    def __init__(self, filen=None, fp=None, column_names=None, skip_first_line=False,
                 first_line_is_header=False, delimiter='\t', convert_values=True,
                 allow_underscores_in_numeric_literals=False, keep_commented_lines=False):
        # Initialise
        self._filen = filen
        self._ncols = 0
        self._header = []
        self._delimiter = delimiter
        self._data = []
        self._convert_values = bool(convert_values)
        self._allow_underscores_in_numbers = bool(allow_underscores_in_numeric_literals)
        self._keep_commented_lines = bool(keep_commented_lines)
        # Set up column names
        if column_names:
            self._set_header(column_names)
        # Read in data
        close_fp = False
        try:
            if fp is None and filen is not None:
                # Open named file
                fp = open(self._filen, "rt")
                close_fp = True
            if fp:
                self._load(fp,
                           skip_first_line=bool(skip_first_line),
                           first_line_is_header=bool(first_line_is_header))
        finally:
            # Only close the stream if it was opened locally
            if close_fp:
                fp.close()

    def filename(self):
        """
        Return the filename of the tab-delimited file.
        """
        return self._filen

    def header(self):
        """
        Return list of column names

        If no column names were set then this will be an empty list.
        """
        return [h for h in self._header]

    def ncols(self):
        """
        Return the number of columns in the file

        If the file had a header then this will be the number of
        header columns; otherwise it will be the number of columns
        found in the first line of data
        """
        return self._ncols

    def lookup(self, key, value):
        """
        Return lines where the key matches the specified value

        Arguments:
            key (str): column name or index
            value (str): value to match

        Returns:
            List: list of matching TabLine objects.
        """
        result = []
        for line in self._data:
            if line[key] == value:
                result.append(line)
        return result

    def index_by_line_number(self, line_number):
        """
        Return index of a data line given the file line number

        Given the line number for a line in the original file,
        returns the index required to access the data for that
        line in the TabFile object.

        If no matching line is found then raises an IndexError.
        """
        for idx in range(len(self._data)):
            if self._data[idx].line_number() == line_number:
                return idx
        raise IndexError(f"No line number '{line_number}")

    def insert(self, idx, line=None):
        """
        Create and insert a new data line at a specified index

        Creates a new data line object and inserts it into the list
        of lines at the specified index position 'idx' (nb NOT a
        line number from the file).

        Optionally if the 'line' argument is specified then it
        should contain data items which will be used to populate the
        inserted line; 'line' can be a "raw" string of delimited
        values, a list, or a TabLine object.

        Arguments:
            idx (int): index position to insert the line at
            line (object): (optional) a list of data items

        Returns:
            TabLine: the new inserted TabLine object.
        """
        data_line = self._tabline(line=line)
        self._data.insert(idx, data_line)
        return data_line

    def append(self, line=None):
        """
        Create and append a new data line

        Creates a new data line object and appends it to the end of
        the list of lines.

        The supplied 'line' can be a "raw" line (i.e. string of
        delimited values, e.g. "1\t2\t3"), a list or other
        iterable (e.g. [1, 2, 3]), or a TabLine instance.

        Alternatively, if 'line' is not supplied or is None then
        a default 'empty' TabLine-based object is created, appended
        and returned.

        Arguments:
            line (object): the line to append (either 'raw' string
                of delimited values, a list, or a TabLine instance)

        Returns:
          TabLine: appended data line object.
        """
        line = self._tabline(line)
        self._data.append(line)
        return line

    def append_column(self, name, fill_value=''):
        """
        Append a new (empty) column

        Arguments:
            name (str): name for the new column
            fill_value (any): optional, value to insert into
                all rows in the new column
        """
        for line in self._data:
            line.append_column(name, fill_value)
        self._header.append(name)
        self._ncols = len(self._header)
        return self

    def reorder(self, new_columns):
        """
        Rearrange the columns in the file

        Arguments:
            new_columns (list): list of column names or indices in
                the new order

        Returns:
          TabFile: new TabFile object with columns reordered.
        """
        reordered_tabfile = self._tabfile(column_names=new_columns,
                                          delimiter=self._delimiter)
        for data in self._data:
            reordered_tabfile.append(data.subset(*new_columns))
        return reordered_tabfile

    def transpose(self):
        """
        Transpose the contents of the file

        Returns:
          TabFile: transposed TabFile object.
        """
        transposed_tabfile = self._tabfile(delimiter=self._delimiter)
        for data in self._data:
            transposed_tabfile.append_column(None)
            for i in range(len(data)):
                try:
                    transposed_tabfile[i][-1] = data[i]
                except IndexError:
                    transposed_tabfile.append()
                    transposed_tabfile[i][-1] = data[i]
        return transposed_tabfile

    def transform(self, column_name, transform_func):
        """
        Apply arbitrary function to a column

        For each line of data the transformation function will be invoked
        with the value of the named column, with the result being written
        back to that column (overwriting the existing value).

        Arguments:
            column_name (str): name of column to write transformation result to
            transform_func (object): callable object that will be invoked to
                perform the transformation
        """
        for line in self:
            line[column_name] = transform_func(line[column_name])
        return self

    def compute(self, column_name, compute_func):
        """
        Compute and store values in a new column

        For each line of data the computation function will be invoked
        with the line as the sole argument, and the result will be stored in
        a new column with the specified name.

        Arguments:
            column_name (str): name or index of column to write computation
                result to
            compute_func (object): callable object that will be invoked to
                perform the computation
        """
        if column_name not in self.header():
            try:
                # Check to see if it's actually an integer index
                column_name = int(column_name)
            except ValueError:
                # Neither existing column name nor integer index
                self.append_column(column_name)
        for line in self:
            line[column_name] = compute_func(line)
        return self

    def sort(self, sort_func, reverse=False):
        """
        Sort data using arbitrary function

        Performs an in-place sort based on the suppled sort_func.

        sort_func should be a function object which takes a data line
        object as input and returns a single numerical value; the data
        lines will be sorted in ascending order of these values (or
        descending order if reverse is set to True).

        To sort on the value of a specific column use e.g.

        >>> tabfile.sort(lambda line: line['col'])

        Arguments:
            sort_func (function): function object taking a data line
                object as input and returning a single numerical value
            reverse (bool): (optional) either False (default) to sort
                in ascending order, or True to sort in descending order
        """
        self._data = sorted(self._data,
                            key=sort_func,
                            reverse=reverse)
        return self

    def write(self, filen=None, fp=None, include_header=False, no_hash=False,
              delimiter=None):
        """
        Write the TabFile data to an output file

        One of either the 'filen' or 'fp' arguments must be given,
        specifying the file name or stream to write the TabFile data to.

        Arguments:
            filen (str): (optional) name of file to write to; ignored if fp is
                also specified
            fp (any): (optional) a file-like object opened for writing; used in
                preference to filen if set to a non-null value.
                Note that the calling program must close the stream in
                these cases.
            include_header (bool): (optional) if set to True, the first
                line will be a 'header' line
            no_hash (bool): (optional) if set to True and include_header is
                also True then don't put a hash character '#' at the
                start of the header line in the output file.
            delimiter (str): (optional) delimiter to use when writing data
                values to file (defaults to the delimiter specified on input)
        """
        close_fp = False
        reset_delimiter = self._delimiter
        try:
            if fp is None and filen is not None:
                # Open named file for writing
                fp = open(filen, "wt")
                close_fp = True
            if include_header:
                if not no_hash:
                    leading_hash = '#'
                else:
                    leading_hash = ''
                if delimiter is None:
                    delim = str(self._delimiter)
                else:
                    delim = str(delimiter)
                fp.write(f"{leading_hash}{delim.join(self.header())}\n")
            # Update line delimiters for output if necessary
            if delimiter is not None and delimiter != self._delimiter:
                for data in self._data:
                    data.delimiter(delimiter)
            # Write the data
            for data in self._data:
                fp.write(f"{data}\n")
        finally:
            # Reset line delimiters
            if delimiter is not None and delimiter != reset_delimiter:
                for data in self._data:
                    data.delimiter(reset_delimiter)
            # Only close the stream if it was opened locally
            if close_fp:
                fp.close()

    def _load(self, fp, skip_first_line=False, first_line_is_header=False):
        """
        Internal: load data into the object from file

        Lines starting with '#' are ignored (unless the first_line_is_header
        is set and the first line starts with '#').

        If a header is set then lines with fewer data items than header
        items raise an IndexError exception.

        Arguments:
          fp (File): file-like object to read data from
          skip_first_line (bool): (optional) if True then ignore the first
              line of the input file
          first_line_is_header (bool): (optional) if True then take column
              names from the first line of the file
        """
        line_number = 0
        for line in fp:
            ##line = line.rstrip("\n")
            line_number += 1
            if skip_first_line:
                # Skip first line
                skip_first_line = False
                continue
            elif first_line_is_header and len(self.header()) == 0:
                # Set up header from first line
                self._set_header(line.strip().strip('#').split(self._delimiter))
                first_line_is_header = False
                continue
            if line.lstrip().startswith('#') and \
               not self._keep_commented_lines:
                # Skip commented line
                continue
            # Store data
            data_line = self._tabline(line.rstrip("\n"),
                                      line_number=line_number)
            if self._ncols > 0:
                if len(data_line) != self._ncols:
                    # Inconsistent lines are an error
                    logger.error(f"Line {line_number} has wrong number of data items")
                    logger.error("Line: %s" % data_line)
                    logger.error(f"Expected {self._ncols}, got {len(data_line)}")
                    raise IndexError(f"wrong number of data items in line {line_number}")
            else:
                # Set number of columns
                self._ncols = len(data_line)
            self._data.append(data_line)

    def _set_header(self, column_names):
        """
        Internal: set the names for columns of data

        Arguments:
          column_names (list): list with names for each column in order.
        """
        assert(len(self) == 0)
        if len(self._header) > 0:
            self._header = []
        for name in column_names:
            self._header.append(name)
        self._ncols = len(self._header)

    def _tabline(self, line, line_number=None):
        """
        Internal: wrap data in a TabLine object
        """
        return TabLine(line=line,
                       column_names=self._header,
                       delimiter=self._delimiter,
                       convert_values=self._convert_values,
                       allow_underscores_in_numeric_literals=
                       self._allow_underscores_in_numbers,
                       line_number=line_number)

    def _tabfile(self, *args, **kwargs):
        """
        Internal: return a TabFile object
        """
        return TabFile(*args, **kwargs)

    def __getitem__(self,key):
        return self._data[key]

    def __delitem__(self,key):
        del(self._data[key])

    def __len__(self):
        return len(self._data)

    def __repr__(self):
        return '\n'.join([str(x) for x in self._data])


class TabLine:
    """
    Class representing a line of data from a tab-delimited file

    Values can be accessed by integer index or by column names (if
    set):

    >>> line = TabDataLine("1\t2\t3", ('first','second','third'))
    >>> line[0]
    1
    >>> line["second"]
    2

    Values can also be changed:

    >>> line['second'] = new_value

    Values are automatically converted to integer or float types as
    appropriate.

    Subsets of data can be created using the 'subset' method.

    Line numbers can also be set by the creating subprogram, and
    queried via the 'line_number' method.

    It is possible to use a different field delimiter than tabs, by
    explicitly specifying the value of the 'delimiter' argument,
    e.g. for a comma-delimited line:

    >>> line = TabDataLine("1,2,3",delimiter=',')

    Check if a line is empty:

    >>> if not line:
    ...     print("Blank line")

    Arguments:
        line (str): (optional) 'raw' line with data values separated
            by tabs (or appropriate delimiter)
        column_names (list): (optional) list of column names to assign
            values to
        delimiter (str): (optional) delimiter character (defaults to tab)
        line_number (int): (optional) Line number
        convert_values (bool): if True then convert values to the
            appropriate types; if False then all values will be converted
            to strings.
        allow_underscores_in_numeric_literals (bool): (optional) if True
            then treat numerical values with underscores as numbers
            according to PEP 15; if False (the default) then treat them
            as strings
    """
    def __init__(self, line=None, column_names=None, delimiter='\t',
                 line_number=None, convert_values=True,
                 allow_underscores_in_numeric_literals=False):
        # Conversion function
        if convert_values:
            if allow_underscores_in_numeric_literals:
                self._convert_func = self._convert_to_type_pep515
            else:
                self._convert_func = self._convert_to_type
        else:
            self._convert_func = self._convert_to_str
        # Data
        self._data = []
        self._delimiter = str(delimiter)
        self._line_number = None
        # Handle input line
        if line is not None:
            if str(line) == line:
                # Assume input is a 'raw' string
                line = [x.rstrip("\n") for x in str(line).split(self._delimiter)]
            for value in line:
                self._data.append(self._convert_func(value))
        # Column names
        if column_names:
            self._column_names = [str(c) for c in column_names]
            while len(self._data) < len(self._column_names):
                self._data.append("")
        else:
            self._column_names = []
        # Line number
        if line_number is not None:
            invalid_line_number = False
            try:
                line_number = int(line_number)
                if line_number < 0:
                    # Line number is less than zero
                    invalid_line_number = True
            except TypeError:
                # Can't convert to an integer
                invalid_line_number = True
            if invalid_line_number:
                raise ValueError(f"invalid line number: '{line_number}'")
        self._line_number = line_number

    def _convert_to_str(self,value):
        """
        Internal: convert value to string
        """
        return str(value)

    def _convert_to_type(self,value):
        """
        Internal: convert a value to the correct type

        Used to coerce input values into integers or floats
        if appropriate before storage in the TabDataLine
        object.
        """
        converted = value
        # Value containing underscores always
        # preserved
        try:
            str(converted).index('_')
            return converted
        except ValueError:
            pass
        # Test for numerical values
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

    def _convert_to_type_pep515(self, value):
        """
        Internal: convert a value to the correct type

        Used to coerce input values into integers or floats
        if appropriate before storage in the TabDataLine
        object.

        The conversion honors PEP 515 so numerical values
        can also contain underscore characters.
        """
        converted = value
        # Remove underscores
        no_underscores = str(converted).replace('_','')
        try:
            # Try integer
            converted = int(str(no_underscores))
        except ValueError:
            # Not an integer, try float
            try:
                converted = float(str(no_underscores))
            except ValueError:
                # Not a float, leave as input
                pass
        # Return value
        return converted

    def append(self, *values):
        """
        Append values to the data line

        Should only be used when creating new data lines.

        Arguments:
            values (list): (optional) list of values to append to
            the data line
        """
        for value in values:
            self._data.append(self._convert_func(value))

    def append_column(self, key, value):
        """
        Append keyed values to the data line

        This adds a new value along with a header name (i.e. key)
        """
        self._column_names.append(key)
        self._data.append(self._convert_func(value))
        return self

    def subset(self, *keys):
        """
        Return a subset of data items

        This method creates a new TabLine instance with a
        subset of data specified by the 'keys' argument, e.g.

        >>> new_line = line.subset(2,1)

        returns an instance with only the 2nd and 3rd data values
        in reverse order.

        To access the items in a subset using index notation,
        use the same keys as those specified when the subset was
        created. For example, for

        >>> s = line.subset("two","nine")

        use s["two"] and s["nine"] to access the data; while for

        >>> s = line.subset(2,9)

        use s[2] and s[9].

        Arguments:
            keys (list): one or more keys specifying columns to
                include in the subset. Keys can be column indices,
                column names, or a mixture, and the same column
                can be referenced multiple times.

        Returns:
            TabLine: new TabLine instance with subset of data items.
        """
        subset = TabLine()
        for key in keys:
            subset.append_column(key, self[key])
        return subset

    def line_number(self):
        """
        Return the line number associated with the line

        NB The line number is set by the class or function which
        created the TabDataLine object, it is not guaranteed by
        the TabDataLine class itself.
        """
        return self._line_number

    def delimiter(self, new_delimiter=None):
        """
        Set and get the delimiter for the line

        If 'new_delimiter' is not None then the field delimiter
        for the line will be updated to the supplied value. This
        affects how lines are represented via the __repr__
        built-in.

        Arguments:
            new_delimiter (str or None): (optional) new delimiter

        Returns:
            String: the current value of the delimiter.
        """
        if new_delimiter is not None:
            self._delimiter = str(new_delimiter)
        return self._delimiter

    def __getitem__(self,key):
        """
        Implement value = TabDataLine[key]

        'key' can be the name of a column or an integer index
        (starting from zero). Column names are checked first.

        WARNING there is potential ambiguity if any column "names"
        also happen to be integers.
        """
        # See if key is a column name
        try:
            i = self._column_names.index(key)
            return self._data[i]
        except ValueError:
            # Not a column name
            # See if it's an integer index
            try:
                i = int(key)
            except ValueError:
                # Not an integer
                raise KeyError(f"column '{key}' not found")
            try:
                return self._data[i]
            except IndexError:
                # Integer but out of range
                raise IndexError(f"integer index out of range for '{key}")

    def __setitem__(self, key, value):
        """
        Implement TabDataLine[key] = value

        'key' can be the name of a column or an integer index
        (starting from zero). Column names are checked first.

        WARNING there is potential ambiguity if any column "names"
        also happen to be integers.
        """
        # Convert value to correct type
        converted_value = self._convert_func(value)
        # See if key is a column name
        try:
            i = self._column_names.index(key)
            self._data[i] = converted_value
        except ValueError:
            # Not a column name
            # See if it's an integer index
            try:
                i = int(key)
            except ValueError:
                # Not an integer
                raise KeyError(f"column '{key}' not found")
            try:
                self._data[i] = converted_value
            except IndexError:
                # Integer but out of range
                raise IndexError(f"integer index out of range for '{key}'")

    def __iter__(self):
        for i in range(len(self._data)):
            yield self._data[i]

    def __len__(self):
        return len(self._data)

    def __nonzero__(self):
        for item in self._data:
            if str(item).strip(): return True
        return False

    def __eq__(self, other):
        if not isinstance(other, TabLine):
            return False
        if self._data != other._data:
            return False
        if self._column_names != other._column_names:
            return False
        if self._delimiter != other._delimiter:
            return False
        return True

    def __repr__(self):
        return self._delimiter.join([str(x) for x in self._data])


class TabFileIterator(Iterator):
    """
    Helper class for iterating through lines in a tab-delimited file

    Class to loop over all lines in a TSV file, returning a TabDataLine
    object for each record.

    The input file should be a tab-delimited text file, specified as
    either a file name (using the 'filen' argument), or a file-like
    object opened for line reading (using the 'fp' argument).

    Each iteration returns a TabLine populated with data from the file.

    Example usage:

    >>> for line in TabFileIterator(filen='data.tsv'):
    ...     print(line)

    Arguments:
        filen (str): name of the file to iterate through
        fp (any): file-like object opened for reading
        column_names (list): optional list of names to use as
            column headers in the returned TabLines
    """
    def __init__(self, filen=None, fp=None, column_names=None):
        self._filen = filen
        self._column_names = column_names
        self._line_number = 0
        self._close_fp = False
        if fp is None:
            self._fp = open(filen, "rt")
            self._close_fp = True
        else:
            self._fp = fp

    def _tabline(self, line):
        """
        Internal: wrap data in a TabLine object
        """
        return TabLine(line=line,
                       column_names=self._column_names,
                       line_number=self._line_number)

    def __next__(self):
        """
        Return next record from TSV file as a TabDataLine object
        """
        line = self._fp.readline()
        self._line_number += 1
        if line != "":
            return self._tabline(line=line)
        else:
            # Reached EOF
            if self._close_fp:
                self._fp.close()
            raise StopIteration