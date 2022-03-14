Reporting ChIP-seq outputs
==========================

The :ref:`reference_make_macs2_xls` utility can be used to convert an
output tab-delimited ``.XLS`` file from ``macs2`` into an MS Excel
spreadsheet (either ``.xlsx`` or ``.xls`` format).

Additionally a ``.bed`` format file can be output, provided that ``macs2``
was not run with the ``--broad`` option.

To process output from older versions of ``macs`` (i.e. 1.4.2 and earlier)
the legacy :ref:`reference_make_macs_xls` utility can be used; however for
this version only MS XLS format is supported, and there is no option to
output a ``.bed`` file.
