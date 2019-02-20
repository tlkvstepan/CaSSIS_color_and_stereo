#!/usr/bin/env python
import sys
import os
from shutil import copyfile

if len(sys.argv) < 3:
    print('tgocassis_copySeq <seq.lis> <seq_dir>')
    print('<seq.lis> are files with list of framelets. \n'
          '<seq_dir> is an output directory')
    sys.exit()

seq_file = sys.argv[1]
output_dir = sys.argv[2]
input_dir = os.path.dirname(seq_file)

# check input
assert os.environ.get('ISISROOT') is not None, 'ISIS is not installed properly'
assert os.path.isfile(seq_file), 'File %s does not exist' % (seq_file)
assert os.path.isdir(output_dir), 'Folder %s does not exist' % (output_dir)

with open(seq_file) as file:
    framelet_list = file.readlines()
    framelet_list = [framelet.rstrip('\n') for framelet in framelet_list]
    for framelet in framelet_list:
        copyfile(
            os.path.join(input_dir, framelet + '.xml'),
            os.path.join(output_dir, framelet + '.xml'))
        copyfile(
            os.path.join(input_dir, framelet + '.dat'),
            os.path.join(output_dir, framelet + '.dat'))
