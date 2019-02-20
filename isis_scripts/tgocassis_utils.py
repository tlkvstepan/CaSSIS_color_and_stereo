from collections import defaultdict
from datetime import datetime
import fnmatch
import math
import os
import re
import sys

import cv2
import numpy as np

OBSERVATION_TYPE = {
    0: 'mono',
    1: 'first_stereo',
    2: 'second_stereo'
}


def parse_xml(xml_filename):
    f = open(xml_filename, 'r')
    observation_name_pattern = '<CTF_Id>(.+)_(\d)</CTF_Id>'
    observation_type_pattern = '<CTF_Id>.+_(\d)</CTF_Id>'
    band_name_pattern = '<Filter Form="Acronym">(.+)</Filter>'
    window_counter_pattern = 'WindowCounter="(\d)"'
    window_start_row_pattern = 'Window{}_Start_Row="(\d+)"'
    window_end_row_pattern = 'Window{}_End_Row="(\d+)"'
    window_start_column_pattern = 'Window{}_Start_Col="(\d+)"'
    window_end_column_pattern = 'Window{}_End_Col="(\d+)"'
    info = {}
    if f:
        data = f.read()
        info['observation_name'] = re.search(observation_name_pattern,
                                             data).group(1)
        info['observation_type'] = OBSERVATION_TYPE[int(
            re.search(observation_type_pattern, data).group(1))]
        info['band'] = re.search(band_name_pattern, data).group(1)
        info['window_number'] = int(
            re.search(window_counter_pattern, data).group(1)) + 1
        info['window_start_row'] = int(
            re.search(
                window_start_row_pattern.format(info['window_number']),
                data).group(1)) + 1
        info['window_end_row'] = int(
            re.search(
                window_end_row_pattern.format(info['window_number']),
                data).group(1)) + 1
        info['window_start_column'] = int(
            re.search(
                window_start_column_pattern.format(info['window_number']),
                data).group(1)) + 1
        info['window_end_column'] = int(
            re.search(
                window_end_column_pattern.format(info['window_number']),
                data).group(1)) + 1
    else:
        print('Can not open %s' % xml_fname)
    f.close()
    return info


def find_imshift(trg_im, src_im):

    # shift of the source to the right / up is negative

    bf = cv2.BFMatcher()

    # Initiate FAST detector
    star = cv2.xfeatures2d.StarDetector_create()

    # Initiate BRIEF extractor
    brief = cv2.xfeatures2d.BriefDescriptorExtractor_create()

    # find the keypoints with STAR
    kpTrg = star.detect(trg_im, None)
    kpSrc = star.detect(src_im, None)

    kpTrg, desTrg = brief.compute(trg_im, kpTrg)
    kpSrc, desSrc = brief.compute(src_im, kpSrc)

    matches = bf.knnMatch(desTrg, desSrc, k=2)

    #ratio test
    good_matches = []
    for m, n in matches:
        if m.distance < 0.75 * n.distance:
            good_matches.append([m])

    # thresholding
    dx = []
    dy = []
    for match in good_matches:
        dx_local = kpTrg[match[0].queryIdx].pt[0] - kpSrc[match[0].
                                                          trainIdx].pt[0]
        dy_local = kpTrg[match[0].queryIdx].pt[1] - kpSrc[match[0].
                                                          trainIdx].pt[1]
        if math.sqrt(dx_local * dx_local + dy_local * dy_local) < 100:
            dx.append(dx_local)
            dy.append(dy_local)

    dx_med = np.median(np.array(dx))
    dy_med = np.median(np.array(dy))

    return dx_med, dy_med


def write_subExp(im, dat_fname):

    h, w = im.shape
    f = open(dat_fname, 'wb')
    if f:
        # level1 - float (32bit), level0 - uint16
        raw_data = im.reshape((h * w))
        raw_data.astype(np.float32).tofile(f)
        f.close()
        return True
    else:
        print('Can not open %s' % dat_fname)
        return False


def read_framelet(xml_filename):
    dat_fname = xml_filename[:-4] + '.dat'
    info = parse_xml(xml_filename)
    w = info['window_end_column'] - info['window_start_column'] + 1
    h = info['window_end_row'] - info['window_start_row'] + 1
    im = []
    f = open(dat_fname, 'rb')
    if f:
        # level1 - float (32bit), level0 - uint16
        raw_data = np.fromfile(f, dtype=np.float32, count=-1)
        h_actual = raw_data.size / w
        if (h_actual < h):
            print('dataloss detected')
        im = raw_data.reshape((h_actual, w))
        f.close()
    else:
        print('Can not open %s' % xml_filename)
    return (im, info)


def time_str2timeobj(timeStr):
    return datetime.strptime(timeStr, '%Y-%m-%dT%H.%M.%S.%f')


def split_by_band(filenames):
    filenames_by_band = {'RED': [], 'NIR': [], 'BLU': [], 'PAN': []}
    for filename in filenames:
        filenames_by_band[parse_filename(filename)['band']].append(filename)
    return filenames_by_band


def split_by_observation_name(filenames):
    filenames_by_observation_name = defaultdict(lambda: [])
    for filename in filenames:
        filenames_by_observation_name[parse_xml(filename)
                                      ['observation_name']].append(filename)
    return filenames_by_observation_name


def split_by_sequence_type(filenames):
    filenames_by_sequence_type = defaultdict(lambda: [])
    for filename in filenames:
        filenames_by_sequence_type[parse_xml(filename)
                                      ['observation_type']].append(filename)
    return filenames_by_sequence_type


def find_xml_files(path):
    filenames = []
    for filename in os.listdir(path):
        if not fnmatch.fnmatch(filename, '*.xml'):
            continue
        filenames.append(os.path.join(path, filename))
    return filenames


def parse_filename(filename):
    pattern = '\w+-\w+-(\d\d\d\d-\d\d-\d\dT\d\d.\d\d.\d\d.\d\d\d)-(\w+)-\d\d(\d\d\d)-\w+.xml'
    match = re.search(pattern, filename)
    if match:
        time_string = match.group(1)
        band = match.group(2)
        exposure_number = match.group(3)
    else:
        print('failed to parse filename %s', filename)
        sys.exit()
    return {
        'filename': filename,
        'time_string': time_string,
        'band': band,
        'exposure_number': exposure_number
    }


def write_lines_list(fname, lines_list):
    f = open(fname, 'w')
    if f:
        for item in lines_list:
            f.write("%s\n" % item)
        f.close()
        return True
    else:
        print('can not open %s' % fname)
        return False


def read_lines_list(fname):
    f = open(fname)
    if f:
        list = f.read().splitlines()
        f.close()
        return list
    else:
        print('can not open %s' % fname)
        sys.exit()
        return []


if __name__ == '__main__':
    main()
