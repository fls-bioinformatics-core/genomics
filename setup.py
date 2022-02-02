"""Description

Setup script to install genomics/bcftbx

Copyright (C) University of Manchester 2011-2021 Peter Briggs

"""

# Hack to acquire all scripts that we want to
# install into 'bin'
from glob import glob
scripts = []
for pattern in ('bin/*.py','bin/*.sh',):
    scripts.extend(glob(pattern))
for pattern in ('utils/*.pl','utils/*.py','utils/*.R','utils/*.sh'):
    scripts.extend(glob(pattern))

# Setup for installation etc
from setuptools import setup
import bcftbx
setup(name = "genomics-bcftbx",
      version = bcftbx.__version__,
      description = 'Utilities for NGS and genomic bioinformatics',
      long_description = """Utility programs and libraries used for Next Generation
      Sequencing (NGS) and genomic bioinformatics, developed and used within the
      Bioinformatics Core Facility (BCF) at the University of Manchester""",
      url = 'https://github.com/fls-bioinformatics-core/genomics',
      maintainer = 'Peter Briggs',
      maintainer_email = 'peter.briggs@manchester.ac.uk',
      packages = ['bcftbx',
                  'bcftbx.cli',
                  'bcftbx.qc'],
      license = 'AFL-3',
      # Pull in dependencies
      install_requires = ['xlwt >= 0.7.2',
                          'xlrd >= 0.7.1',
                          'xlutils >= 1.4.1',
                          'xlsxwriter >= 0.8.4',],
      # Enable 'python setup.py test'
      test_suite='nose.collector',
      tests_require=['nose'],
      # Scripts
      scripts = scripts,
      # Configuration file for QC
      data_files = [('share',['share/bcftbx.functions.sh',
                              'share/bcftbx.lock.sh']),],
      classifiers=[
          "Development Status :: 4 - Beta",
          "Environment :: Console",
          "Intended Audience :: End Users/Desktop",
          "Intended Audience :: Science/Research",
          "Intended Audience :: Developers",
          "License :: OSI Approved :: Academic Free License (AFL)",
          "Operating System :: POSIX :: Linux",
          "Operating System :: MacOS",
          "Topic :: Scientific/Engineering",
          "Topic :: Scientific/Engineering :: Bio-Informatics",
          "Programming Language :: Python :: 3",
          'Programming Language :: Python :: 3.6',
          'Programming Language :: Python :: 3.7',
          'Programming Language :: Python :: 3.8',
      ],
      include_package_data=True,
      zip_safe = False)
