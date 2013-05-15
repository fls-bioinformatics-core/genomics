#!/bin/sh
#
# Automatically process Illumina-based sequencing run
#
AUTO_PROCESS_VERSION="0.2.2"
#
if [ $# -lt 1 ] || [ "$1" == "-h" ] || [ "$1" == "--help" ] ; then
    echo "Usage: $0 COMMAND [ PLATFORM DATA_DIR ]"
    echo ""
    echo "Automatically process data from an Illumina-based sequencing"
    echo "platform"
    echo ""
    echo "COMMAND can be one of:"
    echo ""
    echo "  setup: prepares a new analysis directory. This step must be"
    echo "         done first and requires that PLATFORM and DATA_DIR "
    echo "         arguments are also supplied (these do not have to be"
    echo "         specified for other commands)."
    echo "         This creates an analysis directory in the current dir"
    echo "         with a custom_SampleSheet.csv file; this should be"
    echo "         examined and edited before running the subsequent "
    echo "         steps."
    echo ""
    echo "  make_fastqs: runs CASAVA to generate Fastq files from the"
    echo "         raw bcls."
    echo ""
    echo "  run_qc: runs the QC pipeline and generates reports."
    echo ""
    echo "The make_fastqs and run_qc commands must be executed from the"
    echo "analysis directory created by the setup command."
    exit
fi
#
set +o noclobber
#
# Internal functions
# 
function log_step() {
    # Write a line to the logging file
    #
    # Usage: log_step STEP STATUS [ MESSAGE ]
    #
    # STEP:    name of the step e.g. Setup
    # STATUS:  e.g. STARTED, ERROR, FINISHED
    # MESSAGE: message text
    local timestamp=`date`
    local step_name=$1
    local step_status=$2
    local msg="$3"
    if [ ! -f processing.log ] ; then
	touch processing.log
    fi
    echo "[$timestamp]"$'\t'"$step_name"$'\t'"$step_status"$'\t'"$msg" >> processing.log
    if [ ! -z "$msg" ] ; then
	echo "$msg"
    fi
}
#
function store_info() {
    # Store key-value pair in info file
    #
    # Usage: store_info KEY VALUE
    local KEY="$1"
    local VALUE="$2"
    # Remove existing value
    grep -v "^${KEY}"$'\t' processing.info > tmp.processing.info 2>/dev/null
    /bin/mv tmp.processing.info processing.info
    # Write key-value pair
    echo ${KEY}$'\t'${VALUE} >> processing.info
}
#
function get_info() {
    # Retrieve value associated with key
    #
    # Usage: get_info KEY
    #
    # Returns the value(s) extracted from the info file
    local KEY="$1"
    echo $(grep ^${KEY}$'\t' processing.info | cut -f2)
}
#
function get_bases_mask() {
    # Read RunInfo.xml and return CASAVA-style bases mask string
    #
    # Usage: get_bases_mask RUN_INFO_XML
    #
    # RUN_INFO_XML: full path and name of RunInfo.xml file to read
    #
    # Returns a bases mask string for use in bcl to fastq
    # conversion e.g. y250,I8,I8,y250
    local run_info_xml=$1
    local bases_mask=
    while read line ; do
	read=$(echo $line | grep "<Read ")
	if [ ! -z "$read" ] ; then
	    numcycles=
	    indexread=
	    for field in $read ; do
		if [ -z "$numcycles" ] ; then
		    numcycles=$(echo $field | sed 's/\"//g' | grep "^NumCycles=" | cut -d= -f2)
		fi
		if [ -z "$indexread" ] ; then
		    indexread=$(echo $field | sed 's/\"//g' | grep "^IsIndexedRead=" | cut -d= -f2)
		fi
	    done
	    if [ "$indexread" == "N" ] ; then
		indexread="y"
	    else
		indexread="I"
	    fi
	    if [ ! -z "$bases_mask" ] ; then
		bases_mask="$bases_mask,"
	    fi
	    bases_mask="${bases_mask}${indexread}${numcycles}"
	fi
    done < $run_info_xml
    echo $bases_mask
}
#
function get_nmismatches() {
    # Determine optimum number of mismatches from bases mask
    #
    # Usage: get_mismatches BASES_MASK
    #
    # BASES_MASK is a string of the form y101,I8,I8,y85
    #
    # Returns 1 for index tags > 6, 0 otherwise
    local bases_mask=$1
    local tag_length=0
    # Loop over comma-separated elements in bases mask
    for mask in $(echo $bases_mask | sed 's/,/ /g') ; do
	# Is it an index read?
	index_read=$(echo $mask | grep I 2>/dev/null)
	if [ ! -z "$index_read" ] ; then
	    # Extract number of cycles/bases by deleting 'I'
	    # Also remove any trailing 'n' e.g. from I6n
	    test_tag_length=$(echo $index_read | sed 's/I//g' | sed 's/n[0-9]*//g')
	    if [ $test_tag_length -gt $tag_length ] ; then
		tag_length=$test_tag_length
	    fi
	fi
    done
    #
    if [ $tag_length -ge 6 ] ; then
	# One mismatch allowed
	echo 1
    else
	# No mismatches
	echo 0
    fi
}
#
# Functions for processing stages
#
function setup() {
    # Prepares data for processing
    # Make analysis dir
    if [ -d $ANALYSIS_DIR ] ; then
	echo ERROR Analysis dir $ANALYSIS_DIR already exists
	exit 1
    fi
    mkdir $ANALYSIS_DIR
    cd $ANALYSIS_DIR
    log_step Setup STARTED "*** Setting up analysis directory ***"
    log_step Setup INFO "$0 version $AUTO_PROCESS_VERSION"
    # Create standard subdirectories
    log_step Setup INFO "Making logs directory"
    mkdir logs
    cat > logs/README <<EOF
Directory holding logs from $0
EOF
    log_step Setup INFO "Making ScriptCode directory"
    mkdir ScriptCode
    cat > ScriptCode/README <<EOF
Directory holding custome scripts etc
EOF
    # Write info file
    store_info DATA_DIR $DATA_DIR
    store_info PLATFORM $PLATFORM
    store_info ANALYSIS_DIR $ANALYSIS_DIR
    log_step Setup INFO "Data dir $DATA_DIR"
    log_step Setup INFO "Platform $PLATFORM"
    # Locate initial sample sheet
    sample_sheet=
    multiple_sample_sheets=
    for f in $(ls $DATA_DIR/*.csv) ; do
	log_step Setup INFO "Found CSV file: $f"
	if [ ! -z "$sample_sheet" ] ; then
	    multiple_sample_sheets=yes
	    if [ $(basename $f) == "SampleSheet.csv" ] ; then
		sample_sheet=
	    fi
	fi
	if [ -z "$sample_sheet" ] ; then
	    sample_sheet=$f
	fi
    done
    if [ -z "$sample_sheet" ] ; then
	log_step Setup ERROR "No sample sheet found"
	exit 1
    fi
    if [ ! -z "$multiple_sample_sheets" ] ; then
	log_step Setup WARNING "Multiple csv files found"
    fi
    log_step Setup INFO "Source sample sheet: $sample_sheet"
    store_info SAMPLE_SHEET $sample_sheet
    # Create cleaned-up copy of sample sheet
    sample_sheet_cmd="prep_sample_sheet.py --fix-spaces --fix-duplicates --fix-empty-projects"
    if [ $PLATFORM == "miseq" ] ; then
	sample_sheet_cmd="$sample_sheet_cmd --miseq"
    fi
    sample_sheet_cmd="$sample_sheet_cmd -o custom_SampleSheet.csv $sample_sheet"
    log_step INFO "Running command: $sample_sheet_cmd"
    $sample_sheet_cmd
    if [ ! -f "custom_SampleSheet.csv" ] ; then
	log_step Setup ERROR "Failed to create sample sheet copy"
	exit 1
    fi
    # Determine bases mask
    run_info_xml=$DATA_DIR/RunInfo.xml
    if [ ! -f $run_info_xml ] ; then
	log_step Setup ERROR "No file $run_info_xml"
	exit 1
    else
	store_info RUN_INFO_XML $run_info_xml
	log_step Setup INFO "Getting bases mask from $run_info_xml"
        bases_mask=$(get_bases_mask $run_info_xml)
	store_info BASES_MASK $bases_mask
	log_step Setup INFO "Bases mask from RunInfo.xml: $bases_mask"
    fi
    # Define the default processing run
    store_info DEFINE_RUN custom_SampleSheet.csv:Unaligned:$bases_mask
    # Finish this step
    log_step Setup FINISHED "Setup completed ok"
}
#
function make_fastqs() {
    # Generates fastq files with CASAVA
    log_step Make_fastqs STARTED "*** Generating fastq files ***"
    log_step Make_fastqs INFO "$0 version $AUTO_PROCESS_VERSION"
    # Check for CASAVA/configureBclToFastq.pl etc
    got_casava=$(which configureBclToFastq.pl 2>&1 | grep "which: no configureBclToFastq.pl in ")
    if [ ! -z "$got_casava" ] ; then
	log_step Make_fastqs ERROR "configureBclToFastq.pl not found"
	exit 1
    fi
    # Collect processing runs and iterate over them
    for run in $(get_info DEFINE_RUN) ; do
	# Extract run information
	sample_sheet=$(echo $run | cut -d: -f1)
	unaligned_dir=$(echo $run | cut -d: -f2)
	bases_mask=$(echo $run | cut -d: -f3)
	nmismatches=$(echo $run | cut -d: -f4)
	# Generate fastq files for this run
	make_fastqs_for_run $sample_sheet $unaligned_dir $bases_mask $nmismatches
    done
    log_step Make_fastqs FINISHED "Fastq generation completed ok"
}
#
function make_fastqs_for_run() {
    # Generate fastq files for a single run
    #
    # Usage: make_fastqs_for_run SAMPLE_SHEET UNALIGNED_DIR BASES_MASK [NMISMATCHES]
    local sample_sheet=$1
    local unaligned_dir=$2
    local bases_mask=$3
    local nmismatches=$4
    log_step Make_fastqs INFO "*** Generating fastq files for $sample_sheet ***"
    log_step Make_fastqs INFO "Sample sheet: $sample_sheet"
    log_step Make_fastqs INFO "Output dir: $unaligned_dir"
    log_step Make_fastqs INFO "Bases mask: $bases_mask"
    # Determine nmismatches from bases mask if not found in definition
    if [ -z "$nmismatches" ] ; then
	nmismatches=$(get_nmismatches $bases_mask)
	log_step Make_fastqs INFO "Number of mismatches (determined from bases mask): $nmismatches"
    else
	log_step Make_fastqs INFO "Number of mismatches: $nmismatches"
    fi
    # Use qsub -sync y to wait for qsubbed job to finish
    qsub_cmd="qsub -terse -q serial.q -sync y -b y -cwd -o logs -N bclToFastq.$unaligned_dir -V bclToFastq.sh --use-bases-mask $bases_mask --nmismatches $nmismatches $DATA_DIR $unaligned_dir $sample_sheet"
    log_step Make_fastqs INFO "Running command: $qsub_cmd"
    qsub_id=$($qsub_cmd | head -n 1)
    status=$?
    log_step Make_fastqs INFO "Qsub job id: $qsub_id"
    if [ ! -d $unaligned_dir ] ; then
	log_step Make_fastqs ERROR "Failed to generate $unaligned_dir directory"
	exit 1
    fi
    if [ $status -ne 0 ] ; then
	log_step Make_fastqs ERROR "bclToFastq step finished with code $status"
	exit 1
    fi
    # Check output status from CASAVA log file
    casava_exit_code=$(grep "make: finished exit code " logs/bclToFastq.sh.o$qsub_id 2>/dev/null | cut -d" " -f5)
    log_step Make_fastqs INFO "CASAVA exit code: $casava_exit_code"
    if [ $casava_exit_code -ne 0 ] ; then
	log_step Make_fastqs ERROR "CASAVA make step finished with exit code $casava_exit_code"
	exit 1
    fi
    # Check that the outputs match expectations
    verify_cmd="analyse_illumina_run.py --unaligned=$unaligned_dir --verify=$sample_sheet ."
    log_step Make_fastqs INFO "Running command: $verify_cmd"
    status=$?
    if [ $status -ne 0 ] ; then
	log_step Make_fastqs ERROR "Predicted and actual outputs don't match"
	exit 1
    fi
    log_step Make_fastqs INFO "Fastq outputs verified against sample sheet"
    # Generate summary and statistics
    log_step Make_fastqs INFO "Generating summary statistics"
    qsub_cmd="qsub -terse -q serial.q -sync y -b y -cwd -o logs -V -N stats.$unaligned_dir analyse_illumina_run.py --unaligned=$unaligned_dir --stats ."
    log_step Make_fastqs INFO "Running command: $qsub_cmd"
    qsub_id=$($qsub_cmd | head -n 1)
    log_step Make_fastqs INFO "Qsub job id: $qsub_id"
    if [ -f logs/stats.$unaligned_dir.o${qsub_id} ] ; then
	make_fastqs_summary="$unaligned_dir.summary"
	if [ -f $make_fastqs_summary ] ; then
	    /bin/rm $make_fastqs_summary
	fi
	ln -s logs/stats.$unaligned_dir.o${qsub_id} $make_fastqs_summary
	cat $make_fastqs_summary
	log_step Make_fastqs INFO "Summary stats written to $make_fastqs_summary"
    else
	log_step Make_fastqs ERROR "Failed to generate summary stats"
	exit 1
    fi
    log_step Make_fastqs INFO "Fastq generation completed for $sample_sheet"
}
#
function run_qc() {
    # Do QC generation for all processing runs
    log_step Run_qc STARTED "*** Running QC ***"
    log_step Run_qc INFO "$0 version $AUTO_PROCESS_VERSION"
    for run in $(get_info DEFINE_RUN) ; do
	# Extract run information
	sample_sheet=$(echo $run | cut -d: -f1)
	unaligned_dir=$(echo $run | cut -d: -f2)
	# Do QC for this run
	do_qc_for_run $sample_sheet $unaligned_dir
    done
    log_step Run_qc FINISHED "QC completed ok"
}
#
function do_qc_for_run() {
    # Do QC generation
    #
    # Usage: run_qc_for_run SAMPLE_SHEET UNALIGNED_DIR BASES_MASK [NMISMATCHES]
    local sample_sheet=$1
    local unaligned_dir=$2
    log_step Run_qc STARTED "*** Running QC for $sample_sheet ***"
    log_step Run_qc INFO "Sample sheet: $sample_sheet"
    log_step Run_qc INFO "Output dir: $unaligned_dir"
    # Check that outputs match sample sheet
    analyse_illumina_run.py --unaligned=$unaligned_dir --verify=$sample_sheet .
    status=$?
    if [  $status -ne 0 ] ; then
	echo ERROR Unable to verify fastq outputs
	log_step Run_qc ERROR "Unable to verify fastq outputs against sample sheet"
	exit 1
    fi
    log_step Run_qc INFO "Fastq outputs verified against sample sheet"
    # Set up analysis directories
    build_illumina_analysis_dir.py --unaligned=$unaligned_dir .
    status=$?
    if [ $status -ne 0 ] ; then
	log_step Run_qc ERROR "Build_illumina_analysis_dir finished with code $status"
	exit 1
    fi
    # Get list of analysis directories
    projects=
    for p in $(ls -d $unaligned_dir/Project_*) ; do
	proj=$(echo $p | sed 's/^'$unaligned_dir'\/Project_//g')
	if [ ! -d $proj ] ; then
	    log_step Run_qc ERROR "Unable to locate project dir $proj"
	    exit 1
	fi
	projects="$projects $proj"
    done
    echo Projects: $projects
    # Set up QC run command
    qc_cmd="run_qc_pipeline.py --debug --limit=8 --queue=serial.q --input=fastqgz illumina_qc.sh $projects"
    run_qc_pipeline_log=logs/run_qc_pipeline.$unaligned_dir.$$.log
    log_step Run_qc INFO "Running command: $qc_cmd"
    log_step Run_qc INFO "Output will be written to $run_qc_pipeline_log"
    $qc_cmd > $run_qc_pipeline_log 2>&1
    # Verify outputs and generate QC reports
    qc_error=
    for p in $projects ; do
	verify_cmd="qcreporter.py --verify --platform=illumina $p"
	log_step Run_qc INFO "Running command: $verify_cmd"
	$verify_cmd
	status=$?
	if [ $status -ne 0 ] ; then
	    qc_error=yes
	    log_step Run_qc WARNING "QC pipeline failed for $p"
	else
	    log_step Run_qc INFO "QC outputs verified for $p"
	    report_cmd="qcreporter.py --platform=illumina $p"
	    log_step Run_qc INFO "Running command: $report_cmd"
	    $report_cmd
	    log_step Run_qc INFO "Generated QC report for $p"
	fi  
    done
    if [ ! -z "$qc_error" ] ; then
	echo ERROR Failures in qc pipeline
	log_step Run_qc ERROR "Failures in qc pipeline"
	exit 1
    fi
    # Finished
    log_step Run_qc FINISHED "QC completed ok"
}
#
# Main script
#
# Check if platform and data dir info is already available
if [ "$1" == "setup" ] ; then
    # Get platform and data dir from command line
    PLATFORM=$2
    DATA_DIR=$3
    # Set up analysis directory name
    ANALYSIS_DIR=$(basename ${DATA_DIR})_analysis
    echo Analysis dir $ANALYSIS_DIR
    # Run setup and exit
    setup
    exit 0
else
    # Acquire from processing.info file
    PLATFORM=$(get_info PLATFORM)
    DATA_DIR=$(get_info DATA_DIR)
fi
#
# Check that we have basic information
if [ -z "$DATA_DIR" ] || [ -z "$PLATFORM" ] ; then
    echo ERROR no data dir and/or platform information
    exit 1
fi
#
# Check the platform is valid
if [ "$PLATFORM" == "ga2x" ] || [ "$PLATFORM" == "hiseq" ] || [ "$PLATFORM" == "miseq" ] ; then
    echo Platform $PLATFORM
else
    echo Unrecognised platform: $PLATFORM
    exit 1
fi
#
# Perform the requested actions
while [ ! -z "$1" ] ; do
    case $1 in
	make_fastqs)
	    make_fastqs
	    ;;
	run_qc)
	    run_qc
	    ;;
	*)
	    echo ERROR unknown action $3
	    exit 1
	    ;;
    esac
    shift
done
##
#
