#!/usr/bin/env python3

# The MIT License (MIT)
# =====================
#
# Copyright © 2020 Azavea
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the “Software”), to deal in the Software without
# restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following
# conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.

import argparse
import ast
import copy
import json
import os
import sys

import numpy as np

import rasterio as rio
import scipy.ndimage


def cli_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument('--input-path', required=True, type=str)
    parser.add_argument('--name', required=True, type=str)
    parser.add_argument('--output-path', required=True, type=str)
    return parser


if __name__ == '__main__':
    args = cli_parser().parse_args()

    cloudless_vrt = '/tmp/cloudless.vrt'
    cloudy_vrt = '/tmp/cloudy.vrt'
    cloudless_tif = '/tmp/{}-cloudless.tif'.format(args.name)
    cloudy_tif = '/tmp/{}-cloudy.tif'.format(args.name)

    # Download
    os.system('aws s3 sync {} /tmp/'.format(args.input_path))

    # Build VRTs
    os.system('gdalbuildvrt {} $(ls -r /tmp/backstop*.tif)'.format(cloudy_vrt))
    os.system(
        'gdalbuildvrt {} $(ls -r /tmp/backstop*.tif) $(ls -r /tmp/*.tif | grep -v backstop)'.format(cloudless_vrt))

    # Produce final images
    os.system('gdalwarp {} -co COMPRESS=DEFLATE -co PREDICTOR=2 -co TILED=YES -co SPARSE_OK=YES -co BIGTIFF=YES {}'.format(cloudy_vrt, cloudy_tif))
    os.system('gdalwarp {} -co COMPRESS=DEFLATE -co PREDICTOR=2 -co TILED=YES -co SPARSE_OK=YES -co BIGTIFF=YES {}'.format(cloudless_vrt, cloudless_tif))

    # Upload
    os.system('aws s3 cp {} {}'.format(cloudy_tif, args.output_path))
    os.system('aws s3 cp {} {}'.format(cloudless_tif, args.output_path))