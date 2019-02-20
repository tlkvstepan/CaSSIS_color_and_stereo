#!/usr/bin/env python

import sys
import os
import glob
import tempfile

if len(sys.argv) < 3:
    print('tgocassis_2isis <seq_dir> <cub_dir>')
    print('<seq_dir> is directory containing framelets.\n'
          '<cub_dir> is an output directory with spiced cubes')
    sys.exit()

input_dir = sys.argv[1]
output_dir = sys.argv[2]

# check input
assert os.environ.get('ISISROOT') is not None, 'ISIS is not installed properly'
assert os.path.isdir(input_dir), 'Folder %s does not exist' % (input_dir)

seqlist_file = tempfile.mktemp()

# make list
seqlist = glob.glob(os.path.join(input_dir, "*.xml"))
with open(seqlist_file, 'w') as file:
    for framelet in seqlist:
        file.write("%s\n" % os.path.basename(framelet).rstrip('.xml'))

# convert to ISIS and spice up
exe_str = 'tgocassis2isis from="%s/\$1.xml" to="%s/\$1.cub" -batchlist=%s' % (
    input_dir, output_dir, seqlist_file)
os.system(exe_str)

exe_str = 'spiceinit from="%s/\$1.cub" ckp=t spkp=t -batchlist=%s' % (
    output_dir, seqlist_file)
os.system(exe_str)

os.remove(seqlist_file)
