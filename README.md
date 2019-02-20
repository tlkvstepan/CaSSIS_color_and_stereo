# CASSIS_stereo 
Repository to store code for stereo processing of TGO CASSIS image.
  
**/isis_scripts** 

Collection of Python-ISIS-ASP for processing CaSSIS data.

**/isis_apps** 

Custom ISIS applications. Should be compiled with USGS ISIS. 

# Standalone package
Stand alone package is avalable for GoogleDrive. It is build for research purposes using 
[CDE](http://www.pgbovine.net/cde.html) virtualization tool and contains all python, ISIS, ASP dependencies so it should run standalone on any Linux machine (tested on Ubuntu14.04).

Having CaSSIS level1(a,b,c..) data in folder `level1c/` run

```
process_folder.py \
        "/level1c"
        "/processed"
        --no_ba
        --no_dtm
        --debug
        --observation MY34_004204_186
        --observation MY34_004204_235
```
As a result each observation is placed in individual folder in `processed/` folder.  . For "mono" observations the scripts reconstructs map-projected color mosaic, which
is bundle-adjusted. For "stereo" observations the script reconstructs two map-projected color mosaics, which are bundle-adjusted , and computes disparity image and DTM.

`--no_ba` flag turns off the bundle adjustment, `--no_dtm` flag disables DTM computation, `--debug` flag forces script to preserve debug information and `--observation` option allows to specify observation for processing.  

To explore what observations are avaliable in `level1c/` one can run
```
tgocassis_findSeq.py "/level1c"
```
The script creates `level1c/summary.csv` file with summary of all observation found in the folder.
