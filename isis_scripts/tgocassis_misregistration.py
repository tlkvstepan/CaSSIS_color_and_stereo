#!/usr/bin/env python
"""Automatically compute bands misregistration in mosaics.

Args:
    path_to_input_folder: Folder (possibly with subfolders) that contains mosaics.
                 column contains name of the mosaic, the second x-shift and
                 the third y-shift.
    source_band: band that will be translated.
    target_band: band to which we will translate the source band.

If source or target band does not exist in the mosaic, mosaic is ignored.

Example:
    tgocassis_misregistration.py \
        "/isis"
        "misregistration.csv"
        --source_band RED
        --target_band NIR
        --visualize 
"""
import click
import commands
import os
import tempfile

import matplotlib.pyplot as plt
from mpl_toolkits import axes_grid1
from scipy import interpolate
import numpy as np


def _add_scaled_colorbar(plot, aspect=20, pad_fraction=0.5, **kwargs):
    """Adds scaled colorbar to existing plot."""
    divider = axes_grid1.make_axes_locatable(plot.axes)
    width = axes_grid1.axes_size.AxesY(plot.axes, aspect=1. / aspect)
    pad = axes_grid1.axes_size.Fraction(pad_fraction, width)
    current_axis = plt.gca()
    cax = divider.append_axes("right", size=width, pad=pad)
    plt.sca(current_axis)
    return plot.axes.figure.colorbar(plot, cax=cax, **kwargs)


def save_matrix(filename,
                matrix,
                minimum_value=None,
                maximum_value=None,
                colormap='magma',
                is_colorbar=True):
    """Saves the matrix to the image file.

    Args:
        filename: image file where the matrix will be saved.
        matrix: tensor of size (height x width). Some values might be
                equal to inf.
        minimum_value, maximum value: boundaries of the range.
                                      Values outside ot the range are
                                      shown in white. The colors of other
                                      values are determined by the colormap.
                                      If maximum and minimum values are not
                                      given they are calculated as 0.001 and
                                      0.999 quantile.
        colormap: map that determines color coding of matrix values.
    """
    figure = plt.figure()
    noninf_mask = ~np.isnan(matrix)
    if minimum_value is None:
        minimum_value = np.percentile(matrix[noninf_mask], 1)
    if maximum_value is None:
        maximum_value = np.percentile(matrix[noninf_mask], 99)
    plot = plt.imshow(matrix, colormap, vmin=minimum_value, vmax=maximum_value)
    if is_colorbar:
        _add_scaled_colorbar(plot)
    plot.axes.get_xaxis().set_visible(False)
    plot.axes.get_yaxis().set_visible(False)
    figure.savefig(filename, bbox_inches='tight', dpi=200)
    plt.close()


def _bands(mosaic_filename):
    """Returns list of bands in a mosaics (ISIS CUB).

    Args: 
        mosaic_filename: filename of ISIS CUB mosaic.
    """
    exec_string = 'catlab from={}'.format(mosaic_filename)
    _, output_string = commands.getstatusoutput(exec_string)
    start_of_filters_list = output_string.find('FilterName = (') + 14
    end_of_filters_list = output_string.find(')\n', start_of_filters_list)
    filters_string = output_string[start_of_filters_list:end_of_filters_list]
    return filters_string.split(', ')


def _basename_wo_extension(path_to_file):
    return os.path.basename(path_to_file).split('.')[0]


def _explode(mosaic_filename):
    """Returns band of a mosaic (ISIS CUB).

    Args: 
        mosaic_filename: filename of ISIS CUB mosaic.
    """
    basename = _basename_wo_extension(mosaic_filename)
    explode_prefix = os.path.join(tempfile.mkdtemp(), basename)
    exec_string = 'explode from={} to={}'.format(mosaic_filename,
                                                 explode_prefix)
    os.system(exec_string)
    bands_list = _bands(mosaic_filename)
    path_to_band_files = {}
    for band_index, band_name in enumerate(bands_list):
        path_to_band_files[
            band_name] = explode_prefix + '.band{:04d}.cub'.format(band_index +
                                                                   1)
    return path_to_band_files


def _search_deffile():
    search_deffile = tempfile.mkstemp(suffix='.def')[1]
    with open(search_deffile, 'w') as f:
        content_str = """ 
        Object = AutoRegistration
           Group = Algorithm
             Name = MaximumCorrelation
             Tolerance = 0.1
           EndGroup
           Group = PatternChip
             Samples = 30
             Lines   = 30 
             MinimumZScore = 1e-5
           EndGroup
           Group = SearchChip
             Samples = 50 
             Lines   = 50 
           EndGroup
        EndObject
        """
        f.write(content_str)
    return search_deffile


def _register(source_filename, target_filename):
    results_filename = tempfile.mkstemp(suffix='.txt')[1]
    search_deffile = _search_deffile()
    exec_string = 'coreg from={} match={} deffile={} flatfile={}'.format(
        source_filename, target_filename, search_deffile, results_filename)
    commands.getstatusoutput(exec_string)
    (x_source, y_source, _, _, x_shift, y_shift, _) = np.loadtxt(
        results_filename, skiprows=1, delimiter=',').T
    return x_source, y_source, x_shift, y_shift


def _compute_bands_mismatch(mosaic_filename, source_band, target_band):
    bands_files = _explode(mosaic_filename)
    if ((source_band not in bands_files) or (target_band not in bands_files)):
        return None
    (x_source, y_source, x_shift, y_shift) = _register(
        bands_files[source_band], bands_files[target_band])
    return x_source, y_source, x_shift, y_shift


@click.command()
@click.argument('path_to_input_folder', type=click.Path(exists=True))
@click.option('--source_band', default='PAN')
@click.option('--target_band', is_flag='NIR')
@click.option('--visualize', is_flag=True)
def main(path_to_input_folder, source_band, target_band, visualize):
    path_to_input_folder = os.path.abspath(path_to_input_folder)
    x_shifts = []
    y_shifts = []
    shifts = []
    filenames = []
    for directory, _, files_list in os.walk(path_to_input_folder):
        for filename in files_list:
            if '.cub' in filename:
                path_to_input_file = os.path.join(directory, filename)
                result = _compute_bands_mismatch(path_to_input_file,
                                                 source_band, target_band)
                if result is not None:
                    (x_source, y_source, x_shift, y_shift) = result
                    if visualize:
                        path_to_x_shift_visualization_file = os.path.join(
                            directory, filename[:-4] + '_x_shift.pdf')
                        path_to_y_shift_visualization_file = os.path.join(
                            directory, filename[:-4] + '_y_shift.pdf')
                        points = (x_source, y_source)
                        x_grid, y_grid = np.meshgrid(
                            np.arange(x_source.min(), x_source.max(), 5),
                            np.arange(y_source.min(), y_source.max(), 5))
                        x_shift_visualization = interpolate.griddata(
                            points, x_shift, (x_grid, y_grid), method='linear')
                        y_shift_visualization = interpolate.griddata(
                            points, y_shift, (x_grid, y_grid), method='linear')
                        save_matrix(
                            path_to_x_shift_visualization_file,
                            x_shift_visualization,
                            colormap='magma',
                            is_colorbar=True)
                        save_matrix(
                            path_to_y_shift_visualization_file,
                            y_shift_visualization,
                            colormap='magma',
                            is_colorbar=True)
                    x_shifts.append(np.median(x_shift))
                    y_shifts.append(np.median(y_shift))
                    shifts.append(np.median(np.sqrt(x_shift**2 + y_shift**2)))
                    filenames.append(filename)
    print('In total {} files processed'.format(len(filenames)))
    print('x-misalignment: {}+/-{}'.format(
        np.mean(x_shifts), np.std(x_shifts)))
    print('y-misalignment: {}+/-{}'.format(
        np.mean(y_shifts), np.std(y_shifts)))
    print('Euclidian misalignment: {}+/-{}'.format(
        np.mean(shifts), np.std(shifts)))
