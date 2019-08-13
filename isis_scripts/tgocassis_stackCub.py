#!/usr/bin/env python
import sys
import os
import tempfile

if len(sys.argv) < 3:
    print(
        'tgocassis_stackCub <red.cub> ... <green.cub> <blue.cub> <rgb.cub> '
        '<red.cub>, ..., <blue.cub> are input cubes of different bands. '
        '<rgb.cub> is an output multi-band cube')
    sys.exit()

output_fn = os.path.abspath(sys.argv[-1])
output_dir = os.path.dirname(output_fn)
input_list_fn = []

for index in range(1, len(sys.argv) - 1):
    input_list_fn.append(os.path.abspath(sys.argv[index]))

# check input
assert os.environ.get('ISISROOT') is not None, 'ISIS is not installed properly'
assert os.path.isdir(output_dir), 'Folder %s does not exist' % (output_dir)
for input_fn in input_list_fn:
    assert os.path.isfile(input_fn), 'File %s does not exist' % (input_fn)

cub_lis = tempfile.mktemp()
untrimmed_mosaic = tempfile.mktemp(suffix='.cub')

# make list
with open(cub_lis, 'w') as file:
    for input_fn in input_list_fn:
        file.write("%s\n" % input_fn)

# join cubes
exe_str = 'cubeit fromlist="%s" to="%s"' % (cub_lis, untrimmed_mosaic)
print 'Calling %s' % exe_str
os.system(exe_str)

# trim areas which do not have all bands
exe_str = 'bandtrim from="%s" to="%s"' % (
    untrimmed_mosaic, output_fn)
os.system(exe_str)

os.remove(cub_lis)
