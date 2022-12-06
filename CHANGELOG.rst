Version History and Changes
===========================

---------------------------
Version 1.12.0 (2022-12-06)
---------------------------

* bcftbx/IlluminaData: add basic support for 'RunParameters.xml'
  files in Illumina runs
  https://github.com/fls-bioinformatics-core/genomics/pull/206
* bcftbx: add NovaSeq 6000 as a recognised sequencing platform
  ('novaseq6000')
  https://github.com/fls-bioinformatics-core/genomics/pull/205
* bcftbx: add Python 3.9 and 3.10 to list of supported versions
  https://github.com/fls-bioinformatics-core/genomics/pull/202
* bcftbx/Pipeline: expose stderr output from the 'Job' class
  https://github.com/fls-bioinformatics-core/genomics/pull/201
* Substantial refactoring of utility scripts (and removal of
  some deprecated legacy scripts):
  - utils:
    https://github.com/fls-bioinformatics-core/genomics/pull/198
  - QC-pipeline:
    https://github.com/fls-bioinformatics-core/genomics/pull/197
  - NGS-utils:
    https://github.com/fls-bioinformatics-core/genomics/pull/195
  - solid2cluster:
    https://github.com/fls-bioinformatics-core/genomics/pull/194
  - microarray:
    https://github.com/fls-bioinformatics-core/genomics/pull/192
  - build-indexes:
    https://github.com/fls-bioinformatics-core/genomics/pull/190
  - RNA-seq:
    https://github.com/fls-bioinformatics-core/genomics/pull/189
  - ChIP-seq:
    https://github.com/fls-bioinformatics-core/genomics/pull/188
  - illumina2cluster:
    https://github.com/fls-bioinformatics-core/genomics/pull/187
* bcftbx/fasta: new library module with 'FastaChromIterator'
  class (relocated from 'split_fasta.py' utility)
  https://github.com/fls-bioinformatics-core/genomics/pull/196
* bcftbx/TabFile: add 'TabFileIterator' class (relocated from
  'best_exons.py' utility)
  https://github.com/fls-bioinformatics-core/genomics/pull/193
* bcftbx: drop support for Python 2
  https://github.com/fls-bioinformatics-core/genomics/pull/185
* prep_sample_sheet.py: add option to reverse complement i5
  indexes
  https://github.com/fls-bioinformatics-core/genomics/pull/183

---------------------------
Version 1.11.1 (2021-06-07)
---------------------------

* bcftbx/mock: fix mock HISEQ sample sheet data
  https://github.com/fls-bioinformatics-core/genomics/pull/181
* illumina2cluster/verify_paired.py: fix broken ``--version``
  option
  https://github.com/fls-bioinformatics-core/genomics/pull/180

---------------------------
Version 1.11.0 (2020-09-16)
---------------------------

* bcftbx/TabFile: 'TabFile' can keep commented lines from
  the input file by specifying 'keep_commented_lines=True'
  https://github.com/fls-bioinformatics-core/genomics/pull/178
* bcftbx/TabFile: 'TabFile.appendColumn' method accepts new
  'fill_value' argument, to provide a default value to put
  into all rows in the new column
  https://github.com/fls-bioinformatics-core/genomics/pull/176
* bcftbx/mock: mock 'RunInfoXml' updated to set the flowcell
  ID more consistently with real-life examples
  https://github.com/fls-bioinformatics-core/genomics/pull/177

---------------------------
Version 1.10.0 (2020-09-16)
---------------------------

* bcftbx/IlluminaData: relax the platform identification
  mechanism in 'IlluminaRun'; Illumina-like run directories
  will be identified as generic 'illumina' platform if no
  explicit platform is supplied or can be identified from the
  instrument name. Exceptions are now only raised for run
  directories which do not appear to come from an Illumina
  sequencer
  https://github.com/fls-bioinformatics-core/genomics/pull/174
* bcftbx/IlluminaData: add new properties to 'IlluminaRun'
  instances: 'sample_sheet' ('SampleSheet' instance) and
  'runinfo' ('IlluminaRunInfo' instance)
  https://github.com/fls-bioinformatics-core/genomics/pull/173
* bcftbx/IlluminaData: add new properties to 'IlluminaRunInfo'
  instances: 'instrument', 'date', 'flowcell' and 'lane_count'
  (extracted from 'RunInfo.xml' file)
  https://github.com/fls-bioinformatics-core/genomics/pull/172
* bcftbx/IlluminaData: 'SampleSheet' class ignores trailing
  empty lines present in the input sample sheet file
  https://github.com/fls-bioinformatics-core/genomics/pull/171
* bcftbx/JobRunner: 'SimpleJobRunner' reports status of
  'join_logs' in '__repr__'; 'fetch_runner' handles 'join_logs'
  when setting up 'SimpleJobRunner'
  https://github.com/fls-bioinformatics-core/genomics/pull/170
* QC-pipeline: 'fastq_screen.sh' updated to handle FastqScreen
  v0.13 and v0.14
  https://github.com/fls-bioinformatics-core/genomics/pull/168

--------------------------
Version 1.9.1 (2020-06-09)
--------------------------

* bcftbx: fix unclosed files and related bugs that were
  producing 'ResourceWarnings' under Python 3 tests
  https://github.com/fls-bioinformatics-core/genomics/pull/163
* bcftbx/JobRunner: improvements to thread safety of the
  'SimpleJobRunner' class when handling job completion and
  cleanup
  https://github.com/fls-bioinformatics-core/genomics/pull/166

--------------------------
Version 1.9.0 (2020-05-20)
--------------------------

* bcftbx/JobRunner: enable available number of CPUS (aka slots,
  cores, threads) to be set and accessed within the
  'SimpleJobRunner' and 'GEJobRunner' classes
  https://github.com/fls-bioinformatics-core/genomics/pull/152
* bcftbx/mock: update 'MockIlluminaData' class to enable
  forcing of creation of sample-level subdirectories when
  generating mock data
  https://github.com/fls-bioinformatics-core/genomics/pull/161
* bcftbx/IlluminaData: update 'SampleSheetPredictor' to
  handle prediction of index reads, and to handle arbitrary
  reads
  https://github.com/fls-bioinformatics-core/genomics/pull/160
* bcftbx/htmlpagewriter: remove unused imports
  https://github.com/fls-bioinformatics-core/genomics/pull/158
* Extend the list of supported Python versions to include
  3.6 and 3.8; update the licence to Academic Free License
  AFL 3.0
  https://github.com/fls-bioinformatics-core/genomics/pull/157
* config/qc.setup.sample: updated to allow user-defined
  environment variables to take precedence over values defined
  in the setup file
  https://github.com/fls-bioinformatics-core/genomics/pull/156

--------------------------
Version 1.8.3 (2020-02-27)
--------------------------

* bcftbx: remove internal version numbers from modules which
  still had them
  https://github.com/fls-bioinformatics-core/genomics/pull/155
* bcftbx/htmlpagewriter: update 'PNGBase64Encoder' for Python
  3 compatibility
  https://github.com/fls-bioinformatics-core/genomics/pull/154
* bcftbx/IlluminaData: 'SampleSheetPredictor' updated to
  handle blank lane numbers in input samplesheet
  https://github.com/fls-bioinformatics-core/genomics/pull/153

--------------------------
Version 1.8.2 (2020-02-17)
--------------------------

* bcftbx/IlluminaData: fix error in call to 'digits' method
  in 'split_run_name_full'
  https://github.com/fls-bioinformatics-core/genomics/pull/149
* NGS-general/extract_reads.py: fix bug with handling gzipped
  files under Python 2, and broken ``--version`` option under
  Python 3
  https://github.com/fls-bioinformatics-core/genomics/pull/150
* bcftbx/FASTQFile: fix bugs with reading Fastqs from disk
  under Python 3
  https://github.com/fls-bioinformatics-core/genomics/pull/151

--------------------------
Version 1.8.1 (2019-11-20)
--------------------------

* bcftbx/IlluminaData: fix to `SampleSheet` class to handle
  cases when header lines have a 'key' without a comma
  delimiter or value (thanks Ryan Golhar @golharam)
  https://github.com/fls-bioinformatics-core/genomics/pull/148

--------------------------
Version 1.8.0 (2019-09-27)
--------------------------

* Updates for compatibility with Python 2.7 and 3.7

  - https://github.com/fls-bioinformatics-core/genomics/pull/146
  - https://github.com/fls-bioinformatics-core/genomics/pull/145
  - https://github.com/fls-bioinformatics-core/genomics/pull/144
  - https://github.com/fls-bioinformatics-core/genomics/pull/143
  - https://github.com/fls-bioinformatics-core/genomics/pull/141
  - https://github.com/fls-bioinformatics-core/genomics/pull/139
  - https://github.com/fls-bioinformatics-core/genomics/pull/138
  - https://github.com/fls-bioinformatics-core/genomics/pull/137
  - https://github.com/fls-bioinformatics-core/genomics/pull/136
  - https://github.com/fls-bioinformatics-core/genomics/pull/135
  - https://github.com/fls-bioinformatics-core/genomics/pull/134
  - https://github.com/fls-bioinformatics-core/genomics/pull/133
  - https://github.com/fls-bioinformatics-core/genomics/pull/132
  - https://github.com/fls-bioinformatics-core/genomics/pull/131
  - https://github.com/fls-bioinformatics-core/genomics/pull/130
  - https://github.com/fls-bioinformatics-core/genomics/pull/128
  - https://github.com/fls-bioinformatics-core/genomics/pull/127
  - https://github.com/fls-bioinformatics-core/genomics/pull/126
  - https://github.com/fls-bioinformatics-core/genomics/pull/125
  - https://github.com/fls-bioinformatics-core/genomics/pull/124
  - https://github.com/fls-bioinformatics-core/genomics/pull/121
  - https://github.com/fls-bioinformatics-core/genomics/pull/120
  - https://github.com/fls-bioinformatics-core/genomics/pull/119
  - https://github.com/fls-bioinformatics-core/genomics/pull/118
  - https://github.com/fls-bioinformatics-core/genomics/pull/117
  - https://github.com/fls-bioinformatics-core/genomics/pull/116
  - https://github.com/fls-bioinformatics-core/genomics/pull/115
  - https://github.com/fls-bioinformatics-core/genomics/pull/114
  - https://github.com/fls-bioinformatics-core/genomics/pull/113
  - https://github.com/fls-bioinformatics-core/genomics/pull/112
  - https://github.com/fls-bioinformatics-core/genomics/pull/110
  - https://github.com/fls-bioinformatics-core/genomics/pull/109
  - https://github.com/fls-bioinformatics-core/genomics/pull/108
  - https://github.com/fls-bioinformatics-core/genomics/pull/107
  - https://github.com/fls-bioinformatics-core/genomics/pull/106


--------------------------
Version 1.7.0 (2019-07-04)
--------------------------

* bcftbx/cmdparse: updated to use `argparse` as the default
  subparser
  https://github.com/fls-bioinformatics-core/genomics/pull/99
* bcftbx: switch to using Python3-compatible `print` function
  instead of `print` statement
  https://github.com/fls-bioinformatics-core/genomics/pull/100
* bcftbx: fix Python syntax for raising and capturing
  exceptions
  https://github.com/fls-bioinformatics-core/genomics/pull/101
* bcftbx/JobRunner: remove the `DRMAAJobRunner` class
  https://github.com/fls-bioinformatics-core/genomics/pull/102
* illumina2cluster/prep_sample_sheet.py: fix to bug with
  conflicting `-v` options introduced in previous version
  https://github.com/fls-bioinformatics-core/genomics/pull/105

--------------------------
Version 1.6.0 (2019-06-10)
--------------------------

* Command line utilities: updated to use `argparse` for
  processing command line arguments
  https://github.com/fls-bioinformatics-core/genomics/pull/96
* bcftbx: Python classes updated to ensure they all inherit
  from `object`
  https://github.com/fls-bioinformatics-core/genomics/pull/95
* bcftbx/mock: `MockIlluminaData` updated to handle arbitrary
  reads (e.g. `R1`,`R2`,`I1`) when creating Fastqs
  https://github.com/fls-bioinformatics-core/genomics/pull/97

--------------------------
Version 1.5.5 (2019-04-30)
--------------------------

* bcftbx/JobRunner: stability improvements and bug fixes to
  GEJobRunner
  https://github.com/fls-bioinformatics-core/genomics/pull/88
  https://github.com/fls-bioinformatics-core/genomics/pull/90
  https://github.com/fls-bioinformatics-core/genomics/pull/91

--------------------------
Version 1.5.4 (2019-02-21)
--------------------------

* bcftbx/IlluminaData: fix to SampleSheet class to handle
  samplesheet files which contain `[Manifests]` section
  https://github.com/fls-bioinformatics-core/genomics/pull/87

--------------------------
Version 1.5.3 (2019-01-31)
--------------------------

* bcftbx/JobRunner: fixes to GEJobRunner to deal with race
  conditions on job finalization
  https://github.com/fls-bioinformatics-core/genomics/pull/85

--------------------------
Version 1.5.2 (2018-09-28)
--------------------------

* QC-pipeline/fastq_strand.py:

  - version 0.0.4: fixes cases when `STAR` fails
    to map any reads
    https://github.com/fls-bioinformatics-core/genomics/pull/81

* QC-pipeline/illumina_qc.sh:

  - version 1.3.3: fixes bug setting permissions
    when using `--no-screens` option
    https://github.com/fls-bioinformatics-core/genomics/pull/82

* bcftbx/JobRunner: updates to `GEJobRunner` to
  improve thread safety
  https://github.com/fls-bioinformatics-core/genomics/pull/80

--------------------------
Version 1.5.1 (2018-09-13)
--------------------------

* bcftbx/IlluminaData:

  - add `iSeq` to the list of known platforms
  - enable handling of run names with four-digit
    year in the datestamp
    https://github.com/fls-bioinformatics-core/genomics/pull/79
  - drop module-level version number


--------------------------
Version 1.5.0 (2018-08-22)
--------------------------

* bcftbx/JobRunner: substantial overhaul of
  `GEJobRunner` to reduce footprint when
  running on compute cluster e.g. removed calls
  to `qacct` and reduced calls to `qstat`.

  - https://github.com/fls-bioinformatics-core/genomics/pull/73
  - https://github.com/fls-bioinformatics-core/genomics/pull/76

* NGS-general/split_fastq.py: new utility that
  splits a Fastq file or R1/R2 pair based on the
  lanes present in the file(s); can be used to
  reverse the merging of Fastq files when
  `bcl2fastq` is run with `--no-lane-splitting`

  - https://github.com/fls-bioinformatics-core/genomics/pull/77

* QC-pipeline/fastq_strand.py:

  - version 0.0.3
  - removes existing output files on startup
  - only write final outputs on success
  - always remove temporary working directories
    on completion (even if program failed)
  - https://github.com/fls-bioinformatics-core/genomics/pull/72

* bcftbx/utils: reimplement `AttributeDictionary`
  class so it can be pickled

  - https://github.com/fls-bioinformatics-core/genomics/pull/78


--------------------------
Version 1.4.0 (2018-07-03)
--------------------------

* ChIP-seq/make_macs2_xls.py

  - version 0.5.0: add '-b'/'--bed' option to
    output additional TSV file with { chrom,
    abs_summit+/-100 } columns

* QC-pipeline/fastq_strand.py:

  - version 0.0.2:
  - can be run on a single Fastq (as well as pairs)
  - changes to command line if specifying STAR
    indexes directly: now needs '-g'/'--genome'
    option for this

* QC-pipeline/illumina_qc.sh:

  - version 1.3.2: new '--no-screens' option
    suppresses running of 'fastq_screen'


--------------------------
Version 1.3.2 (2018-05-14)
--------------------------

* bcftbx/JobRunner: update `GEJobRunner` to sanitize
  the supplied job name for use internally (before
  submission to Grid Engine); the supplied name is
  still used for communicating with external
  processes

--------------------------
Version 1.3.1 (2018-04-19)
--------------------------

* bcftbx/JobRunner: fix `GEJobRunner` to wrap
  script arguments in double quotes if they
  contain whitespace

--------------------------
Version 1.3.0 (2018-03-29)
--------------------------

* QC-pipeline/fastq_strand.py: new utility program
  which runs the STAR aligner to generate statistics
  on the strandedness of Fastq R1/R2 file pairs
* bcftbx/IlluminaData: fix the `fix_bases_mask`
  function to correctly handle empty barcode
  sequences

--------------------------
Version 1.2.0 (2018-03-29)
--------------------------

* NGS-general/reorder_fasta.py: new utility program
  to reorder chromosomes into karyotypical order in
  a FASTA file
* bcftbx/IlluminaData: new function
  `split_run_name_full`, which also extracts the
  datestamp, instrument name, flow cell ID and prefix
  from the run name
* bcftbx/IlluminaData: allow platform to be specified
  explicitly when creating `IlluminaRun` objects
  (for when platform cannot be extracted from the
  data directory name)

--------------------------
Version 1.1.0 (2018-01-24)
--------------------------

* bcftbx/cmdparse: major update to enable
  `argparse` to used as an alternative to `optparse`
  when parsing subcommands (thanks to Mohit Agrawal
  `@mohit2agrawal`)
* bcftbx/IlluminaData:

  - Enable `SampleSheet` class to handle quoted header
    values with commas in IEM-format sample sheets
  - Update `SampleSheetPredictor` to handle missing
    (blank) projects; fix bugs with the `set` method
    and update documentation.

* bcftbx/JobRunner: trap for attempt to delete a
  a missing/already deleted job in
  `SimpleJobRunner.list()`

--------------------------
Version 1.0.4 (2017-10-05)
--------------------------

* bcftbx/utils:

  - `mkdir` function supports new `recursive` option
    (creates any intermediate directories that are
    required)
  - New `mkdirs` function creates intermediate
    directories automatically (wraps `mkdir`)

* bcftbx/IlluminaData: samplesheet prediction and
  validation allows invoking subprogram to force
  insertion of 'sample' directory level even if
  `bcl2fastq` wouldn't normally produce one (needed
  for 10xGenomics `cellranger mkfastq` output)
* bcftbx/ngsutils: new library module with file
  reading and Fastq read extraction functions taken
  from `NGS-general/extract_reads.py` utility
* NGS-general/extract_reads.py: read extraction
  functions moved into new `bcftbx.ngsutils` module

--------------------------
Version 1.0.3 (2017-08-31)
--------------------------

* QC-pipeline/illumina_qc.sh:

  - version 1.3.1
  - reduce the default subset size for `fastq_screen`
    to 10000
  - can now handle Fastqs with `.fq[.gz]` extension
  - new option `--qc_dir` (specify target QC output
    directory
  - checks that required programs are on the path at
    start up

* QC-pipeline/fastq_screen.sh:

  - reduce the default subset size to 10000
  - can now handle Fastqs with `.fq[.gz]` extension
  - new option `--qc_dir` (specify target QC output
    directory

* bcftbx/Pipeline: `GetFastq[Gz]Files` now also
  detects `.fq[.gz]` files
* bcftbx/qc/report: 'strip_ngs_extensions' now also
  handles `.fq[.gz]` files

--------------------------
Version 1.0.2 (2017-05-12)
--------------------------

* bcftbx/FASTQFile: `FastqIterator` & `FastqRead`
  updated to handle reads with zero-length sequences
* bcftbx/JobRunner: `GEJobRunner` skips `qacct` call
  when job is terminated.
* bcftbx/IlluminaData: `IlluminaFastq` updated to
  handle "index read" (i.e. I1/I2) Fastq file names

--------------------------
Version 1.0.1 (2017-03-31)
--------------------------

* bcftbx/htmlpagewriter: fix bug writing closing
  `</head>` tag to HTML documents
* illumina2cluster/prep_sample_sheet.py: move the
  lane/name parsing functions into `utils` library
* QC-pipeline/fastq_screen.sh: explicitly specify
  `fastq_screen` `--force` option to overwrite
  existing outputs

--------------------------
Version 1.0.0 (2017-02-23)
--------------------------

* bcftbx/FASTQFile:

  - `FastqRead` now supports equality operator (`==`)
     to check if two reads are the same.
  - `nreads` function updated to implicitly handle
    gzipped FASTQs.

* bcftbx/IlluminaData: `duplicated_names` function
  handles duplicates in IEM samplesheets which don't
  have an `index` column.
* QC-pipeline/fastq_screen.sh:

  - updated to support `fastq_screen` versions 0.9.*
  - trap for unsupported `--color` option for later
    versions of `fastq_screen` (0.6.0+)
  - trap for broken `--subset` option in versions
    0.6.0-2 of `fastq_screen`


----------------------------
Version 0.99.15 (2016-10-07)
----------------------------

* bcftbx/IlluminaData: fix bug in `SampleSheetPredictor`
  class which generated incorrect sample indexes for
  `bcl2fastq2` output when the sample sheet contained
  lanes out of order (e.g. 2 appearing before 1).
* bcftbx/IlluminaData: new function
  `list_missing_fastqs` (returns list of Fastqs
  predicted from sample sheet which are missing from
  the output of `CASAVA` or `bcl2fastq`); update
  `verify_run_against_sample_sheet` to wrap this
  (functionality should be unchanged).

----------------------------
Version 0.99.14 (2016-08-31)
----------------------------

* bcftbx/IlluminaData: new class `SampleSheetPredictor`
  (and supporting classes) for improved prediction of
  sample sheet outputs; new function `cmp_sample_names`
  added (use for sorting sample names)
* illumina2cluster/prep_sample_sheet.py 0.4.0: update
  prediction of outputs and add automatic pagination
  when run in a terminal window
* QC-pipeline/fastq_screen.sh: updated to handle
  `fastq_screen` 0.6.* and 0.7.0.
* bcftbx/JobRunner: update `SimpleJobRunner` and
  `GEJobRunner` classes to capture exit code from the
  underlying jobs (via `exit_status` property)
* bcftbx/Pipeline: update `Job` class to add new
  `update` method (checks job status and updates
  internals) and expose the exit code from the
  underlying job (as returned via the job runner)
  via `exit_code` property
* bcftbx/simple_xls: new `save_as_xlsx` method added
  to `XLSWorkBook` class, to enable output to XLSX
  format Excel files; new `freeze_panes` function
  added to `XLSWorkSheet` class
* ChIP-seq/make_macs2_xls.py: default output is now
  XLSX (use `--format` option to switch back to XLS)

----------------------------
Version 0.99.13 (2016-08-16)
----------------------------

* bcftbx/IlluminaData: updates to `IlluminaData` and
  `IlluminaFastq` classes to handle 'non-canonical'
  FASTQ file names (i.e. names which don't conform
  to Illumina naming scheme)
* bcftbx/IlluminaData: new function
  `samplesheet_index_sequence` (extracts barcodes
  from lines from `SampleSheet` objects)
* Add `HISeq4000` and `MiniSeq` to known platforms
  in `bcftbx/IlluminaData` and `bcftbx/platforms`.

----------------------------
Version 0.99.12 (2016-06-30)
----------------------------

* bcftbx/IlluminaData: new 'cycles' property for
  IlluminaRun class; update SampleSheet class to
  handle missing '[Data]' section in input file;
  improvements to IlluminaData class for handling
  bcl2fastq v2.* outputs.

----------------------------
Version 0.99.11 (2016-06-09)
----------------------------

* QC-pipeline/fastq_screen.sh: updated to handle output
  from `fastq_screen` v0.5.2.
* QC-pipeline/prep_sample_sheet.py 0.3.1: new options
  --set-adapter and --set-adapter-read2 allow updating
  of adapter sequences specified in IEM sample sheets.
* bcftbx/IlluminaData: new `sample_name_column`
  property added to the `SampleSheet` class.

----------------------------
Version 0.99.10 (2016-06-02)
----------------------------

* QC-pipeline/fastq_screen.sh & illumina_qc.sh: new
  --subset option allows explicit specification of
  subset size to be passed to fastq_screen (default
  is still 1000000, use 0 to use all reads as per
  fastq_screen 0.5.+)

---------------------------
Version 0.99.9 (2016-05-23)
---------------------------

* bcftbx/utils: fix pretty_print_names function, which
  was broken if consective sample name prefixes differed
  but their indices were consecutive.

---------------------------
Version 0.99.8 (2016-04-05)
---------------------------

* bcftbx/IlluminaData: fixes for IlluminaRun when the
  target directory doesn't exist; fixes for prediction
  and verification of IlluminaData against sample
  sheets for bcl2fastq v2 outputs using
  --no-lane-splitting option.
* bcftbx/mock: new module with classes for creating
  "mock" Illumina directories for testing (moved from
  the unit tests).

---------------------------
Version 0.99.7 (2016-04-01)
---------------------------

* bcftbx/IlluminaData: fixes for "illegal" name and
  ID detection and mitigation in IEM samplesheets;
  fixes to handle of outputs from bcl2fastq v2 in
  special cases when 'Sample_ID's and 'Sample_Name's
  are not consistent.

---------------------------
Version 0.99.6 (2016-01-19)
---------------------------

* Updates for handling sequencing data from NextSeq
  and bcl2fastq v2:
* bcftbx/IlluminaData: new generic SampleSheet
  class handles both IEM- and CASAVA-style sample
  sheets transparently; CasavaSampleSheet and
  IEMSampleSheet classes reimplemented as wrappers
  for SampleSheet.
* bcftbx/IlluminaData: IlluminaRun class updated
  to handle NextSeq output.
* bcftbx/IlluminaData: IlluminaData, IlluminaProject,
  IlluminaSample and IlluminaFastq classes updated
  to handle outputs from bcl2fastq v2.
* prep_sample_sheet.py: handles both IEM and CASAVA
  style sample sheets; use -f/--format option to
  convert one to the other.

---------------------------
Version 0.99.5 (2016-01-04)
---------------------------

* extract_reads.py: updated to use a more efficient
  method for reading data from input files.
* bcftbx/FASTQFile: FastqIterator updated to use
  a more efficient method for reading data from
  FASTQ files.
* bcftbx/qc/report: updated to handle special case
  for Illumina data where the input FASTQ is empty
  (i.e. has no reads) so there are no QC outputs.

---------------------------
Version 0.99.4 (2015-11-19)
---------------------------

* changed package name to 'genomics-bcftbx' in
  setup.py.

---------------------------
Version 0.99.3 (2015-09-25)
---------------------------

* fetch_fasta.sh: fix bug when MD5 sum failed (e.g.
  if file was missing)
* extract_reads.py: updated to handle gzipped input
  files.

---------------------------
Version 0.99.2 (2015-08-05)
---------------------------

* Porting to Ubuntu: update Python scripts to use
  '#!/usr/bin/env python' and shell scripts to use
  '#!/bin/bash'
* bcftbx/TabFile: add switch to TabFile class to
  prevent type conversions when reading in data
* bcftbx/utils: new function 'get_hostname'.
* NGS-general/split_fasta.py: fixes to handle
  comments in sequence definition lines.

---------------------------
Version 0.99.1 (2015-04-16)
---------------------------

* First version which is installable via setup.py
* Significant rearrangement of various scripts and
  programs
* First version of sphinx-based documentation added
* First version of test scripts for SOLiD and
  Illumina QC scripts

------------------
Version 2015-02-12
------------------

* QC-pipeline/illumina_qc.sh

  - Version 1.2.2
  - Add --threads option (pass number of threads to
    use to fastq_screen and fastqc)

* QC-pipeline/fastq_screen.sh

  - Add --threads option (pass number of threads to
    use to fastq_screen command)

------------------
Version 2014-12-10
------------------

* utils/cmpdirs.py

  - Version 0.0.1
  - Version 0.0.2
  - Version 0.0.3
  - New program to recursively compare the contents
    of one directory against another.

------------------
Version 2014-12-04
------------------

* build-indexes/make_seq_alignments.sh

  - New script to create sequence alignment (.nib)
    files from a Fasta file.

------------------
Version 2014-12-03
------------------

* utils/symlink_checker.py

  - version 1.1.1
  - Add 'genomics' top-level directory to search path
    for Python modules.

------------------
Version 2014-10-31
------------------

* QC-pipeline/illumina_qc.sh

  - version 1.2.0
  - Default behaviour is not *not* to decompress fastq
    files, unless new '--ungzip-fastqs' option is
    specified (and existing option '--no-gzip-fastqs' now
    does nothing).
  - version 1.2.1
  - Added --version option.

------------------
Version 2014-10-14
------------------

* bcftbx/cmdparse.py

  - version 1.0.0
  - New module for creating 'command parsers', for
    processing command lines of the form 'PROG CMD OPTIONS
    ARGS'.

* bcftbx/JobRunner.py

  - version 1.1.0
  - New function 'fetch_runner', returns appropriate job
    runner instance matching text description (used for
    specifying job runners on command line or in config
    files).

------------------
Version 2014-10-10
------------------

* bcftbx/utils.py

  - version 1.5.0
  - New function 'list_dirs', gets subdirectories of
    specified parent directory.

* bcftbx/Solid.py

  - Updated 'SolidRun' class to handle cases where the
    run definition file is missing.

------------------
Version 2014-10-09
------------------

* bcftbx/Md5sum.py

  - version 1.1.0
  - 'md5sum' function updated to handle either file name,
     or a file-like object opened for reading.

* bcftbx/utils.py

  - version 1.4.8
  - New function 'get_current_user', gets name of
    user running the program.

------------------
Version 2014-10-08
------------------

* bcftbx/utils.py

  - version 1.4.7
  - New property 'resolve_link_via_parent' for PathInfo
    class, gets 'real' path from one that includes
    symbolic links at any level.

------------------
Version 2014-09-01
------------------

* bcftbx/qc/report.py

  - version 0.99.1
  - relocated QC reporting classes and functions from the
    qcreporter.py program into a new module in the bcftbx
    package.

* bcftbx

  - version 0.99.0
  - add a single version for the whole package, accessible
    using the 'bcftbx.get_version()' function.

* utils/md5checker.py

  - version 0.3.2
  - move unit tests into separate test module & remove --test
    option.

------------------
Version 2014-08-21
------------------

* bcftbx

  - Substantial update: Python library modules from 'share'
    relocated to 'bcftbx' and turned into a Python package.
  - 'bcf_utils.py' also renamed to 'bcftbx/utils.py'.
  - Python applications also updated to reflect the changes.

* microarray/best_exons.py

  - version 1.2.1
  - new program: averages data for 'best' exons for each gene
    symbol in a file.

------------------
Version 2014-08-15
------------------

* share/JobRunner.py

  - version 1.0.5
  - new 'ge_extract_args' property for GEJobRunner.

------------------
Version 2014-08-11
------------------

* share/Md5sum.py

  - version 1.0.1
  - fixed compute_md5sums function to handle broken links

------------------
Version 2014-06-16
------------------

* QC-pipeline/illumina_qc.sh

  - version 1.1.1
  - Need to specify the --extract option to work with FastQC

    0.11.2 (should be backwardsly compatible with 0.10.1).

* share/IlluminaData.py

  - version 1.1.5
  - 'get_casava_sample_sheet' needs to handle leading & trailing
    spaces in barcode sequences.

* share/bcf_utils.py

  - version 1.4.5
  - New function 'walk' traverses directory tree (wrapper for
    os.walk function).

------------------
Version 2014-06-04
------------------

* share/IlluminaData.py

  - version 1.1.4
  - Fix_bases_mask updated to handle situation when a single index
    sequence is supplied for dual index data.

* illumina2cluster/report_barcodes.py

  - version 0.0.2
  - Make reporting cutoff apply only to exact matches.
  
------------------
Version 2014-06-02
------------------

* illumina2cluster/prep_sample_sheet.py

  - version 0.2.1
  - New options --include-lanes and --truncate-barcodes allow
    selection of subset of lanes, and barcode sequences to be
    cut down.

------------------
Version 2014-05-22
------------------

* illumina2cluster/report_barcodes.py

  - New program: examine barcode sequences from one or more
    FASTQ files and report the most prevalent.

------------------
Version 2014-05-15
------------------

* utils/manage_seqs.py

  - New program: utility to handle sets of named sequences;
    intended to help manage custom 'contaminants' files for input
    into the Brabaham 'FastQC' program.

------------------
Version 2014-05-07
------------------

* QC-pipeline/illumina_qc.sh

  - version 1.1.0
  - Optionally use a non-default list of contaminants for
    FastQC (if specified in the qc.setup file)
  - Create and set a local tmp directory for Java when
    running FastQC.
  - New --no-gunzip option suppresses creation of uncompressed
    fastq files.

* share/bcf_utils.py

  - version 1.4.4
  - New functions for getting user and group names and ID numbers
    from the system.
  - New 'PathInfo' class for getting information about file system
    paths.
  - Moved symbolic link handling classes and functions in from
    utils/symlink_checker.py program.
  - 'format_file_sizes' function updated to format to specific
    units, and able to handle terabyte sizes.
  - new function 'find_program'.

* share/htmlpagewriter.py

  - version 1.0.0
  - New module: HTML page generation functionality relocated from
    the QC-pipeline/qcreporter.py utility.

* share/IlluminaData.py

  - version 1.1.3
  - Move 'describe_project', 'summarise_projects' and
    'verify_run_against_sample_sheet' functions from
    illumina2cluster/analyse_illumina_run.py into this
    module.

* share/JobRunner.py

  - version 1.0.4
  - fix broken 'terminate' method for SimpleJobRunner.
  - move set/get of log directory into the BaseJobRunner
    class.

* share/Md5sum.py

  - Moved Md5Checker and Md5Reporter classes from
    utils/md5checker.py program.
  
* share/Pipeline.py

  - version 0.1.3
  - add 'runner' property to Job class (to access associated
    JobRunner instance).

* share/platforms.py

  - added additional platforms and new function 'list_platforms'

* utils/md5checker.py

  - version 0.3.0
  - substantial refactoring of code to add unit tests;
    core functions and classes moved to the share/Md5sym.py
    module.

* utils/symlink_checker.py

  - version 1.1.0
  - refactored to add unit tests and move core functions and
    classes to share/bcf_utils.

* utils/uncompress_fastqz.sh

  - New utility script for uncompressing fastq files.
  

------------------
Version 2014-04-17
------------------

* ChIP-seq/make_macs2_xls.py

  - version 0.3.2
  - Only sort output on fold enrichment
  - Handle output from --broad option of MACS2
  - Split data over multiple sheets if row limit is exceeded
    (approx 64k records)
  - Prevent reported command line being truncated if maximum
    cell size is exceeded (approx 250 characters)
  - Refactored internals to make more robust, added unit
    tests and switched to use simple_xls module for
    spreadsheet generation.

------------------
Version 2014-04-10
------------------

* RNA-seq/bowtie_mapping_stats.py

  - version 1.1.5
  - Updated to handle paired-end output from Bowtie2

------------------
Version 2014-04-09
------------------

* share/simple_xls.py

  - version 0.0.7
  - New methods for inserting and appending columns and rows,
    which better mimic operations that would be used within a
    graphical spreadsheet program.
  - Significant updates to handling internal book-keeping to
    improve performance.

------------------
Version 2014-04-04
------------------

* RNA-seq/bowtie_mapping_stats.py

  - version 1.1.3
  - Updated, now works with output from both Bowtie and Bowtie2
  
* share/simple_xls.py

  - version 0.0.3
  - New module intended to provide a nicer programmatic interface
    to Excel spreadsheet generation (built on top of
    Spreadsheet.py).

------------------
Version 2014-02-11
------------------

* share/JobRunner.py

  - version 1.0.2
  - SimpleJobRunner: 'join_dirs' option joins stderr to stdout
  - GEJobRunner: jobs in 't' (transferring) and 'qw'
    (queued-waiting) states counted as "running"
  - GEJobRunner: arbitrary qsub arguments can be specified via
    'ge_extra_args' option

* share/SpreadSheet.py

  - version 0.1.8: add support for additional style options
    ('font_height', 'centre', 'shrink_to_fit')

* share/bcf_utils.py

  - version 1.0.3
  - New function 'find_program' (locate file on PATH)
  - New function 'name_matches' (simple pattern matching for project
    and sample names, moved from analyse_illumina_data.py)
  - New class 'AttributeDictionary'
  - New class 'OrderedDictionary'
  - New function 'touch' (creates new empty file)

* QC-pipeline/illumina_qc.sh

  - Gunzip fastq.gz files via temporary name, to avoid partial
    fastqs left behind if script terminates prematurely
  - Write program version information to 'qc' subdirectory

* QC-pipeline/fastq_screen.sh

  - Clean up existing files from previous incomplete run

* QC-pipeline/qcreporter.py

  - version 0.1.1
  - QCSample: 'fastqc' method made into a property

* share/Pipeline.py

  - version 0.1.2
  - Job class: add 'wait' method (waits for job to complete)
  - PipelineRunner: 'max_concurrent_jobs' now applies only to
    pipeline instance (i.e. not across all pipelines)
  - PipelineRunner: implemented __del__ method to clean up
    running pipeline instance (i.e. terminate running jobs)

* share/IlluminaData.py

  - version 1.1.2
  - New function 'fix_bases_mask' (adjust bases mask to match
    actual barcode sequence lengths, for bclToFastq)

* ChIP-seq/make_macs_xls.sh

  - Removed (redundant wrapper script to make_macs_xls.py)

* Unit tests

  - Python unit tests moved into separate files in 'share'

------------------
Version 2013-11-18
------------------

* build-indexes/fetch_fasta.sh

  - Neurospora crassa (Ncrassa) updated to June 25th 2013
    version.

* build-indexes/bowtie2_build_indexes.sh

  - New: wrapper script to build bowtie2 indexes from a
    fasta file.

* build-indexes/build_indexes.sh

  - remove bfast indexes & add bowtie2.

------------------
Version 2013-11-15
------------------

* build-indexes/fetch_fasta.sh

  - various builds renamed to longer & more accurate names:
    * hg18    -> hg18_random_chrM
    * hg19    -> hg19_GRCh37_random_chrM
    * mm9     -> mm9_random_chrM_chrUn
    * mm10    -> mm10_random_chrM_chrUn
    * dm3     -> dm3_het_chrM_chrU
    * ecoli   -> e_coli
    * dicty   -> dictyostelium
    * chlamyR -> Creinhardtii169
  - updates to broken download URLs and checksums for PhiX,
    sacBay, ws200 and ws201 genome builds.
  - UniVec updated to build #7.1.

------------------
Version 2013-11-13
------------------

* build-indexes/fetch_fasta.sh

  - updated to include sacCer1, sacCer3 and mm10 sequences.
  - updated URL for C. reinhardtii.
  - fixed minor bug in 'fetch_url' function.

------------------
Version 2013-09-11
------------------

* share/IlluminaData.py

  - version 1.1.1: update get_casava_sample_sheet function to
    handle "Experimental Manager"-type sample sheet files when
    there are no barcode indexes.

* share/JobRunner.py

  - version 1.0.1: fix and standardise handling of log and error
    files for SimpleJobRunner and GEJobRunner classes; also added
    minimal unit tests for these classes.

------------------
Version 2013-09-09
------------------

* share/FASTQFile.py

  - version 0.3.0: attempt to improve performance of
    SequenceIdentifier class (use string parsing instead of
    regular expressions), and added new method 'is_pair_of'
    (can be used to check if another SequenceIdentifier forms
    an R1/2 pair with this one). FastqRead class has new attribute
    'raw_seqid' (returns original sequence id header supplied on
    instantiation). New function 'fastqs_are_pair' checks that
    corresponding read headers match between two FASTQ files.

* illumina2cluster/verify_paired.py

  - version 1.0.0: new utility to check that two fastq files form
    an R1/R2 pair.

* illumina2cluster/analyse_illumina_run.py

  - version 0.1.11: updated implementation of --merge-fastqs option.

* illumina2cluster/check_paired_fastqs.py

  - Removed: replaced by 'verify_paired.py'.

* share/JobRunner.py

  - version 1.0.1: updates to SimpleJobRunner and GEJobRunner classes
    (store names associated with each job, and enable lookup via 'name'
    method; ensure stored log directory is an absolute path, and that
    log and error file names can be retrieved correctly even if log dir
    is subsequently changed).

------------------
Version 2013-09-06
------------------

* illumina2cluster/analyse_illumina_run.py

  - version 0.1.9: improvements to reporting options when using
    --summary and --list options.
  - version 0.1.10: fix bug for runs that don't have undetermined
    indices.

* share/IlluminaData.py

  - version 1.0.2: new method 'fastq_subset' for IlluminaSample
    (returns subset of fastq files based on read number).

------------------
Version 2013-08-22
------------------

* share/bcf_utils.py:

  - version 1.0.1: added new function 'concatenate_fastq_files'
    (concatenates a list of fastq files).
  - version 1.0.2: updated 'concatenate_fastq_files' to improve
    performance, and added tests.

* illumina2cluster/analyse_illumina_run.py

  - version 0.1.8: new option --merge-fastqs, creates
    concatenated fastq files for each sample.

* share/IlluminaData.py

  - version 1.0.1: new property 'full_name' for IlluminaData,
    (returns name suitable for analysis subdirectory); new
    function 'get_unique_fastq_names' (generates mapping of
    full Illumina-style fastq file names to shortest unique
    version).

* illumina2cluster/build_illumina_analysis_dir.py

  - version 1.0.1: move analysis directory creation code from
    __main__ to new 'create_analysis_dir' function.
  - version 1.0.2: remove redundant functions and switch to
    versions in bcf_utils module.

------------------
Version 2013-08-21
------------------

* share/bcf_utils.py

  - added baseline version number (1.0.0)

* illumina2cluster/build_illumina_analysis_dir.py

  - added baseline version number (1.0.0)

------------------
Version 2013-08-20
------------------

* share/IlluminaData.py, JobRunner.py

  - added version numbers (baseline 1.0.0)

* share/FASTQFile.py

  - version 0.2.6: fix sequence length returned for
    colorspace reads by FastqRead.seqlen
  - version 0.2.5: added is_colorspace property to FastqRead

------------------
Version 2013-08-19
------------------

* illumina2cluster/prep_sample_sheet.py:

  - version 0.2.0: --miseq option is deprecated as it's no
    longer necessary; sample sheet conversion is performed
    automatically if required.

* illumina2cluster/IlluminaData.py:

  - new function 'get_casava_sample_sheet' produces a
    CasavaSampleSheet object from sample sheet CSV file
    regardless of format. 'convert_miseq_samplesheet_to_casava'
    is deprecated as it is now just a wrapper to the more
    genral function.

* share/FASTQFile.py

  - version 0.2.4: added new properties to FastqRead: seqlen
    (return sequence length), maxquality and minquality (max
    and min encoded quality scores).

------------------
Version 2013-08-14
------------------

* share/FASTQFile.py

  - version 0.2.3: new FastqAttributes class provides
    access to "gross" attributes of FASTQ file (e.g. read
    count, file size).

* share/JobRunner.py

  - SimpleJobRunner and GEJobRunner classes allow destination
    directory for log files to be specified explicitly, and
    to be changed after instantiation via new 'log_dir' methods.
  - GEJobRunner class has new 'queue' method allowing GE queue
    to be changed after instantiation.

------------------
Version 2013-08-08
------------------

* illumina2cluster/analyse_illumina_run.py

  - version 0.1.7: --summary option generates a one-line
    description of projects and numbers of samples, suitable
    for logging file entries.

------------------
Version 2013-08-05
------------------

* share/IlluminaData.py

  - new classes IlluminaRun (extracts data from a directory
    with the "raw" data from a sequencer run) and
    IlluminRunInfo (extracts data from a RunInfo.xml file).

* share/platforms.py

  - new Python module with utilities and data to identify NGS
    sequencer platforms
  
* illumina2cluster/rsync_seq_data.py

  - version 0.0.5: moved sequencer platform identification
    code to share/platforms.py
  - version 0.0.4: new options --no-log (write rsync ouput
    directly to stdout) and --exclude (specify rsync filter
    patterns to exclude files from transfer); explicitly
    handle keyboard interrupt (i.e. ctrl-C) during rsync
    operation.

------------------
Version 2013-08-01
------------------

* illumina2cluster/rsync_seq_data.py

  - version 0.0.3: added new hiseq sequencer pattern to
    PLATFORMS.

------------------
Version 2013-07-26
------------------

* illumina2cluster/rsync_seq_data.py

  - version 0.0.2: add --mirror option, runs rsync with
    --delete-after option to remove files from target directory
    which are no longer present in the source.

* share/Spreadsheet.py

  - version 0.1.7: fixed bug which meant formulae generation
    failed for columns after 'Z' (i.e. 'AA', 'AB' etc).

------------------
Version 2013-07-19
------------------

* ChIP-seq/make_macs2_xls.py

  - modified version of make_macs_xls.py to convert XLS output
    files from MACS 2.0.10 (contributed by Ian Donaldson).

------------------
Version 2013-07-15
------------------

* illumina2cluster/rsync_seq_data.sh

  - removed, replaced by rsync_seq_data.py.

* illumina2cluster/rsync_seq_data.py

  - version 0.0.1: new program for rsync'ing sequencing data to
    the appropriate location in the archive.

* utils/cluster_load.py

  - new utility for reporting current Grid Engine utilisation by
    wrapping the qstat program.

------------------
Version 2013-05-21
------------------

* illumina2cluster/auto_process_illumina.sh

  - version 0.2.4: use multiple cores for bcl-to-fastq conversion.

* share/IlluminaData.py

  - IlluminaSample class no longer raises an exception if no fastq
    files are found, so IlluminaData objects can be populated from
    an incomplete CASAVA run.

* illumina2cluster/build_illumina_analysis_dir.py

  - automatically determine the set of shortest unique link names
    to use for fastqs in each project.

------------------
Version 2013-05-20
------------------

* illumina2cluster/bclToFastq.sh

  - New option --nprocessors allows specification of number of
    cores to utilise when performing bcl to Fastq conversion.

------------------
Version 2013-05-17
------------------

* illumina2cluster/auto_process_illumina.sh

  - version 0.2.3: fix bug with extracting the exit code from the
    CASAVA/bcl2fastq step.

* share/FASTQFile.py

  - version 0.2.1: implement more efficient line counting in nreads
    function.

* illumina2cluster/analyse_illumina_run.py

  - version 0.1.4: print results from --stats option in real time.

------------------
Version 2013-05-15
------------------

* illumina2cluster/auto_process_illumina.sh

  - version 0.2.2: fix automatic determination of number of allowed
    mismatches from the bases mask, to deal with e.g. 'I6n'

------------------
Version 2013-05-02
------------------

* illumina2cluster/auto_process_illumina.sh

  - version 0.2.1: write log files to "logs" subdirectory.

------------------
Version 2013-05-01
------------------

* illumina2cluster/auto_process_illumina.sh

  - version 0.2.0: updated to work with multiple sample sheets.

------------------
Version 2013-04-25
------------------

* illumina2cluster/auto_process_illumina.sh

  - version 0.1.0: significant updates to improve robustness, automatically
    acquire mismatches and generate statistics report.

* ilumina2cluster/analyse_illumina_run.py

  - version 0.1.2: also report file sizes as well as number of reads for
    Fastq files using --stats option.

* share/bcf_utils.py

  - new function "format_file_size" (converts file size supplied in bytes
    into human-readable form e.g. 4.0K, 186.0M, 1.6G).

------------------
Version 2013-04-24
------------------

* share/bcf_utils.py

  - fix bug in extract_index (failed for names ending with 0 e.g. 'PJB0').

------------------
Version 2013-04-23
------------------

* ilumina2cluster/analyse_illumina_run.py

  - version 0.1.1: added --stats option (reports number of reads for each
    FASTQ file generated by CASAVA's bcl-to-FASTQ conversion).

* share/IlluminaData.py

  - IlluminaData class has new property "undetermined" (allows access to
    undetermined reads produced by demultiplexing).
  - IlluminaProject.prettyPrintSamples() no longer includes info on paired
    endedness of the data in the project.

------------------
Version 2013-04-22
------------------

* illumina2cluster/auto_process_illumina.sh

  - new script to automate processing of sequencing data from Illumina
    platforms.

------------------
Version 2013-04-16
------------------

* QC-pipeline/run_qc_pipeline.py

  - fix bug with --queue option which meant queue specification was not
    being honoured by the program.

------------------
Version 2013-04-11
------------------

* illumina2cluster/analyse_illumina_run.py

  - version 0.1.0: new option --verify=SAMPLE_SHEET, verifies outputs
    against those predicted by the named sample sheet.

* share/IlluminaData.py

  - CasavaSampleSheet class:

    1. In "duplicated_names" method, now considers index and lane number
       as well as SampleID and SampleProject in determining uniqueness.

    2. New method "predict_output", returns a data structure describing
       the expected project/sample/base file name hierarchy that would be
       created using the sample sheet.

    3. Added 'paired_end' attribute to the IlluminaData and
       IlluminaProject classes.

* illumina2cluster/prep_sample_sheet.py

  - version 0.1.0: renamed from 'update_sample_sheet.py'
  - version 0.1.1: print predicted outputs for the input sample sheet.

* illumina2cluster/update_sample_sheet.py

  - renamed to 'prep_sample_sheet.py'

* illumina2cluster/demultiplex_undetermined_fastq.py

  - new program: reassign reads with undetermined index sequences (i.e.
    barcodes) from the FASTQ files in the 'Undetermined_indices'
    output directory from CASAVA.

------------------
Version 2013-04-10
------------------

* QC-pipeline/qcreporter.py

  - version 0.1.0: added version number, and write this to report header
    along with date and time of report generation.
  - put the per-base quality boxplot from FastQC into the top-level
    report.

* share/IlluminaData.py

  - CasavaSampleSheet class: automatically remove double quotes from
    around sample sheet values upon reading.

------------------
Version 2013-04-09
------------------

* share/FASTQFile.py

  - version 0.2.0: added tests, new function "nreads" (counts reads in
    FASTQ), and enabled FastqIterator to read data from an open
    file-like object.

------------------
Version 2013-04-08
------------------

* share/IlluminaData.py

  - updated IlluminaProject class: allow "Undetermined_indices" dir to
    also be treated as a "project" within the class framework.

* illumina2cluster/analyse_illumina_run.py

  - added --copy option, to copy specific FASTQ files to pwd.

------------------
Version 2013-04-05
------------------

* QC-pipeline/qcreporter.py

  - new --regexp option allows selection of a subset of samples based on
    regular expression pattern matching e.g. --regexp=SY[1-4]?_trim

------------------
Version 2013-03-13
------------------

* share/JobRunner.py

  - update GEJobRunner and DRMAAJobRunner classes to deal with suspended
    jobs.

* share/FASTQFile.py

  - version 0.1.2: update FastqRead class to operate in a more efficient
    "lazy" fashion.

------------------
Version 2013-03-07
------------------

* utils/fastq_sniffer.py

  - new utility to identify likely FASTQ file format, quality encoding
    and equivalent Galaxy data type.

------------------
Version 2013-02-19
------------------

* utils/extract_reads.py

  - version 0.1.3: fix bug handling fastq files, was confused by quality
    lines beginning with '#' character.

------------------
Version 2013-02-18
------------------

* illumina2cluster/update_sample_sheet.py

  - fix bug in --set-id option which misidentified lanes by their number.

------------------
Version 2013-01-29
------------------

* illumina2cluster/update_sample_sheet.py

  - new option --miseq indicates input sample sheet is in MiSeq format,
    (which will be converted to CASAVA format on output).

* share/IlluminaData.py

  - update convert_miseq_samplesheet_to_casava to handle paired-end MiSeq
    sample sheet.
  - add new attribute "paired_end" to IlluminaSample objects, to indicate
    whether the sample has paired end data.

* illumina2cluster/build_illumina_analysis_dir.py

  - deal correctly with linking to paired end Fastq files.

------------------
Version 2013-01-25
------------------

* share/IlluminaData.py

  - fix bug in convert_miseq_samplesheet_to_casava (always wrote empty
    sample sheet).

------------------
Version 2013-01-24
------------------

* share/FASTQFile.py

  - version 0.1.0: "casava" format now renamed to "illumina18", for
    consistency with FASTQ information at
    http://en.wikipedia.org/wiki/FASTQ_format
  - version 0.1.1: fixed failure to read Illumina 1.8+ files that are
    missing barcode sequences in the identifier string.

------------------
Version 2013-01-23
------------------

* share/IlluminaData.py

  - new class CasavaSampleSheet for handling sample sheet files for input
    into CASAVA.
  - new function convert_miseq_samplesheet_to_casava for creating CASAVA
    style sample sheet from one from a MiSEQ sequencer.

* illumina2cluster/update_sample_sheet.py

  - updated to use the CasavaSampleSheet class from IlluminaData.py.

------------------
Version 2013-01-22
------------------

* share/FASTQFile.py

  - version 0.0.2: enable FastqIterator to operate on gzipped FASTQ input.

------------------
Version 2013-01-21
------------------

* utils/split_fasta.py

  - version 0.1.0: substantial rewrite to enable the core functionality
    to be unit tested.

* utils/extract_reads.py

  - version 0.1.2: cosmetic updates to comments etc only.

------------------
Version 2013-01-18
------------------

* utils/split_fasta.py

  - new utility for splitting Fasta file into individual chromosomes.

------------------
Version 2013-01-14
------------------

* QC-pipeline/qcreporter.py

  - new option --verify: reports if all expected outputs from the QC
    pipeline exist for each sample, to check that the pipeline ran to
    completion.

------------------
Version 2013-01-10
------------------

* QC-pipeline/fastq_stats.sh

  - fix bug in sorting stats file, now header lines should always sort to
    the top of the file.

* illumina2cluster/analyse_illumina_run.py

  - first version of reporting utility for Illumina data, similar to the
    "analyse_solid_run.py" in solid2cluster.

* illumina2cluster/build_illumina_analysis_dir.py

  - moved --list and --report functions to new analyse_illumina_data.py
    utility.

* solid2cluster/analyse_solid_run.py

  - only print paths to primary data files if --report-paths option is
    specified
  - print timestamps for primary data files along with sample names
  - --quiet option renamed to --no-warnings

  
------------------
Version 2013-01-09
------------------

* illumina2cluster/build_illumina_analysis_dir.py

  - moved classes for handling Illumina data to IlluminaData.py, and take
    other utility functions from bcf_utils.py

* share/Experiment.py

  - moved utility functions to bcf_utils.py module

* share/IlluminaData.py

  - new Python module containing classes for handling Illumina-based
    sequencing data, extracted from build_illumina_analysis_dir.py.

* share/bcf_utils.py

  - new Python module containing common utility functions shared between
    sequencing data modules, extracted from Experiment.py.

------------------
Version 2013-01-07
------------------

* illumina2cluster/build_illumina_analysis_dir.py

  - add --report option to pretty print sample names within each project.

------------------
Version 2012-12-06
------------------

* NGS-general/boxplotps2png.sh

  - utility to generate PNGs from PS boxplots generated by qc_boxplotter.
  
* QC-pipeline/qcreporter.py

  - updated to deal with reporting QC for older SOLiD runs which predate
    filtering (so there are just boxplots and fastq_screens).

------------------
Version 2012-11-27
------------------

* QC-pipeline/qcreporter.py

  - added --qc_dir option to specify a non-default QC directory.

------------------
Version 2012-11-26
------------------

* illumina2cluster/rsync_seq_data.sh

  - utility script wrapping rsync command for copying arbitrary sequence
    data directories.

* illumina2cluster/update_sample_sheet.py

  - check for empty sampleID and SampleProject names.

* QC-pipeline/illumina_qc.sh

  - add --nogroup option to FastQC invocation.
  - remove ".fastq" from output log file names when running with fastq.gz
    input files.

* illumina2cluster/build_illumina_analysis_dirs.py

  - make relative (rather than absolute) symbolic links to source fastq files
    when building analysis directories.

------------------
Version 2012-11-16
------------------

* utils/fastq_edit.py

  - version 0.0.2: added --stats option to generate simple statistics
    about input FASTQ file.

------------------
Version 2012-11-13
------------------

* illumina2cluster/bclToFastq.sh

  - added --nmismatches options (passes number of allowed mismatches to
    the underlying configureBclToFastq.pl script in CASAVA).

-------------------
Version 42012-11-01
-------------------

* utils/symlink_checker.py

  - new utility for checking and updating (broken) symbolic links.

* QC-pipeline/qcreporter.py

  - added --format option (explicitly specify format of base input files if
    necessary) and updated automatic platform and data type detection.

* share/Spreadsheet.py

  - version 0.1.6: Workbook class issues warning when appending to an existing
    XLS file (previously warned when creating a new file)

------------------
Version 2012-10-31
------------------

* illumina2cluster/update_sample_sheet.py

  - new option --fix-duplicates automatically deals with duplicated
    SampleID/SampleProject combinations; using --fix-duplicates and
    --fix-spaces together should deal with most sample sheet problems
    without requiring further intervention.

------------------
Version 2012-10-18
------------------

* solid2cluster/analyse_solid_run.py

  - --layout option now defaults to 'absolute' links to primary data in generated
    script.

* solid2cluster/build_analysis_dir.py

  - default is now to make absolute links to primary data files

------------------
Version 2012-10-16
------------------

* illumina2cluster/update_sample_sheet.py

  - added --ignore-warnings option (forces output sample sheet file to
    be written out even if there are errors)

------------------
Version 2012-10-15
------------------

* illumina2cluster/bclToFastq.sh

  - added --use-bases-mask option (passes mask specification to the underlying
    configureBclToFastq.pl script in CASAVA).

* illumina2cluster/build_illumina_analysis_dir.py

  - added new options --keep-names (preserve the full names of the source fastq
    files when creating links) and --merge-replicates (create merged fastq files
    for each set of replicates detected).

------------------
Version 2012-10-03
------------------

* QC-pipeline/run_qc_pipeline.py

  - added --regexp option to allow filtering of input file names.

* QC-pipeline/solid_qc.sh, illumina_qc.sh

  - write data about underlying QC programs (including versions) to
    <sample>.programs output files.

* QC-pipeline/qcreporter.py

  - report QC program information from <sample>.programs files (if
    available).


  - output ZIP file has run/sample-specific top-level directory; HTML
    report file name restored to 'qc_report.html'.

------------------
Version 2012-10-01
------------------

* QC-pipeline/qcreporter.py

  - fixed bug for correctly allocating screens to samples
  - added --platform option to explicitly specify platform type
  - output HTML and ZIP file names now of the form qc_report.<run>.<name>

* solid2cluster/build_analysis_dir.py, illumina2cluster/build_illumina_analysis_dir.py

  - create empty "ScriptCode" subdirectories for each analysis directory,
    for bioinformaticians to store project-specific scripts and code etc.

------------------
Version 2012-09-28
------------------

* utils/md5checker.py

  - version 0.2.3: explicitly report if either of the inputs doesn't exist in
    -d/--diff mode.

* solid2cluster/log_solid_run.sh

  - renamed to log_seq_data.sh

* illumina2cluster/build_illumina_analysis_dir.py

  - fix bug that resulted in broken links being generated.

------------------
Version 2012-09-24
------------------

* solid2clusteranalyse_solid_run.py

  - new option --md5=... generates checksums for specified primary data files
    (offering more fine-grained control than --md5sum option).

------------------
Version 2012-09-18
------------------

* solid2cluster/analyse_solid_run.py

  - new option --gzip=... creates compressed versions of specified primary data
    files for transfer.

* share/TabFile.py

  - version 0.2.6: TabFile.append and TabFile.insert methods updated to allow
    arbitrary TabDateLine objects to be added to the TabFile object.

------------------
Version 2012-09-17
------------------

* share/SolidData.py

  - add SolidRun.verify method to check run integrity

* solid2cluster/analyse_solid_run.py

  - use SolidRun.verify method to check SOLiD runs

------------------
Version 2012-09-13
------------------

* illumina2cluster/update_sample_sheet.py

  - added checks for duplicated SampleID/SampleProject combinations & spaces
    in names, and refuse to write new SampleSheet containing either of these
    features.
  - new option --fix-spaces will automatically replace spaces with underscores
    in SampleID and SampleProject fields.

* illumina2cluster/build_illumina_analysis_dir.py

  - updated to allow for possibility of more than one fastq.gz file per
    sample directory
  - new option --unaligned=... allows alternative name to be specified for the
    "Unaligned" subdirectory holding fastq.gz files.

* share/TabFile.py

  - version 0.2.5: implement __nonzero__ built-in for TabDataLine to enable
    easy test for whether a line is blank.

------------------
Version 2012-09-11
------------------

* utils/md5checker.py

  - version 0.2.2: added unit tests (run using --test option); fixed exit
    code for -d/--diff mode if broken or missing files are encountered.

------------------
Version 2012-08-30
------------------

* utils/md5checker.py

  - version 0.2.1: -d/--diff mode now compares files in pairwise fashion;
    reports "missing" files as part of the total number of files checked;
    also reports "broken" source files which cannot be checksummed.

------------------
Version 2012-08-24
------------------

* share/SolidData.py

  - updates to SolidLibrary allows access to all primary data associated
    with a sample/library, via new SolidLibrary.primary_data property
    (which holds a list of SolidPrimaryData objects referencing CSFASTA
    QUAL file pairs plus timestamp information).
  - added basic support for locating 'unassigned' read files for each
    sample: each SolidSample object has an associated unassigned
    SolidLibrary.

------------------
Version 2012-08-23
------------------

* share/SolidData.py

  - SolidRun class updated to handle situations where SOLiD run directory
    names differ from the run names (e.g. because the directory has been
    renamed)
  - New function 'list_run_directories' gets matching SOLiD run directory
    names

* solid2cluster/analyse_solid_run.py

  - new option --copy can be used to copy selected primary data files from
    a run (useful if preparing data for transfer)

* illumina2cluster/build_illumina_analysis_dirs.py

  - new utility to query/build analysis directories for Illumina GA2
    sequencing data post bcl-to-fastq conversion

------------------
Version 2012-08-15
------------------

* illumina2cluster/update_sample_sheet.py

  - new utility for editing Illumina GA2 SampleSheet.csv files before
    running bcl to fastq conversion

------------------
Version 2012-08-07
------------------

* ChIP-seq/make_macs_xls.py

  - version 0.1.0: fixed to handle output from MACS 1.4.2 (backwards
    compatible with output from other version of MACS)

------------------
Version 2012-08-03
------------------

* QC-pipeline/qcreporter.py

  - new utility to generate HTML reports for SOLiD and Illumina QC
    script runs

------------------
Version 2012-07-27
------------------

* shared/TabFile.py

  - version 0.2.4: allow TabFile.computeColumn() to reference
    destination columns by integer indices as well as by column name

------------------
Version 2012-07-24
------------------

* shared/TabFile.py

  - version 0.2.3: TabFile can now handle user-defined delimiters (not
    just tabs) for reading and writing; new TabFile.transpose() method
    converts columns to rows

------------------
Version 2012-07-05
------------------

* utils/md5checker.py

  - version 0.1.2: explicitly report missing files separately from
    checksum failures

------------------
Version 2012-07-02
------------------

* RNA-seq/bowtie_mapping_stats.py

  - version 0.1.6: for multiple input files, add the filename to the
    sample number in the output file

------------------
Version 2012-06-29
------------------

* illumina2cluster/bclToFastq.sh

  - Bcl to Fastq conversion wrapper script for Illumina sequencing data

* QC-pipeline

  - new script illumina_qc.sh implements QC pipeline for Illumina data
  - qc.sh renamed to solid_qc.sh

------------------
Version 2012-06-25
------------------

* share/TabFile.py

  - version 0.2.1: TabDataLine now preserves the type of non-numeric
    data items (previously they were automatically converted to strings)

------------------
Version 2012-06-22
------------------

* utils/md5checker.py

  - version 0.1.1: reports 'bad' MD5 sum lines; can now handle file
    names containing whitespace

------------------
Version 2012-06-13
------------------

* build-indexes/bowtie_build_indexes.sh

  - added --cs and --nt options (build only color- or nucleotide
    space indexes)

* build-indexes/fetch_fasta.sh

  - updated UniVec for build 7.0 (Dec. 5 2011)

------------------
Version 2012-06-01
------------------

* QC-pipeline/qc.sh

  - updated to run in either 'single end' mode (operate on one F3 or
    F5 csfasta/qual pair) or 'paired end' mode (operate on F3
    csfasta/qual pair plus csfasta/qual F5 pair)

* QC-pipeline/cleanup_qc.sh

  - utility to clean up all QC products from current directory

------------------
Version 2012-05-17
------------------

* NGS-general/remove_mispairs.py

  - Python implementation of remove_mispairs.pl works with
    non-interleaved any fastq

------------------
Version 2012-05-10
------------------

* NGS-general

  - New utilities from Ian Donaldson:
  - remove_mispairs.pl: remove "singleton" reads from paired end fastq
  - separate_paired_fastq.pl: separate F3 and F5 reads from fastq
  - trim_fastq.pl: trim down sequences in fastq file from 5' end

------------------
Version 2012-05-09
------------------

* microarray/xrothologs.py

  - cross-reference data for two species using probe set lookup

------------------
Version 2012-05-08
------------------

* RNA-seq/bowtie_mapping_stats.py

  - summarise statistics from bowtie output into XLS spreadsheet

------------------
Version 2012-05-03
------------------

* utils/sam2soap.py

  - first version of SAM to SOAP converter

