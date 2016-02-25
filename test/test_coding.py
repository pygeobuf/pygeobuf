import glob
import json
import os

import pytest

from geobuf import Decoder, Encoder


@pytest.mark.parametrize(
    "filename",
    glob.glob(os.path.join(os.path.dirname(__file__), "fixtures/*.json")))
def test_coding(filename):
    geojson = json.loads(open(filename).read())
    pb = Encoder().encode(geojson)
    geojson2 = Decoder().decode(pb)
    assert geojson == geojson2
