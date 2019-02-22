#!/usr/bin/env python
"""Automatically processes CaSSIS level1(a,b,c) observations.

Args:
    input_folder: folder with level1(a,b,c) framelets.
    output_folder: folder with processed observations. Each observation is
                   placed in individual folder. For "mono" observations
                   the scripts reconstructs map-projected color mosaic, which
                   is (optionally) bundle-adjusted. For "stereo" observations
                   the script reconstructs two map-projected color mosaics,
                   which are (optionally) bundle-adjusted, and
                   (optionally) computes disparity image and DTMs.
    no_ba: if flag is True, the script will not perform bundle adjustment.
    no_dtm: if flag is True, the scipts will not compute disparity image
            and DTMs for every observation.
    debug: if flag is True, the script keeps all intermediated results,
           otherwise they are deleted.
    observation: process only specified observation. Multiple observations ca
                 can be specified (see example call). Observation name should
                 not contain observation type digit, i.e., it should be
                 MY34_004204_186 no MY34_004204_186_1.

Example:
    tgocassis_process.py \
        "/level1c"
        "/processed"
        --no_ba
        --no_dtm
        --debug
        --observation MY34_004204_186
        --observation MY34_004204_235
"""

import os
import click
import shutil
import csv
from distutils import spawn

MINIMUM_FRAMELET_AREA = 10000


def _remove_temporary_files_and_folders(folder):
    files_and_folders = os.listdir(folder)
    print(files_and_folders)
    for file_or_folder in files_and_folders:
        path_to_file_or_folder = os.path.join(folder, file_or_folder)
        if os.path.isdir(path_to_file_or_folder):
            shutil.rmtree(path_to_file_or_folder)
        else:
            if not ('disparity' in file_or_folder or 'dtm' in file_or_folder
                    or 'colormosaic' in file_or_folder):
                os.remove(path_to_file_or_folder)


def _clean_up_folder(folder_to_remove):
    for root, folders, files in os.walk(folder_to_remove):
        for file in files:
            os.unlink(os.path.join(root, file))
        for folder in folders:
            shutil.rmtree(os.path.join(root, folder))


def _filter_by_observation_name(sequences, observation_name):
    return [
        row for row in sequences if row['observation_name'] == observation_name
    ]


def _filter_by_sequence_type(sequences, sequences_type):
    return [row for row in sequences if row['sequence_type'] == sequences_type]


@click.command()
@click.argument('input_folder', type=click.Path(exists=True))
@click.argument('output_folder', type=click.Path(exists=False))
@click.option('--no_ba', is_flag=True)
@click.option('--no_dtm', is_flag=True)
@click.option('--debug', is_flag=True)
@click.option('--observation', multiple=True)
def main(input_folder, output_folder, no_ba, no_dtm, debug, observation):
    from_folder = os.path.abspath(input_folder)
    to_folder = os.path.abspath(output_folder)
    ba = 'yes'
    if no_ba:
        ba = 'no'
    assert os.environ.get(
        'ISISROOT') is not None, 'ISIS is not installed properly.'
    assert spawn.find_executable(
        'tgocassis_triangulate') is not None, 'tgocassis_triangulate '
    ' ISIS application is not installed properly.'
    assert spawn.find_executable(
        'stereo') is not None, 'ASP is not installed properly.'

    # Clear output path.
    _clean_up_folder(output_folder)

    # Browse input folder.
    execution_string = 'tgocassis_findSeq.py -from {}'.format(from_folder)
    os.system(execution_string)

    # Read summary.
    summary_filename = os.path.join(from_folder, 'summary.csv')
    summary_file = open(summary_filename)
    summary_reader = csv.DictReader(summary_file)
    sequences_summary = list(summary_reader)
    if observation:
        observation_names = observation
    else:
        observation_names = set(
            [sequence['observation_name'] for sequence in sequences_summary])
    for observation_name in observation_names:
        observation_sequences = _filter_by_observation_name(
            sequences_summary, observation_name)
        sequence_types = set(
            [sequence['sequence_type'] for sequence in observation_sequences])
        bands = {}
        framelet_lists = {}
        for sequence_type in sequence_types:
            sequence_bands = _filter_by_sequence_type(observation_sequences,
                                                      sequence_type)
            framelet_lists[sequence_type] = []
            bands[sequence_type] = []

            for band in sequence_bands:
                (height, width, band_name) = (int(band['height']),
                                              int(band['width']), band['band'])
                if height * width > MINIMUM_FRAMELET_AREA:
                    framelet_lists[sequence_type].append(
                        os.path.join(
                            from_folder, '{}_{}_{}.lis'.format(
                                observation_name, sequence_type, band_name)))
                    bands[sequence_type].append(band_name)
        if len(sequence_types) == 1:
            # Mono mode.
            observation_folder = os.path.join(
                to_folder, '{}_mono'.format(observation_name))
            os.makedirs(observation_folder)
            execution_string = 'tgocassis_mapproj_mosaic.py -from {} -to {} -ba {}'.format(
                " ".join(framelet_lists['mono']), observation_folder, ba)
            os.system(execution_string)
        else:
            # Stereo mode.
            observation_folder = os.path.join(
                to_folder, '{}_stereo'.format(observation_name))
            os.makedirs(observation_folder)
            execution_string = 'tgocassis_mapproj_mosaic.py -from {} -from1 {} -to {} -ba {}'.format(
                " ".join(framelet_lists['first_stereo']), " ".join(
                    framelet_lists['second_stereo']), observation_folder, ba)
            os.system(execution_string)
            if not no_dtm:
                first_mosaic_framelets_folder = os.path.join(
                    observation_folder,
                    '{}_first_stereo_PAN_MAP'.format(observation_name))
                second_mosaic_framelets_folder = os.path.join(
                    observation_folder,
                    '{}_second_stereo_PAN_MAP'.format(observation_name))
                first_mosaic_filename = os.path.join(
                    observation_folder,
                    '{}_first_stereo_PAN_MOS.cub'.format(observation_name))
                second_mosaic_filename = os.path.join(
                    observation_folder,
                    '{}_second_stereo_PAN_MOS.cub'.format(observation_name))
                disparity_filename = os.path.join(
                    observation_folder,
                    '{}_disparity.tif'.format(observation_name))
                dtm_filename = os.path.join(
                    observation_folder, '{}_dtm.cub'.format(observation_name))
                execution_string = 'tgocassis_clcDisp.py {} {} {}'.format(
                    first_mosaic_filename, second_mosaic_filename,
                    disparity_filename)
                os.system(execution_string)
                execution_string = 'tgocassis_triangulate ASP_DISP={} MOSAIC0={} MOSAIC1={} MAPPROJ_FRAMELETS0_DIR={} MAPPROJ_FRAMELETS1_DIR={} TO={}'.format(
                    disparity_filename, first_mosaic_filename,
                    second_mosaic_filename, first_mosaic_framelets_folder,
                    second_mosaic_framelets_folder, dtm_filename)
                os.system(execution_string)
        if not debug:
            _remove_temporary_files_and_folders(observation_folder)


if __name__ == '__main__':
    main()