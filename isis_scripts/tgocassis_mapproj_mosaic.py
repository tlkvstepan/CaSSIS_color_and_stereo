#!/usr/bin/env python
import argparse
import os
import shutil
import sys

parser = argparse.ArgumentParser(
    description=
    'Function creates map-projected color mosaic cube and saves all intermediate results.'
)

parser.add_argument(
    '-from',
    metavar='framelets.lis',
    dest='framelet_lists',
    nargs='+',
    help='files with a list of framelets for the first stereo image',
    required=True)

parser.add_argument(
    '-from1',
    metavar='framelets.lis',
    dest='framelet_lists1',
    nargs='+',
    help='files with a list of framelets for the second stereo image')

parser.add_argument(
    '-to',
    metavar='out_dir',
    dest='out_dir',
    help='output directory',
    required=True)

parser.add_argument(
    '-ba', dest='ba', default='no', help='perform bundle adjustment')

parser.add_argument(
    '-match_tone',
    dest='match_tone',
    default='no',
    help='perform tone matching')

args = parser.parse_args()

if (args.ba == 'no' or args.ba == 'No' or args.ba == 'NO' or args.ba == 'FALSE'
        or args.ba == 'false' or args.ba == 'False'):
    args.ba = False
else:
    args.ba = True

# check input
assert os.environ.get('ISISROOT') is not None, 'ISIS is not installed properly'
assert os.path.isdir(args.out_dir), 'Folder %s does not exist' % (args.out_dir)

stereo_framelet_lists = []
stereo_framelet_lists.append(args.framelet_lists)
if args.framelet_lists1 is not None:
    stereo_framelet_lists.append(args.framelet_lists1)

for i, sequence_framelet_lists in enumerate(stereo_framelet_lists):
    for band_framelet_lists in sequence_framelet_lists:
        assert os.path.isfile(
            band_framelet_lists), 'File %s does not exist' % (
                band_framelet_lists)
    stereo_framelet_lists[i] = [
        band_framelet_lists for band_framelet_lists in sequence_framelet_lists
        if os.stat(band_framelet_lists).st_size != 0
    ]

#empty output folder
for root, dirs, files in os.walk(args.out_dir):
    for f in files:
        os.unlink(os.path.join(root, f))
    for d in dirs:
        shutil.rmtree(os.path.join(root, d))

map_file = os.path.join(args.out_dir, 'common.map')

stereo_level2_dirs = []
stereo_cube_dirs = []
stereo_mapproj_dirs = []
stereo_mosaic_files = []
stereo_colormosaic_files = []
stereo_browse_files = []
stereo_denoise_dirs = []
stereo_trim_dirs = []

if args.ba: stereo_ba_dirs = []

for index, sequence_framelet_lists in enumerate(stereo_framelet_lists):

    sequence_name = os.path.basename(
        sequence_framelet_lists[0])[:-8] + '_' + '_'.join(
            band_framelet_list[-7:-4]
            for band_framelet_list in sequence_framelet_lists)
    colormosaic_file = os.path.join(args.out_dir,
                                    sequence_name + '_colormosaic.cub')
    # in browse file we can save only 3 channel
    sequence_name = os.path.basename(
        sequence_framelet_lists[0])[:-8] + '_' + '_'.join([
            sequence_framelet_lists[min(
                i,
                len(sequence_framelet_lists) - 1)][-7:-4] for i in range(0, 3)
        ])
    browse_file = os.path.join(args.out_dir,
                               sequence_name + '_colormosaic.png')

    stereo_colormosaic_files.append(colormosaic_file)
    stereo_browse_files.append(browse_file)

    sequence_level2_dirs = {}
    sequence_cube_dirs = {}
    sequence_mapproj_dirs = {}
    sequence_mosaic_files = {}
    sequence_denoise_dirs = {}
    sequence_trim_dirs = {}

    if args.ba: sequence_ba_dirs = {}

    for band_framelet_list in sequence_framelet_lists:

        band_id = band_framelet_list[-7:-4]

        base = os.path.basename(band_framelet_list)[:-4]

        band_level2_dir = os.path.join(args.out_dir, base + '_SEQ')
        band_cube_dir = os.path.join(args.out_dir, base + '_CUB')
        band_mapproj_dir = os.path.join(args.out_dir, base + '_MAP')

        band_mosaic_file = os.path.join(args.out_dir, base + '_MOS.cub')

        sequence_level2_dirs[band_id] = band_level2_dir
        sequence_cube_dirs[band_id] = band_cube_dir
        sequence_mapproj_dirs[band_id] = band_mapproj_dir
        sequence_mosaic_files[band_id] = band_mosaic_file

        # folders for triming blu band
        if band_id == 'BLU':
            band_trim_dir = os.path.join(args.out_dir, base + '_TRIM')
            sequence_trim_dirs[band_id] = band_trim_dir
            os.makedirs(band_trim_dir)

        # folders for denoising nir and blu
        if band_id in ['NIR', 'BLU']:
            band_denoise_dir = os.path.join(args.out_dir, base + '_DENOISE')
            sequence_denoise_dirs[band_id] = band_denoise_dir
            os.makedirs(band_denoise_dir)

        # folders for ba (if needed)
        if args.ba:
            if band_id in ['NIR', 'BLU']:
                band_ba_dirs = os.path.join(args.out_dir, base + '_DENOISE_BA')
            else:
                band_ba_dirs = os.path.join(args.out_dir, base + '_CUB_BA')
            sequence_ba_dirs[band_id] = band_ba_dirs
            # note that ba automatically creates output folders..

        # create dirs
        os.makedirs(band_level2_dir)
        os.makedirs(band_cube_dir)
        os.makedirs(band_mapproj_dir)

        # copy level2
        exe_str = 'tgocassis_copySeq.py "%s" "%s" ' % (band_framelet_list,
                                                       band_level2_dir)
        os.system(exe_str)

        # convert to cube
        exe_str = 'tgocassis_2isis.py "%s" "%s" ' % (band_level2_dir,
                                                     band_cube_dir)
        os.system(exe_str)

        if band_id == 'BLU':
            # trim last BLU
            exe_str = 'tgocassis_trim.py "%s" "%s" ' % (band_cube_dir,
                                                        band_trim_dir)
            os.system(exe_str)
            # filter BLU
            exe_str = 'tgocassis_denoise.py "%s" "%s" ' % (band_trim_dir,
                                                           band_denoise_dir)
            os.system(exe_str)

        if band_id == 'NIR':
            # filter NIR
            exe_str = 'tgocassis_denoise.py "%s" "%s" ' % (band_cube_dir,
                                                           band_denoise_dir)
            os.system(exe_str)

    stereo_level2_dirs.append(sequence_level2_dirs)
    stereo_cube_dirs.append(sequence_cube_dirs)
    stereo_denoise_dirs.append(sequence_denoise_dirs)
    stereo_mapproj_dirs.append(sequence_mapproj_dirs)
    stereo_mosaic_files.append(sequence_mosaic_files)

    if args.ba: stereo_ba_dirs.append(sequence_ba_dirs)

# ba
if args.ba:
    for nsequence, sequence_framelet_lists in enumerate(stereo_framelet_lists):

        # make list dirs with cubes
        band_dirs = []
        for band_id, _ in stereo_cube_dirs[nsequence].iteritems():
            if band_id in ['NIR', 'BLU']:
                band_dirs.append('"' +
                                 stereo_denoise_dirs[nsequence][band_id] + '"')
            else:
                band_dirs.append('"' + stereo_cube_dirs[nsequence][band_id] +
                                 '"')
        band_dirs_string = ' '.join(band_dirs)

        exe_str = 'tgocassis_ba.py -inp_dirs %s' % (band_dirs_string)
        os.system(exe_str)

        if os.listdir(stereo_ba_dirs[nsequence][list(
                stereo_ba_dirs[nsequence].keys())[0]]) == []:
            sys.exit('BA failed')

# create map-projection map using the first and the second sequence
all_dirs = []
if args.ba:

    # make list of all cubes in both sequences
    for nsequence, sequence_framelet_lists in enumerate(stereo_framelet_lists):
        for band_id, _ in stereo_cube_dirs[nsequence].iteritems():
            all_dirs.append('"' + stereo_ba_dirs[nsequence][band_id] + '"')
    all_dirs_string = ' '.join(all_dirs)

else:

    # make list of cube in both sequences
    for nsequence, sequence_framelet_lists in enumerate(stereo_framelet_lists):
        for band_id, _ in stereo_cube_dirs[nsequence].iteritems():
            if band_id in ['NIR', 'BLU']:
                all_dirs.append('"' + stereo_denoise_dirs[nsequence][band_id] +
                                '"')
            else:
                all_dirs.append('"' + stereo_cube_dirs[nsequence][band_id] +
                                '"')
    all_dirs_string = ' '.join(all_dirs)

exe_str = 'tgocassis_clcMap.py %s "%s"' % (all_dirs_string, map_file)
os.system(exe_str)

# map project and equalize
for nsequence, sequence_framelet_lists in enumerate(stereo_framelet_lists):
    for band_id, _ in stereo_cube_dirs[nsequence].iteritems():

        band_mapproj_dir = stereo_mapproj_dirs[nsequence][band_id]
        if args.ba:
            band_cube_dir = stereo_ba_dirs[nsequence][band_id]
        else:
            if band_id in ['NIR', 'BLU']:
                band_cube_dir = stereo_denoise_dirs[nsequence][band_id]
            else:
                band_cube_dir = stereo_cube_dirs[nsequence][band_id]

        band_mosaic_file = stereo_mosaic_files[nsequence][band_id]

        exe_str = 'tgocassis_mapMos.py "%s" "%s" "%s" "%s" "%s"' % (
            band_cube_dir, map_file, band_mapproj_dir, band_mosaic_file,
            args.match_tone)
        os.system(exe_str)

for nsequence, sequence_framelet_lists in enumerate(stereo_framelet_lists):

    # stack color channels
    mosaic_files_concatenated = ' '.join([
        '"' + mosaic_file + '"'
        for _, mosaic_file in stereo_mosaic_files[nsequence].iteritems()
    ])
    exe_str = 'tgocassis_stackCub.py %s "%s"' % (
        mosaic_files_concatenated, stereo_colormosaic_files[nsequence])
    os.system(exe_str)

    # create browse images
    if len(sequence_framelet_lists) >= 3:
        exe_str = 'isis2std mode=rgb red="%s"+1 green="%s"+2 blue="%s"+3 to="%s" ' % (
            stereo_colormosaic_files[nsequence],
            stereo_colormosaic_files[nsequence],
            stereo_colormosaic_files[nsequence],
            stereo_browse_files[nsequence])
    elif len(sequence_framelet_lists) == 2:
        exe_str = 'isis2std mode=rgb red="%s"+1 green="%s"+2 blue="%s"+2 to="%s" ' % (
            stereo_colormosaic_files[nsequence],
            stereo_colormosaic_files[nsequence],
            stereo_colormosaic_files[nsequence],
            stereo_browse_files[nsequence])
    else:
        exe_str = 'isis2std mode=gray from="%s"+1 green="%s"+1 blue="%s"+1 to="%s" ' % (
            stereo_colormosaic_files[nsequence],
            stereo_colormosaic_files[nsequence],
            stereo_colormosaic_files[nsequence],
            stereo_browse_files[nsequence])
    os.system(exe_str)
