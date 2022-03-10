Installation and set up
=======================

Installing the genomics/bcftbx package
**************************************

Currently it is recommended to install ``genomics-bcftbx`` from Github
into a Python virtual environment, for example:

::
   
    virtualenv venv
    . venv/bin/activate
    pip install https://github.com/fls-bioinformatics-core/genomics/archive/1.11.0.tar.gz

The list of available releases can be found at https://github.com/fls-bioinformatics-core/genomics/releases

Dependencies
************

The package consists predominantly of code written in Python, and the
following versions are supported:

* Python 3.6
* Python 3.7
* Python 3.8

Additional Python packages will be installed automatically by ``pip``.

In addition some of the utilities also use 3rd-party software packages,
including:

* ``STAR`` https://github.com/alexdobin/STAR
