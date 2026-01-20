import base64
import glob
import json
import math
import os

import pytest

import geobuf
from geobuf import Decoder, Encoder

exclude = {'precision.json'}
files = glob.glob(os.path.join(os.path.dirname(__file__), "fixtures/*.json"))
coding_fixtures = [filename for filename in files if os.path.basename(filename) not in exclude]


@pytest.mark.parametrize("filename", coding_fixtures)
def test_coding(filename):
    geojson = json.loads(open(filename).read())
    pb = Encoder().encode(geojson)
    geojson2 = Decoder().decode(pb)
    assert geojson == geojson2


def test_high_precision():
    filename = os.path.join(os.path.dirname(__file__), "fixtures/precision.json")
    with open(filename) as f:
        geojson = json.loads(f.read())
    pbf = Encoder().encode(geojson)
    geojson2 = Decoder().decode(pbf)
    ring = geojson2['features'][0]['geometry']['coordinates'][0]
    assert ring[0] == ring[4]


def test_line_accumulating_error():
    """
    Generate a line of 40 points. Each point's x coordinate, x[n] is at x[n - 1] + 1 + d, where
    d is a floating point number that just rounds to 0 at 6 decimal places, i.e. 0.00000049.
    Therefore a delta compression method that only computes x[n] - x[n - 1] and rounds to 6 d.p.
    will get a constant delta of 1.000000. The result will be an accumulated error along the
    line of 0.00000049 * 40 = 0.0000196 over the full length.
    """
    feature = {
        'type': 'MultiPolygon',
        'coordinates': [[[]]],
    }
    points = 40
    # X coordinates[0, 1.00000049, 2.00000098, 3.00000147, 4.00000196, ...,
    #               37.00001813, 38.00001862, 39.00001911, 40.00001960, 0]
    feature['coordinates'][0][0] = [[i * 1.00000049, 0] for i in range(0, points + 1)]
    feature['coordinates'][0][0].append([0, 0])
    pbf = Encoder().encode(feature)
    round_tripped = Decoder().decode(pbf)

    def round_x(coord):
        x, _ = coord
        return round(x * 1000000) / 1000000.0

    xs_orig = [round_x(coord) for coord in feature['coordinates'][0][0]]
    xs_round_tripped = [round_x(coord) for coord in round_tripped['coordinates'][0][0]]
    assert xs_round_tripped == xs_orig


def test_circle_accumulating_error():
    feature = {
        'type': 'MultiPolygon',
        'coordinates': [[[]]],
    }
    points = 16
    feature['coordinates'][0][0] = [
        [math.cos(math.pi * 2.0 * i / points), math.sin(math.pi * 2.0 * i / points)]
        for i in range(0, points + 1)
    ]
    pbf = Encoder().encode(feature)
    round_tripped = Decoder().decode(pbf)

    def round_coord(coord):
        x, y = coord
        return [round(x * 1000000), round(y * 1000000)]

    ring_orig = [round_coord(coord) for coord in feature['coordinates'][0][0]]
    ring_round_tripped = [round_coord(coord) for coord in round_tripped['coordinates'][0][0]]
    assert ring_round_tripped == ring_orig


def test_dimensions():
    """
    Generate a line of 8 points. Each point is a coordinate with an altitude.
    Ensure dim parameter allows to encode and decode a geometry.

    Using dim=2 will reduce the coordinates by removing the altitude.
    Using dim=3 must conserve the altitude
    """
    feature = {
        'type': 'MultiPolygon',
        'coordinates': [[[]]],
    }
    points = 8
    # Z coordinates[0, 1, 2, 3, ... , 8, 0]
    feature['coordinates'][0][0] = [[0, 0, i] for i in range(0, points + 1)]
    feature['coordinates'][0][0].append([0, 0, 0])

    pbf = Encoder().encode(feature, dim=2)
    dim2 = Decoder().decode(pbf)

    dim2_orig = [[x, y] for x, y, z in feature['coordinates'][0][0]]
    dim2 = dim2['coordinates'][0][0]
    assert dim2 == dim2_orig

    pbf = Encoder().encode(feature, dim=3)
    dim3 = Decoder().decode(pbf)

    dim_orig = feature['coordinates'][0][0]
    dim3 = dim3['coordinates'][0][0]
    assert dim3 == dim_orig


def test_decode_js_encoded_dim_zero():
    """
    Test decoding data where dimensions field is unset (JS encoder behavior).

    The JS geobuf encoder omits the dimensions field when dim=2 (optimization).
    Proto3 returns 0 for unset uint32 fields. The Python decoder must handle
    this by defaulting to 2, matching the JS decoder behavior.

    See: https://github.com/pygeobuf/pygeobuf/issues/59
    """
    # This data was encoded by the JS library (via PostGIS ST_AsGeobuf)
    # with dimensions field omitted (unset, proto3 returns 0)
    data = base64.b64decode('GAAiEAoOCgwIBBoIAAAAAgIAAAE=')
    result = geobuf.decode(data)

    assert result['type'] == 'FeatureCollection'
    assert len(result['features']) == 1
    assert result['features'][0]['geometry']['type'] == 'Polygon'
