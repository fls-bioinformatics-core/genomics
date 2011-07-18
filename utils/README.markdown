utils
=====

Place to put general utility scripts/tools.

cd_set_umask.sh
---------------
Script to set and reverts a user's umask appropriately when moving in and out of q
particular directory (or one of its subdirectories).

do.sh
-----
Execute a command multiple times, substituting a range of integer index
values for each execution. For example:

do.sh 1 43 ln -s /blah/blah#/myfile#.ext ./myfile#.ext

will execute:

ln -s /blah/blah1/myfile1.ext ./myfile1.ext
ln -s /blah/blah2/myfile2.ext ./myfile2.ext
...
ln -s /blah/blah43/myfile43.ext ./myfile43.ext
