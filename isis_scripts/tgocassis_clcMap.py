#!/usr/bin/env python
import sys
import tempfile
import os


if len(sys.argv) < 2:
    print('tgocassis_clcMap <cub_dir0> <cub_dir1 - optional> <file.map> \n'
          '<cub_dir0> <cub_dir1> are directories containing SPICED cube files.\n'
          '<file.map> is an output map file')
    sys.exit()

cub_dirs = []
for arg in sys.argv[1:-1]:
    cub_dirs.append(os.path.abspath(arg))
map_file = os.path.abspath(sys.argv[-1])
output_dir = os.path.dirname(os.path.abspath(map_file))

assert os.environ.get('ISISROOT') is not None, 'ISIS is not installed properly'
for cub_dir in cub_dirs:
    assert os.path.isdir(cub_dir), 'Folder %s does not exist' % (cub_dir)
assert os.path.isdir(output_dir), 'Folder %s does not exist' % (map_file)

cubeslis_file = tempfile.mktemp()

# make common list
for cub_dir in cub_dirs:
    exe_str = 'ls "%s/"*"cub" >> "%s"' % (cub_dir, cubeslis_file)
    print 'Calling %s' % exe_str
    os.system(exe_str)

# find lat / lon range
exe_str = 'mosrange fromlist="%s" to="%s" proj=Equirectangular' % (
    cubeslis_file, map_file)
print 'Calling %s' % exe_str
os.system(exe_str)
os.remove(cubeslis_file)
