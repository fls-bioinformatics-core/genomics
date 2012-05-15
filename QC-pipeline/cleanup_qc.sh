#/bin/sh
#
# Utility script to clean up qc products
echo -n "Remove all QC products in `pwd`? [y/N]: "
read ok
case $ok in
    y|Y|yes|Yes)
	# Do clean up
	/bin/rm -r qc
	/bin/rm *_T_F3.*
	/bin/rm *.fastq
	/bin/rm SOLiD_preprocess_filter.stats SOLiD_preprocess_filter_paired.stats
	/bin/rm qc.*.o* qc.*.e*
	/bin/rm -r tmp.*
	;;
esac
echo "Done"
##
#