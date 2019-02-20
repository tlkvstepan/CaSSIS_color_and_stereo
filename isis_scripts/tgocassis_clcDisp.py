#!/usr/bin/env python

import sys
import tempfile
import os
import shutil

if len(sys.argv) < 4:
    print(
        'tgocassis_clcDisp <mosaic0.cub> <mosaic1.cub> <disp.tif> \n'
        '<mosaic0.cub> <mosaic1.cub> are two stereo mosaic cubes. \n'
        '<disp.tif> is an output match file (sample0, line0, sample1, line1)')
    sys.exit()

mosaic0_fname = os.path.abspath(sys.argv[1])
mosaic1_fname = os.path.abspath(sys.argv[2])
disp_fname = os.path.abspath(sys.argv[3])
disp_dname = os.path.dirname(disp_fname)

bands_dir = tempfile.mkdtemp()
mosaic0_band0 = os.path.join(
    bands_dir,
    os.path.basename(mosaic0_fname).rstrip('.cub') + '.band0001.cub')
mosaic0_band1 = os.path.join(
    bands_dir,
    os.path.basename(mosaic0_fname).rstrip('.cub') + '.band0002.cub')
mosaic1_band0 = os.path.join(
    bands_dir,
    os.path.basename(mosaic1_fname).rstrip('.cub') + '.band0001.cub')
mosaic1_band1 = os.path.join(
    bands_dir,
    os.path.basename(mosaic1_fname).rstrip('.cub') + '.band0002.cub')

assert os.path.isfile(
    mosaic0_fname), 'File %s does not exist' % (mosaic0_fname)
assert os.path.isfile(
    mosaic1_fname), 'File %s does not exist' % (mosaic1_fname)
assert os.path.isdir(disp_dname), 'Folder %s does not exist' % (disp_dname)
assert os.environ.get('ISISROOT') is not None, 'ISIS is not installed properly'

# explode mosaic cube since Ames does not understand mosaic with TRACE
exe_str = 'explode from="%s" to="%s"' % (
    mosaic0_fname,
    os.path.join(bands_dir,
                 os.path.basename(mosaic0_fname).rstrip('.cub')))
print 'Calling %s' % exe_str
os.system(exe_str)

exe_str = 'explode from="%s" to="%s"' % (
    mosaic1_fname,
    os.path.join(bands_dir,
                 os.path.basename(mosaic1_fname).rstrip('.cub')))
print 'Calling %s' % exe_str
os.system(exe_str)

# stereo
# 2 - affine window
# 1 - parabola
# 0 - no

stereo_dir = tempfile.mkdtemp()
stereo_suffix = os.path.join(stereo_dir, 'output')
exe_str = 'stereo "%s" "%s" --alignment-method none --subpixel-mode 2  --stop-point 4 "%s"' % (
    mosaic0_band0, mosaic1_band0, stereo_suffix)
print 'Calling %s' % exe_str
os.system(exe_str)

# save stereo matches to match file
shutil.copyfile(os.path.join(stereo_dir, 'output-F.tif'), disp_fname)

os.remove(mosaic0_band0)
os.remove(mosaic1_band0)
os.remove(mosaic0_band1)
os.remove(mosaic1_band1)

#shutil.rmtree(stereo_dir)
