# Running NASA Ames Stereo Pipeline with TGO CASSIS. 
Repository to store code for stereo processing of TGO CASSIS..
  
**/isis_scripts** 

Collection of Python script that use [USGS ISIS](https://isis.astrogeology.usgs.gov/) and [NASA ASP](https://ti.arc.nasa.gov/tech/asr/groups/intelligent-robotics/ngt/stereo/) for processing CaSSIS data.

**/isis_apps** 

Custom [USGS ISIS](https://isis.astrogeology.usgs.gov/) applications. 

# Standalone package
Standalone package is avaliable for Linux (tested on Ubuntu 14.04). It was build for research purposes using 
[CDE](http://www.pgbovine.net/cde.html) virtualization tool and contains all python, USGS ISIS, NASA ASP dependencies.

## Set up the package

Please download the package from [here](https://drive.google.com/drive/folders/1uMEPxc36iQqh5z38x0iiWrUFj2jYIJfa?usp=sharing). After downoading and extracting the package please add following line to `cde.options` file in root folder of the package
```
ignore_prefix=/CaSSIS
```   
where `/CaSSIS` is a folder on a local PC were cassis data is stored.
Finally, update SPICE kernels in `cde-root/HDD1/Programs/isis_beta/data`. To update all but ck kernels, use USGS ISIS
server. Simply move to `cde-root/HDD1/Programs/isis_beta/data` and run the following command
```
rsync -azv --delete --partial isisdist.astrogeology.usgs.gov::isis3data/data/tgo ./
```
The ck kernel you can download from `halimede` server.

## Explore observations
To explore observations avaliable in the input `level1c/` folder please run
```
tgocassis_findSeq.py.cde "/CaSSIS/M07/181027_stp028_boot6/level1c"
```
The script creates `summary.csv` file in `level1c/` folder with summary of all observation in the folder.

## Process observations
To process several or all observations in the `level1c/` folder, please run
```
tgocassis_process.py.cde \
        "/CaSSIS/M07/181027_stp028_boot6/level1c"
        "/CaSSIS/M07/181027_stp028_boot6/processed"
        --no_ba
        --no_dtm
        --debug
        --observation MY34_004204_186
        --observation MY34_004204_235
```
For each observation in `level1c/` the script creates individual folder in `processed/` folder. For "mono" observations the scripts creates map-projected bundle-adjusted color mosaic, and for "stereo" observations it creates two map-projected bundle-adjusted color mosaics, disparity image and DTM.

`--no_ba` flag turns off the bundle adjustment, `--no_dtm` flag disables DTM computation, `--debug` flag forces script to preserve debug information and `--observation` option allows to specify observation for processing.  

## Run triangulation
To run only triangulation please execute 
```
tgocassis_triangulate.py.cde \
	DISPARITY="/CaSSIS/181027_stp028_boot6/processed/M07/MY34_004204_186_stereo/MY34_004204_186_disparity.tif"		MOSAIC_0="/CaSSIS/181027_stp028_boot6/processed/M07/MY34_004204_186_stereo/MY34_004204_186_first_stereo_PAN_MOS.cub"
	MOSAIC_1="/CaSSIS/181027_stp028_boot6/processed/M07/MY34_004204_186_stereo/MY34_004204_186_second_stereo_PAN_MOS.cub"
	FRAMELETS_0="/CaSSIS/M07/181027_stp028_boot6/processed/MY34_004204_186_stereo/MY34_004204_186_first_stereo_PAN_MAP"	   FRAMELETS_1="/CaSSIS/M07/181027_stp028_boot6/processed/MY34_004204_186_stereo/MY34_004204_186_second_stereo_PAN_MAP"
        DTM="/CaSSIS/M07/181027_stp028_boot6/processed/MY34_004204_186_stereo/MY34_004204_186_dtm.cub"
        ERROR="/CaSSIS/M07/181027_stp028_boot6/processed/MY34_004204_186_stereo/MY34_004204_186_error.cub"
```


If you using this code please cite our [paper](http://fleuret.org/papers/tulyakov-et-al-jasr2018.pdf)
```
@article{tulyakov-et-al-2018,
  title = {Geometric calibration of Colour and Stereo Surface Imaging System of {ESA}'s {T}race {G}as {O}rbiter},
  author = {Tulyakov, S. and Ivanov, A. and Thomas, N. and Roloff, V. and Pommerol, A. and Cremonese, G. and Weigel, T. and Fleuret, F.},
  journal = {Advances in Space Research},
  volume = {61},
  number = {1},
  pages = {487-496},
  year = {2018},
  url = {http://fleuret.org/papers/tulyakov-et-al-jasr2018.pdf}
}
```
