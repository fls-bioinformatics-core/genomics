ChIP-seq specific utilities
===========================

Scripts and tools for ChIP-seq specific tasks.

* :ref:`make_macs2_xls`: convert a MACS output file into an Excel spreadsheet

.. _make_macs_xls:
.. _make_macs2_xls:

make_macs2_xls.py
*****************

Convert a MACS2 tab-delimited output file into an Excel (XLSX) spreadsheet.

Usage::

    make_macs2_xls.py OPTIONS <macs_output_file>.xls [<xlsx_output_file>]

Options::

  -f XLS_FORMAT, --format=XLS_FORMAT
                        specify the output Excel spreadsheet format; must be
                        one of 'xlsx' or 'xls' (default is 'xlsx')
  -b, --bed             write an additional TSV file with chrom,
                        abs_summit+100 and abs_summit-100 data as the columns.
                        (NB only possible for MACS2 run without --broad)

If the ``xlsx_output_file`` isn't specified then it defaults to
``XLS_<macs_output_file>.xlsx``.

.. note::

   To process output from MACS 1.4.2 and earlier use ``make_macs_xls.py``;
   this version only supports ``.xls`` output and doesn't provide either of
   the ``-f`` or ``-b`` options.
