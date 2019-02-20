#!/usr/bin/env python
from datetime import datetime
import argparse
import csv
import os
import sys

import tgocassis_utils

FILE_LIST_PATTERN = '{}_{}_{}.lis'


def _find_start_and_end_time(filenames):
    start_time = datetime.max
    end_time = datetime.min
    for filename in filenames:
        time_string = tgocassis_utils.parse_filename(filename)['time_string']
        time = tgocassis_utils.time_str2timeobj(time_string)
        if time < start_time:
            start_time = time
        if time > end_time:
            end_time = time
    return (start_time, end_time)


def main():
    parser = argparse.ArgumentParser(
        description=
        'Function finds all sequence in the folder with level1 / level2 data.')
    parser.add_argument(
        '-from',
        dest='cassis_folder',
        help='folder with level1 / level2 data',
        required=True)
    args = parser.parse_args()
    cassis_folder = os.path.abspath(args.cassis_folder)
    filenames = tgocassis_utils.find_xml_files(cassis_folder)
    if not filenames:
        print('There are no files in the specified folder.')
        sys.exit()
    # make summary file
    summary_file = open(os.path.join(cassis_folder, 'summary.csv'), 'wb')
    field_names = ['sequence_type', 'observation_name', 'band', 'start_time',
        'end_time', 'number_of_framelets', 'height', 'width', 'start_row',
        'end_row', 'start_column', 'end_column'
    ]
    summary_writer = csv.DictWriter(
        summary_file, delimiter=',', fieldnames=field_names)
    summary_writer.writeheader()
    filenames_by_sequence_type = tgocassis_utils.split_by_sequence_type(
        filenames)
    for sequence_type, filenames in filenames_by_sequence_type.items():
        filenames_by_observation_name = tgocassis_utils.split_by_observation_name(
            filenames)
        for observation_name, filenames in filenames_by_observation_name.items(
        ):
            start_time, end_time = _find_start_and_end_time(filenames)
            filenames_by_band = tgocassis_utils.split_by_band(filenames)
            for band, filenames in filenames_by_band.items():
                number_of_framelets = len(filenames)
                height = width = start_row = end_row = start_column = end_column = 0
                if number_of_framelets > 0:
                    filename = filenames[0]
                    info = tgocassis_utils.parse_xml(filename)
                    start_row = info['window_start_row']
                    end_row = info['window_end_row']
                    start_column = info['window_start_column']
                    end_column = info['window_end_column']
                    height = end_row - start_row + 1
                    width = end_column - start_column + 1
                basename_without_extension = [
                    os.path.basename(filename.rstrip('.xml'))
                    for filename in filenames
                ]
                tgocassis_utils.write_lines_list(
                    os.path.join(
                        cassis_folder,
                        FILE_LIST_PATTERN.format(observation_name,
                                                 sequence_type, band)),
                    basename_without_extension)
                print('{}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}\n'.
                      format(sequence_type,
                             observation_name, band, start_time, end_time,
                             number_of_framelets, height, width, start_row,
                             end_row, start_column, end_column))
                summary_writer.writerow({
                    'sequence_type':
                    sequence_type,
                    'observation_name':
                    observation_name,
                    'band':
                    band,
                    'start_time':
                    start_time,
                    'end_time':
                    end_time,
                    'number_of_framelets':
                    number_of_framelets,
                    'height':
                    height,
                    'width':
                    width,
                    'start_row':
                    start_row,
                    'end_row':
                    end_row,
                    'start_column':
                    start_column,
                    'end_column':
                    end_column
                })
    summary_file.close()
    return 1


if __name__ == '__main__':
    main()
