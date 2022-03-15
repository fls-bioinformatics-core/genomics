************
Installation
************

The ``genomics-bcftbx`` package is available from its GitHub respository at

 * https://github.com/fls-bioinformatics-core/genomics

Specific versions can be obtained as ``tar.gz`` archives from:

 * https://github.com/fls-bioinformatics-core/genomics/releases

The software is written in Python (see :ref:`supported_python_versions` for
a list of supported versions).

It is recommended to install the package into a Python ``virtualenv``, for
example::

    virtualenv venv.bcftbx
    . venv.bcftbx/bin/activate

To install a specific version, first download and unpack the source code,
e.g.::

    wget https://github.com/fls-bioinformatics-core/genomics/archive/2.0.0.tar.gz
    tar zxf 2.0.0.tar.gz

Then install the package using::

    pip install ./genomics-2.0.0

See the :doc:`requirements documentation <requirements>` for details
of other 3rd party software that is needed for specific utilities.

