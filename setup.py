"""Description

Setup script to install genomics/bcftbx

Copyright (C) University of Manchester 2011-15 Peter Briggs

"""

# Hack to acquire all scripts that we want to
# install into 'bin'
from glob import glob
scripts = []
for pattern in ('build-indexes/*.sh',
                'ChIP-seq/*.pl','ChIP-seq/*.py',
                'illumina2cluster/*.py','illumina2cluster/*.sh',
                'microarray/*.py',
                'NGS-general/*.pl','NGS-general/*.py','NGS-general/*.py',
                'QC-pipeline/*.py','QC-pipeline/*.sh',
                'RNA-seq/*.py',
                'solid2cluster/*.py','solid2cluster/*.sh',
                'utils/*.pl','utils/*.py','utils/*.R','utils/*.sh',
                'share/bcftbx.*.sh'):
    scripts.extend(glob(pattern))

# Setup for installation etc
from setuptools import setup
import bcftbx
setup(name = "genomics",
      version = bcftbx.__version__,
      description = 'Utilities for NGS and genomic bioinformatics',
      long_description = """Utility programs and libraries used for Next Generation
      Sequencing (NGS) and genomic bioinformatics, developed and used within the
      Bioinformatics Core Facility (BCF) at the University of Manchester""",
      url = 'https://github.com/fls-bioinformatics-core/genomics',
      maintainer = 'Peter Briggs',
      maintainer_email = 'peter.briggs@manchester.ac.uk',
      packages = ['bcftbx','bcftbx.qc'],
      license = 'Artistic License',
      # Pull in dependencies
      install_requires = ['xlwt >= 0.7.2',
                          'xlrd >= 0.7.1',
                          'xlutils >= 1.4.1'],
      # Enable 'python setup.py test'
      test_suite='nose.collector',
      tests_require=['nose'],
      scripts = scripts,
      include_package_data=True,
      zip_safe = False)
