## Scripts for processing of CaSSIS data

**Prerequisits:**

* Install python2.7
* Install opencv for python
* Install usgs isis
* Put all scripts in globally visible folder

**Description of main functions**
(for additional info call functions with --h / --help will produce help information)

* _tgocassis_findSeq.py_ -from <_level2_dir_>  
Given folder with level1 / level2 data produces lists of sub-exposures for each band and each sequence in the same folder.

* _tgocassis_mapproj_mosaic.py_ -from <_seq1_band1.lis_> ... <_seq1_band4.lis_>   -from1 <_seq2_band1.lis_> ... <_seq2_band4.lis_> -to <_output_dir_> -ba <_yes/no_> 
Produces color mosaic(s) of individaul sequence or stereo sequences, given cubes lists. In the latter case function will produce two mosaics projected on the common map. The function can be run with or without bundle adjustment.

* _batch_mapproj_mosaic.py_ -from <_level2_dir_> -to <_output_dir_> -ba <_yes/no_>
Produces color mosaic of individiaul sequences or stereo sequences for all sequences, given input folder with level1 / level2 data (currently only individual sequences are supported!). The function can be run with or without bundle adjustment.  






