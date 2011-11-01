#!/bin/sh
#
# setup_genome_indexes.sh
#
# Script to automatically setup genome indexes by: fetching
# fasta files, constructing indexes, and making configuration
# files for fastq_screen and Galaxy.
#
# Edit the following variables in the script to specify which
# sequences and indexes to build:
#
# SEQUENCES: list of organisms to fetch FASTA files for (prerequisite
#            for the indexes)
# BOWTIE_INDEXES: list of organisms to build Bowtie indexes for
# BFAST_INDEXES: list of organisms to build Bfast indexes for
# SRMA_INDEXES: list of organisms to build Picard/SRMA indexes for
#
# The following variables specify which organisms to include in
# the fastq_screen conf files (color space bowtie indexes are a
# prerequisite)
#
# FASTQ_SCREEN_MODEL_ORGANISMS: model organisms
# FASTQ_SCREEN_OTHER_ORGANISMS: "other" organisms
# FASTQ_SCREEN_rRNA: rRNA
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
function get_organism_data() {
    local field=$2
    if [ -f "$1.info" ] ; then
	# Found .info file, extract organism name
	local data=`grep "^# $field:" ${1}.info | cut -d' ' -f3-`
	echo "$data"
    else
	echo $1
    fi
}
#
function get_display_name() {
    local organism=$(get_organism_data $1 Organism)
    local name=$(get_organism_data $1 Species)
    echo "$name $1 ($organism)"
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
    local description=$3
    if [ -z "$description" ] ; then
	description=$screen_name
    fi
    #
    if [ ! -d fastq_screen ] ; then
	# Make a fastq_screen directory
	mkdir fastq_screen
    fi
    # Conf file
    local conf_file=fastq_screen/fastq_screen_${screen_name}.conf
    echo Making conf file $conf_file
    # Header
    # Default number of threads is 8
    cat <<EOF > $conf_file
## $screen_name ##
# Description: $description
#
# `date`
#

############
## Threads #
############

THREADS		8

EOF
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
SEQUENCES="dm3 ecoli hg18 mm9 Ncrassa PhiX rn4 sacBay sacCer2 SpR6 UniVec ws200"
for organism in $SEQUENCES ; do
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
FASTQ_SCREEN_MODEL_ORGANISMS="hg18 mm9 rn4 dm3 ws200 ecoli sacCer2 PhiX UniVec SpR6"
FASTQ_SCREEN_OTHER_ORGANISMS="sacBay Ncrassa dicty"
FASTQ_SCREEN_rRNA=""
make_fastq_screen_conf model_organisms \
    "$FASTQ_SCREEN_MODEL_ORGANISMS" "Model organisms"
make_fastq_screen_conf other_organisms \
    "$FASTQ_SCREEN_OTHER_ORGANISMS" "Other organisms"
make_fastq_screen_conf rRNA \
    "FASTQ_SCREEN_rRNA" "rRNA"
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
#
# fastq_screen.loc
echo "# fastq_screen.loc: #"
echo "# Autogenerated .loc file for fastq_screen" > ${TOP_DIR}/fastq_screen.loc
for screen in `ls fastq_screen 2>&1` ; do
    echo Examining $screen
    # Full path for screen file
    screen_file=`pwd`/fastq_screen/$screen
    # Get the description
    description=`grep "^# Description:" $screen_file | cut -d" " -f3-`
    echo "$description"$'\t'"$screen_file" >> ${TOP_DIR}/fastq_screen.loc
done
#
###########################################################
# HTML pages
###########################################################
echo "### Writing HTML index file ###"
cat <<EOF > ${TOP_DIR}/genome_indexes.html
<html>
<head>
<title>Genome Indexes</title>
<style>
table {
   empty-cells: show;
}
th {
   background-color: #660099;
   color: white;
}
td.index {
   text-align: center;
}
td {
   border-bottom: 1px solid #aaaaaa;
}
</style>
</head>
<body>
<h1>Genome Indexes</h1>
<p>The following indexes are currently available:</p>
<table>
<tr>
<th>Id</th>
<th>Name</th>
<th>Organism</th>
<th>Seq</th>
<th>Bowtie (NT)</th>
<th>Bowtie (CS)</th>
<th>Bfast (CS)</th>
<th>Picard/SRMA</th>
<th>Size</th>
</tr>
EOF
for name in `ls . 2>&1` ; do
    fasta=$(get_fasta $name)
    if [ ! -z $fasta ] && [ -d $name ] ; then
	echo Examining $name
	# Get size
	size=`du -s -h $name | cut -f1`
	# Move into organism dir
	cd $name
	# Species name
	species=$(get_organism_data $name Species)
	# Display name
	display_name=$(get_organism_data $name Organism)
	# Determine which indexes are available
	# Bowtie
	bowtie_indexes=$(get_bowtie_indexes $name)
	if [ ! -z "$bowtie_indexes" ] ; then
	    bowtie_indexes=YES
	fi
	# Bowtie color
	bowtie_color_indexes=$(get_bowtie_color_indexes $name)
	if [ ! -z "$bowtie_color_indexes" ] ; then
	    bowtie_color_indexes=YES
	fi
	# Bfast
	bfast_color_indexes=$(get_bfast_color_indexes $fasta)
	if [ ! -z "$bfast_color_indexes" ] ; then
	    bfast_color_indexes=YES
	fi
	# Picard/SRMA
	dict=../${fasta%.*}.dict
	fai=../${fasta}.fai
	if [ -f $dict ] && [ -f $fai ] ; then
	    picard_indexes=YES
	else
	    picard_indexes=
	fi
	# Write the table line
	cat <<EOF >> ${TOP_DIR}/genome_indexes.html
<tr>
<td>$name</td>
<td>$species</td>
<td>$display_name</td>
<td class="index">YES</td>
<td class="index">$bowtie_indexes</td>
<td class="index">$bowtie_color_indexes</td>
<td class="index">$bfast_color_indexes</td>
<td class="index">$picard_indexes</td>
<td>$size</td>
</tr>
EOF
	# Return to original dir
	cd ${TOP_DIR}
    fi
done
total_size=`du -s -h ${TOP_DIR} | cut -f1`
today=`date`
script=`basename $0`
cat <<EOF >> ${TOP_DIR}/genome_indexes.html
</table>
<p>Total size for all indexes: $total_size</p>
<p>This page generated at $today by $script</p>
</body>
</html>
EOF
##
#
