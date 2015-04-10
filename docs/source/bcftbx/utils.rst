``bcftbx.utils``
================

.. automodule:: bcftbx.utils

General utility classes
***********************

.. autoclass:: AttributeDictionary
.. autoclass:: OrderedDictionary

File system wrappers and utilities
**********************************

.. autoclass:: PathInfo
   :members:

.. autofunction:: mkdir
.. autofunction:: mklink
.. autofunction:: chmod
.. autofunction:: touch
.. autofunction:: format_file_size
.. autofunction:: commonprefix
.. autofunction:: is_gzipped_file
.. autofunction:: rootname
.. autofunction:: find_program
.. autofunction:: get_current_user
.. autofunction:: get_user_from_uid
.. autofunction:: get_uid_from_user
.. autofunction:: get_group from_group
.. autofunction:: walk
.. autofunction:: list_dirs
.. autofunction:: strip_ext

Symbolic link handling
**********************

.. autoclass:: Symlink
   :members:

.. autofunction:: links

Sample name utilities
*********************

.. autofunction:: extract_initials
.. autofunction:: extract_prefix
.. autofunction:: extract_index_as_string
.. autofunction:: extract_index
.. autofunction:: pretty_print_names
.. autofunction:: name_matches

File manipulations
******************

.. autofunction:: concatenate_fastq_files

Text manipulations
******************

.. autofunction:: split_into_lines
