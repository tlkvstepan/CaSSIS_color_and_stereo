#!/usr/bin/env python
import sys
import re
import tempfile
import os
import shutil
import tgocassis_utils as tgo
import commands
import glob

if len(sys.argv) < 5:
    print(
        'tgocassis_mapMos <cub_dir> <file.map>  <map_dir> <mosaic.cub> <True/False> \n'
        '<cub_dir> is a directories containing SPICED cube files. \n'
        '<file.map> is a map file. \n'
        '<map_dir> is an output directory with cubes projected to map.\n'
        '<mosaic.cub> is an output mosaic cub.\n'
        '<yes/no> perform equalization.\n')
    sys.exit()

cub_dirname = os.path.abspath(sys.argv[1])
map_filename = os.path.abspath(sys.argv[2])
map_dirname = os.path.abspath(sys.argv[3])
mosaic_filename = os.path.abspath(sys.argv[4])
equ = (sys.argv[5] == 'yes') or (sys.argv[5] == 'Yes') or (
    sys.argv[5] == 'YES') or (sys.argv[5] == 'true') or (
        sys.argv[5] == 'TRUE') or (sys.argv[5] == 'True')

mosaic_dir = os.path.dirname(mosaic_filename)

assert os.environ.get('ISISROOT') is not None, 'ISIS is not installed properly'
assert os.path.isdir(cub_dirname), 'Folder %s does not exist' % (cub_dirname)
assert os.path.isfile(map_filename), 'File %s does not exist' % (map_filename)
assert os.path.isdir(map_dirname), 'Folder %s does not exist' % (map_dirname)
assert os.path.isdir(mosaic_dir), 'Folder %s does not exist' % (mosaic_dir)

alllis_fn = tempfile.mktemp()

# make common list
seqlist = glob.glob(os.path.join(cub_dirname, "*.cub"))
with open(alllis_fn, 'w') as file:
    for idx, framelet in enumerate(seqlist):
        if idx == 0: ref_cub = os.path.basename(framelet).rstrip('.cub')
        file.write("%s\n" % os.path.basename(framelet).rstrip('.cub'))

# calculate extent of the map
_, minLat = commands.getstatusoutput(
    'getkey from="%s" grpname=Mapping keyword=MinimumLatitude' %
    (map_filename))
_, maxLat = commands.getstatusoutput(
    'getkey from="%s" grpname=Mapping keyword=MaximumLatitude' %
    (map_filename))
_, minLon = commands.getstatusoutput(
    'getkey from="%s" grpname=Mapping keyword=MinimumLongitude' %
    (map_filename))
_, maxLon = commands.getstatusoutput(
    'getkey from="%s" grpname=Mapping keyword=MaximumLongitude' %
    (map_filename))

# map project framelets
exe_str = 'cam2map from="%s/\$1.cub" map="%s" pixres=map to="%s/\$1.cub" -batchlist="%s"' % (
    cub_dirname, map_filename, map_dirname, alllis_fn)
os.system(exe_str)

# make list of framelts
exe_str = 'ls "%s/"*".cub" > "%s"' % (map_dirname, alllis_fn)
os.system(exe_str)

if equ:
    # make held cubes list
    heldlis_fn = tempfile.mktemp()
    with open(alllis_fn, 'r') as f:
        lines = f.readlines()
        alllis = [line.rstrip() for line in lines]  # delete line breaks
    print alllis
    heldlis = [alllis[len(alllis) // 2]]

    with open(heldlis_fn, 'w') as f:
        heldlis = [line + '\n' for line in heldlis]
        f.writelines(heldlis)

    # equlaize
    exe_str = 'equalizer fromlist="%s" holdlist="%s"' % (alllis_fn, heldlis_fn)
    print exe_str
    os.system(exe_str)

    # make list of framelts
    exe_str = 'ls "%s/"*".equ.cub" > "%s"' % (map_dirname, alllis_fn)
    os.system(exe_str)

    os.remove(heldlis_fn)

# mosaic
exe_str = 'automos fromlist="%s" mosaic="%s" grange=user minlat=%s maxlat=%s minlon=%s maxlon=%s track=true' % (
    alllis_fn, mosaic_filename, minLat, maxLat, minLon, maxLon)
os.system(exe_str)

# remove temporary files
os.remove(alllis_fn)