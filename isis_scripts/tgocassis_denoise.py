#!/usr/bin/env python
import sys
import tempfile
import os
import shutil


if len(sys.argv) < 3:
    print(
        'tgocassis_denoise <cub_dir> <denoise_cub_dir> \n'
        '<cub_dir> is an input directories containing cubes.\n'
        '<denoise_cub_dir> is an output directory containing denoised cubes.\n'
    )
    sys.exit()

# convert to absolute path
cub_dir = os.path.abspath(sys.argv[1])
denoise_dir = os.path.abspath(sys.argv[2])

print cub_dir
print denoise_dir

# check input
assert os.environ.get('ISISROOT') is not None, 'ISIS is not installed properly'
assert os.path.isdir(cub_dir), 'Folder %s does not exist' % (cub_dir)
assert os.path.isdir(denoise_dir), 'Folder %s does not exist' % (denoise_dir)

# make cube list
cublis_fn = tempfile.mktemp()
exe_str = 'ls "%s/"*".cub"  | xargs -n 1 basename > %s' % (cub_dir, cublis_fn)
os.system(exe_str)

# denoise
denoise1_dir = tempfile.mkdtemp()
exe_str = 'median from="%s/\$1" to="%s/\$1" samples=3 lines=3 filter=all replacement=null -batchlist="%s"' % (
    cub_dir, denoise1_dir, cublis_fn)
os.system(exe_str)
exe_str = 'lowpass from="%s/\$1" to="%s/\$1" samples=3 lines=3 filter=all null=yes hrs=no his=no lrs=no replacement=null -batchlist="%s"' % (
    denoise1_dir, denoise_dir, cublis_fn)
os.system(exe_str)

shutil.rmtree(denoise1_dir)
os.remove(cublis_fn)
