#!/usr/bin/env python

import sys
import tempfile
import os

if len(sys.argv) < 2:
    print('tgocassis_trim <cub_dir0> <cub_dir1 - optional> <file.map> \n'
          '<inp_dir> is directory containing cubes.\n'
          '<out_dir> is an output directory containing trimed cubes.')
    sys.exit()

inp_dir = os.path.abspath(sys.argv[1])
out_dir = os.path.abspath(sys.argv[2])

assert os.environ.get('ISISROOT') is not None, 'ISIS is not installed properly'
assert os.path.isdir(inp_dir), 'Folder %s does not exist' % (inp_dir)
assert os.path.isdir(out_dir), 'Folder %s does not exist' % (out_dir)

# make cube listlist
cubeslis_file = tempfile.mktemp()
exe_str = 'ls "%s/"*"cub" | xargs -n 1 basename >> "%s"' % (inp_dir,
                                                            cubeslis_file)
os.system(exe_str)

# trim
exe_str = 'trim  from="%s/\$1" to="%s/\$1" bottom=5 top=5 -batchlist="%s"' % (
    inp_dir, out_dir, cubeslis_file)
os.system(exe_str)

os.remove(cubeslis_file)
