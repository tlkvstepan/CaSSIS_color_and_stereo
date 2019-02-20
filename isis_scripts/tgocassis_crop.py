#!/usr/bin/env python

import os
import argparse
import tempfile
import commands
import shutil

parser = argparse.ArgumentParser(description='Crop ')

parser.add_argument(
    '-inp_dirs',
    dest='inp_dirs',
    nargs='+',
    help='input directories with spiced cubes',
    required=True)

args = parser.parse_args()

# convert to global path
for i, inp_dir in enumerate(args.inp_dirs):
    args.inp_dirs[i] = os.path.abspath(inp_dir)

# check input
assert os.environ.get('ISISROOT') is not None, 'ISIS is not installed properly'
for i, inp_dir in enumerate(args.inp_dirs):
    assert os.path.isdir(inp_dir), 'Folder %s does not exist' % (inp_dir)

# make output directory for each input
out_dirs = []
for i, inp_dir in enumerate(args.inp_dirs):
    out_dir = inp_dir + '_BA'
    os.mkdir(out_dir)
    out_dirs.append(inp_dir + '_BA')

# copy cubes to output dir (force rewrite)
for i, inp_dir in enumerate(args.inp_dirs):
    exe_str = 'cp -a -rf "%s/". "%s/"' % (inp_dir, out_dirs[i])
    os.system(exe_str)

# make a list of all cubes
_, cubes_list_fn = tempfile.mkstemp()
for i, out_dir in enumerate(out_dirs):
    exe_str = 'echo "%s"/*.cub | xargs -n1 echo >> %s' % (out_dir,
                                                          cubes_list_fn)
    os.system(exe_str)

# compute map
map_fn = tempfile.NamedTemporaryFile(suffix='.map').name
exe_str = 'mosrange fromlist="%s" to="%s" proj=Equirectangular' % (
    cubes_list_fn, map_fn)
os.system(exe_str)

# find max / min lat / lon
_, minLat = commands.getstatusoutput(
    'getkey from="%s" grpname=Mapping keyword=MinimumLatitude' % (map_fn))
_, maxLat = commands.getstatusoutput(
    'getkey from="%s" grpname=Mapping keyword=MaximumLatitude' % (map_fn))
_, minLon = commands.getstatusoutput(
    'getkey from="%s" grpname=Mapping keyword=MinimumLongitude' % (map_fn))
_, maxLon = commands.getstatusoutput(
    'getkey from="%s" grpname=Mapping keyword=MaximumLongitude' % (map_fn))

# create network
# if there is only one or two channels avaliable, we want to seed more points
if len(inp_dir) <= 2:
    step = '0.004'
else:
    step = '0.008'
empyt_net_fn = tempfile.NamedTemporaryFile(suffix='.net').name
exe_str = 'seedgrid TARGET=mars LATSTEP=%s LONSTEP=%s MINLAT=%s MAXLAT=%s MINLON=%s MAXLON=%s ONET=%s SPACING=latlon POINTID="id?????"' % (
    step, step, minLat, maxLat, minLon, maxLon, empyt_net_fn)
os.system(exe_str)

# add cubes to network
net_fn = tempfile.NamedTemporaryFile(suffix='.net').name
exe_str = 'cnetadd cnet=%s addlist=%s onet=%s retrieval=point' % (
    empyt_net_fn, cubes_list_fn, net_fn)
os.system(exe_str)

# register
registered_net_fn = tempfile.NamedTemporaryFile(suffix='.net').name
autoreg_template_fn = tempfile.NamedTemporaryFile(suffix='.def').name
with open(autoreg_template_fn, 'w') as f:
    # we use small search chip and low tolerance, since colors are already well-registered
    content_str = """ 
	Object = AutoRegistration
	   Group = Algorithm
	     Name         = MaximumCorrelation
	     Tolerance = 0.1
	   EndGroup
	   Group = PatternChip
	     Samples = 35
	     Lines   = 35 
	     MinimumZScore = 1e-5
	   EndGroup
	   Group = SearchChip
	     Samples = 60 
	     Lines   = 60 
	   EndGroup
	EndObject
	"""
    f.write(content_str)
exe_str = 'pointreg fromlist=%s cnet=%s onet=%s deffile=%s' % (
    cubes_list_fn, net_fn, registered_net_fn, autoreg_template_fn)
os.system(exe_str)

# find orphan cubes - cubes that have single measure
# orphan cubes can appear at the beggining and at the end of the sequence
_, check_prefix = tempfile.mkstemp()
singlecube_fn = check_prefix + 'SingleCube.txt'
nocontrol_fn = check_prefix + 'NoControl.txt'
exe_str = 'cnetcheck fromlist=%s cnet=%s prefix=%s singlecube=yes nocontrol=yes singlemeasure=no duplicate=no nolatlon=no lowcoverage=no' % (
    cubes_list_fn, registered_net_fn, check_prefix)
os.system(exe_str)

# create new list of cubes with one or none measures
_, nonempty_cubes_list_fn = tempfile.mkstemp()
empty_cubes_list = []
if os.path.isfile(singlecube_fn):
    with open(singlecube_fn, 'r') as f:
        lines = f.readlines()
        empty_cubes_list += [line.split()[0] for line in lines]  # break lines
if os.path.isfile(nocontrol_fn):
    with open(nocontrol_fn, 'r') as f:
        lines = f.readlines()
        empty_cubes_list += [line.split()[0] for line in lines]  # break lines

with open(cubes_list_fn) as f:
    cubes_list = f.readlines()
nonempty_cubes_list = [
    cube.rstrip() for cube in cubes_list
    if cube.rstrip() not in empty_cubes_list
]
with open(nonempty_cubes_list_fn, 'w') as f:
    nonempty_cubes_list = [cube + '\n' for cube in nonempty_cubes_list]
    f.writelines(nonempty_cubes_list)

# clean network
# delete cubes measure that correspond to cubes with only one measure
valid_net_fn = tempfile.NamedTemporaryFile(suffix='.net').name
exe_str = 'cnetextract fromlist=%s cnet=%s cubes=yes cubemeasure=yes noignore=yes nomeasureless=yes nosinglemeasures=yes cubelist=%s onet=%s' % (
    cubes_list_fn, registered_net_fn, nonempty_cubes_list_fn, valid_net_fn)
os.system(exe_str)

# delete orphans from output folders
for cube in empty_cubes_list:
    os.remove(cube)

# make held list from the first, end image in the sequence
_, held_cubes_list_fn = tempfile.mkstemp()
nonempty_cubes_list = sorted(nonempty_cubes_list)

held_cubes_list = [nonempty_cubes_list[0], nonempty_cubes_list[-1]]
with open(held_cubes_list_fn, 'w') as f:
    f.writelines(held_cubes_list)

# bundle adjustment
ba_net_fn = tempfile.NamedTemporaryFile(suffix='.net').name
exe_str = 'jigsaw fromlist="%s" sigma0=1e-3 model1=huber maxits=200 heldlist="%s" cnet="%s" onet="%s" observations=Yes update=True' % (
    nonempty_cubes_list_fn, held_cubes_list_fn, valid_net_fn, ba_net_fn)
_, report = commands.getstatusoutput(exe_str)

# check if bundle adjustment worked
if 'Camera pointing updated' not in report:
    # clean output folder
    for i, out_dir in enumerate(out_dirs):
        for root, dirs, files in os.walk(out_dir):
            for f in files:
                os.unlink(os.path.join(root, f))
            for d in dirs:
                shutil.rmtree(os.path.join(root, d))

# delete temporary files
os.remove(ba_net_fn)
os.remove(held_cubes_list_fn)
os.remove(valid_net_fn)
os.remove(nonempty_cubes_list_fn)
os.remove(registered_net_fn)
if os.path.isfile(singlecube_fn):
    os.remove(singlecube_fn)
if os.path.isfile(nocontrol_fn):
    os.remove(nocontrol_fn)
os.remove(autoreg_template_fn)
os.remove(net_fn)
os.remove(empyt_net_fn)
os.remove(map_fn)
os.remove(cubes_list_fn)
