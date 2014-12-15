import unittest
import glob
import sys
import json

import encode
import decode

class DynamicClassBase(unittest.TestCase):
    longMessage = True

def make_test_function(filename):
    def test(self):
        # self.maxDiff = None
        geojson = json.loads(open(filename, 'rb').read())
        pb = encode.encode(geojson)
        geojson2 = decode.decode(pb)
        self.assertEqual(geojson, geojson2, 'encode and decode ' + filename)
    return test

if __name__ == '__main__':

    for filename in glob.glob("./fixtures/*.json"):
        klassname = 'Test_' + filename.replace('/fixtures/', '').replace('.json', '')
        globals()[klassname] = type(klassname,
            (DynamicClassBase,), {'test_encode_decode': make_test_function(filename)})

    unittest.main()
