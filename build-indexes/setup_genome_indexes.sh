#!/bin/sh
#
# setup_genome_indexes.sh
#
# Script to automatically setup genome indexes by: fetching
# fasta files, constructing indexes, and making configuration
# files for fastq_screen and Galaxy.
#
# Import functions
. `dirname $0`/../share/functions.sh
#
# Initialise
TOP_DIR=`pwd`
SCRIPT_DIR=$(abs_path `dirname $0`)
#
###########################################################
# Local functions
###########################################################
function get_fasta() {
    if [ -d "$1" ] ; then
	# Directory exists, look for .info
	if [ -f "$1/$1.info" ] ; then
	    # Extract fasta file name
	    local fasta=`grep "^# Fasta:" $1/${1}.info | cut -d' ' -f3`
	    if [ -f "$1/fasta/$fasta" ] ; then
		# Fasta file exists
		echo $1/fasta/$fasta
		return 0
	    fi
	fi
    fi
    # Not found
    echo ""
    return 1
}
#
function get_display_name() {
    if [ -f "$1.info" ] ; then
	# Found .info file, extract organism name
	local name=`grep "^# Organism:" ${1}.info | cut -d' ' -f3-`
	echo "$1 ($name)"
    else
	echo $1
    fi
}
#
function get_bowtie_indexes() {
    if [ ! -d bowtie ] ; then
	# No 'bowtie' subdir
	echo ""
	return 1
    fi
    # Check for basespace index files
    local bwt=`ls bowtie/${1}.*.ebwt 2>/dev/null`
    echo $bwt
}
#
function get_bowtie_color_indexes() {
    if [ ! -d bowtie ] ; then
	# No 'bowtie' subdir
	echo ""
	return 1
    fi
    # Check for colorspace index files
    local bwt=`ls bowtie/${1}_c.*.ebwt 2>/dev/null`
    echo $bwt
}
#
function get_bfast_color_indexes() {
    if [ ! -d bfast ] ; then
	# No 'bfast' subdir
	echo ""
	return 1
    fi
    # Check for colorspace index files
    local bfast_base=`basename $1`
    local bif=`ls bfast/${bfast_base}.cs.*.*.bif 2>/dev/null`
    echo $bif
}
#
function set_bfast_splitting_depth() {
    # Set the splitting depth based on the size
    # of the fasta file
    # Arbitrarily, if fasta file >~ 1Gb then set splitting
    # depth to 1, otherwise set to 0
    echo fasta $1
    local size=`du -s $1 | cut -d$'\t' -f1`
    if [ $size -ge 1000000 ] ; then
	echo 1
    else
	echo 0
    fi
}
#
function make_fastq_screen_conf() {
    #
    local screen_name=$1
    local organisms=$2
    #
    if [ ! -d fastq_screen ] ; then
	# Make a fastq_screen directory
	mkdir fastq_screen
    fi
    # Conf file
    local conf_file=fastq_screen/fastq_screen_${screen_name}.conf
    echo Making conf file $conf_file
    # Header
    echo "## $screen_name ##" > $conf_file
    echo "#" >> $conf_file
    echo "# `date`" >> $conf_file
    # Populate
    local organism=
    for organism in $organisms ; do
	# Find bowtie_c files
	local bowtie_c_base=`pwd`/${organism}/bowtie/${organism}_c
	if [ -f "${bowtie_c_base}.1.ebwt" ] ; then
	    # Add to screen file
	    echo "" >> $conf_file
	    echo "## $organism ##" >> $conf_file
	    echo "DATABASE"$'\t'${organism}$'\t'${bowtie_c_base} >> $conf_file
	else
	    echo "WARNING bowtie indexes not found for $organism"
	fi
    done
}
#
###########################################################
# FASTA FILES
###########################################################
echo "### Setting up FASTA files ###"
ORGANISMS="mm9 sacCer2 SpR6 dm3 ecoli ws200"
for organism in $ORGANISMS ; do
    echo -n "${organism}: "
    fasta=$(get_fasta $organism)
    if [ -z "$fasta" ] ; then
	# Not found
	echo -n "fetching/building FASTA: "
	if [ ! -d $organism ] ; then
	    # Make a directory
	    mkdir $organism
	fi
	# Download the fasta file
	log=`mktemp --suffix=.log`
	cd $organism
	${SCRIPT_DIR}/fetch_fasta.sh ${organism} 2>&1 > $log
	if [ $? -ne 0 ] ; then
	    echo FAILED
	    echo See log: $log
	else
	    echo OK
	    /bin/rm $log
	fi
    else
	# Already exists
	echo "already present: OK"
    fi
    # Return to top level
    cd ${TOP_DIR}
done
#
###########################################################
# BOWTIE INDEXES
###########################################################
echo "### Setting up BOWTIE indexes ###"
BOWTIE_INDEXES="dm3 ecoli mm9 sacCer2 SpR6"
for organism in $BOWTIE_INDEXES ; do
    echo -n "${organism}: "
    fasta=$(get_fasta $organism)
    if [ -z "$fasta" ] ; then
	# Not found
	echo "no FASTA file: FAILED"
    else
	# Move into organism dir
	cd $organism
	# Check for bowtie indexes
	bowtie_indexes=$(get_bowtie_indexes $organism)
	bowtie_color_indexes=$(get_bowtie_color_indexes $organism)
	if [ -z "$bowtie_indexes" ] || [ -z "$bowtie_color_indexes" ] ; then
	    echo -n "building bowtie indexes: "
	    if [ ! -d bowtie ] ; then
		mkdir bowtie
	    fi
	    cd bowtie
	    log=`mktemp --suffix=_bowtie.log`
	    ${SCRIPT_DIR}/bowtie_build_indexes.sh ${TOP_DIR}/${fasta} > $log 2>&1
	    if [ $? -ne 0 ] ; then
		echo FAILED
		echo See log: $log
	    else
		echo OK
		/bin/rm $log
	    fi
	else
	    echo bowtie indexes already built: OK
	fi
    fi
    # Return to original dir
    cd ${TOP_DIR}
done
#
###########################################################
# BFAST INDEXES
###########################################################
echo "### Setting up BFAST indexes ###"
BFAST_INDEXES="ecoli SpR6 mm9"
for organism in $BFAST_INDEXES ; do
    echo -n "${organism}: "
    fasta=$(get_fasta $organism)
    if [ -z "$fasta" ] ; then
	# Not found
	echo "no FASTA file: FAILED"
    else
	# Move into organism dir
	cd $organism
	# Check for bfast indexes
	bfast_color_indexes=$(get_bfast_color_indexes $fasta)
	if [ -z "$bfast_color_indexes" ] ; then
	    echo -n "building bfast indexes: "
	    if [ ! -d bfast ] ; then
		mkdir bfast
	    fi
	    cd bfast
	    log=`mktemp --suffix=_bfast.log`
	    splitting_depth=$(set_bfast_splitting_depth ${TOP_DIR}/${fasta})
	    ${SCRIPT_DIR}/bfast_build_indexes.sh -n 8 -d ${splitting_depth} ${TOP_DIR}/${fasta} > $log 2>&1
	    if [ $? -ne 0 ] ; then
		echo FAILED
		echo See log: $log
	    else
		echo OK
		/bin/rm $log
	    fi
	else
	    echo bfast indexes already built: OK
	fi
    fi
    # Return to original dir
    cd ${TOP_DIR}
done
#
###########################################################
# SRMA INDEXES
###########################################################
echo "### Setting up SRMA indexes ###"
SRMA_INDEXES="ecoli sacCer2 SpR6"
for organism in $SRMA_INDEXES ; do
    echo -n "${organism}: "
    fasta=$(get_fasta $organism)
    if [ -z "$fasta" ] ; then
	# Not found
	echo "no FASTA file: FAILED"
    else
	# Check if indexes already exist
	# i.e. are there .fai and .dict files
	dict=${fasta%.*}.dict
	fai=${fasta}.fai
	if [ ! -f $dict ] || [ ! -f $fai ] ; then
	    # Run the srma_build_indexes.sh script
	    echo -n "building SRMA/fai indexes: "
	    log=`mktemp --suffix=_srma.log`
	    ${SCRIPT_DIR}/srma_build_indexes.sh ${TOP_DIR}/${fasta} > $log 2>&1
	    if [ $? -ne 0 ] ; then
		echo FAILED
		echo See log: $log
	    else
		echo OK
		/bin/rm $log
	    fi
	else
	    echo SRMA indexes already built: OK
	fi
    fi
done
#
###########################################################
# FASTQ_SCREEN
###########################################################
echo "### Setting up fastq_screen conf files ###"
model_organisms="hg18 mm9 rn4 dm3 ws200 ecoli sacCer2 PhiX UniVec SpR6"
other_organisms="sacBay Ncrassa dicty"
make_fastq_screen_conf "model_organisms" "$model_organisms"
make_fastq_screen_conf "other_organisms" "$other_organisms"
#
###########################################################
# GALAXY LOC FILES
###########################################################
echo "### Setting up .loc files for Galaxy ###"
#
# bowtie_indices.loc & bowtie_indices_color.loc
echo "# bowtie_indices.loc/bowtie_indices_color.loc: #"
echo "# Autogenerated .loc file for Bowtie" > ${TOP_DIR}/bowtie_indices.loc
echo "# Autogenerated .loc file for Bowtie (colorspace)" > ${TOP_DIR}/bowtie_indices_color.loc
for organism in $BOWTIE_INDEXES ; do
    echo Examining $organism
    if [ -d $organism ] ; then
	# Move into organism dir
	cd $organism
	# Display name
	display_name=$(get_display_name $organism)
	# Check for bowtie indexes
	bowtie_indexes=$(get_bowtie_indexes $organism)
	if [ ! -z "$bowtie_indexes" ] ; then
	    bowtie_base=`pwd`/bowtie/${organism}
	    echo "$organism"$'\t'"$organism"$'\t'"$display_name"$'\t'"$bowtie_base" >> ${TOP_DIR}/bowtie_indices.loc
	fi
	# Check for color space indexes
	bowtie_color_indexes=$(get_bowtie_color_indexes $organism)
	if [ ! -z "$bowtie_color_indexes" ] ; then
	    bowtie_base=`pwd`/bowtie/${organism}_c
	    echo "$organism"$'\t'"$organism"$'\t'"$display_name"$'\t'"$bowtie_base" >> ${TOP_DIR}/bowtie_indices_color.loc
	fi
	# Return to original dir
	cd ${TOP_DIR}
    fi
done
#
# bfast_indexes.loc
# <unique_id> <build> <galaxy_formats> <description> <bfast_index_dir>
echo "# bfast_indexes.loc: #"
echo "# Autogenerated .loc file for Bfast" > ${TOP_DIR}/bfast_indexes.loc
for organism in $BFAST_INDEXES ; do
    echo Examining $organism
    fasta=$(get_fasta $organism)
    if [ -d $organism ] ; then
	# Move into organism dir
	cd $organism
	# Display name
	display_name=$(get_display_name $organism)
	# Check for bfast indexes
	bfast_color_indexes=$(get_bfast_color_indexes $fasta)
	if [ ! -z "$bfast_color_indexes" ] ; then
	    fasta=`basename $fasta`
	    bfast_base=`pwd`/bfast/${fasta}
	    echo "$organism"$'\t'"$organism"$'\t'"fastqcssanger"$'\t'"$display_name"$'\t'"$bfast_base" >> ${TOP_DIR}/bfast_indexes.loc
	fi
	# Return to original dir
	cd ${TOP_DIR}
    fi
done
#
# picard_index.loc
echo "# picard_index.loc: #"
echo "# Autogenerated .loc file for Picard" > ${TOP_DIR}/picard_index.loc
for organism in $SRMA_INDEXES ; do
    echo Examining $organism
    fasta=$(get_fasta $organism)
    if [ ! -z $fasta ] && [ -d $organism ] ; then
	# Full path for fasta file
	fasta=`pwd`/${fasta}
	# Move into organism dir
	cd $organism
	# Display name
	display_name=$(get_display_name $organism)
	echo "$organism"$'\t'"$organism"$'\t'"$display_name"$'\t'"$fasta" >> ${TOP_DIR}/picard_index.loc
	# Return to original dir
	cd ${TOP_DIR}
    fi
done
#
# all_fasta.loc
echo "# all_fasta.loc: #"
echo "# Autogenerated .loc file" > ${TOP_DIR}/all_fasta.loc
for name in `ls . 2>&1` ; do
    fasta=$(get_fasta $name)
    if [ ! -z $fasta ] && [ -d $name ] ; then
	echo Examining $name
	# Full path for fasta file
	fasta=`pwd`/${fasta}
	# Move into organism dir
	cd $name
	# Display name
	display_name=$(get_display_name $name)
	echo "$name"$'\t'"$name"$'\t'"$display_name"$'\t'"$fasta" >> ${TOP_DIR}/all_fasta.loc
	# Return to original dir
	cd ${TOP_DIR}
    fi
done
##
#
