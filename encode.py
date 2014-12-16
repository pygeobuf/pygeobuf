#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import json
import geobuf_pb2
import collections


def add_point(line, point, e):
    for x in point: line.coords.append(int(round(x * e)))


def populate_line(line, seq, e):
    p0 = [0 for i in seq[0]]
    r = range(len(p0))
    for p in seq:
        add_point(line, [p[i] - p0[i] for i in r], e) # delta encoding
        p0 = p


def encode_geometry(geometry, geometry_json, e):

    gt = geometry_json['type']
    coords = geometry_json.get('coordinates')

    Data = geobuf_pb2.Data
    geometry.type = {
        'Point': Data.POINT,
        'MultiPoint': Data.MULTIPOINT,
        'LineString': Data.LINESTRING,
        'MultiLineString': Data.MULTILINESTRING,
        'Polygon': Data.POLYGON,
        'MultiPolygon': Data.MULTIPOLYGON,
        'GeometryCollection': Data.GEOMETRYCOLLECTION
    }[gt]

    if gt == 'GeometryCollection':
        for single_geometry_json in geometry_json.get('geometries'):
            encode_geometry(geometry.geometry_collection.geometries.add(), single_geometry_json, e)

    elif gt == 'Point':
        add_point(geometry.line_string, coords, e)

    elif gt == 'MultiPoint' or gt == 'LineString':
        populate_line(geometry.line_string, coords, e)

    elif gt == 'MultiLineString' or gt == 'Polygon':
        line_strings = geometry.multi_line_string.line_strings
        for seq in coords: populate_line(line_strings.add(), seq, e)

    elif gt == 'MultiPolygon':
        for polygons in coords:
            poly = geometry.multi_polygon.polygons.add()
            for seq in polygons: populate_line(poly.line_strings.add(), seq, e)


def encode_properties(data, properties, props_json, keys, values):

    for key, val in props_json.viewitems():
        if not (key in keys):
            keys[key] = True
            data.keys.append(key)
            keyIndex = len(data.keys) - 1
        else:
            keyIndex = keys.keys().index(key)

        value_is_json = isinstance(val, dict) or isinstance(val, list)
        if value_is_json: val = json.dumps(val, separators=(',',':'))

        if not (val in values):
            values[val] = True
            value = data.values.add()
            valueIndex = len(data.values) - 1

            if value_is_json: value.json_value = val
            elif isinstance(val, unicode): value.string_value = val
            elif isinstance(val, float):
                if val.is_integer(): value.int_value = int(val)
                else: value.double_value = val
            elif isinstance(val, int) or isinstance(val, long): value.int_value = val
            elif isinstance(val, bool): value.bool_value = val
        else:
            valueIndex = values.keys().index(val)

        properties.append(keyIndex)
        properties.append(valueIndex)


def encode_feature(data, feature, feature_json, e, keys, values):

    if 'id' in feature_json:
        id = feature_json['id']
        if isinstance(id, int) and id >= 0: feature.uint_id = idts
        else: feature.id = id

    encode_geometry(feature.geometry, feature_json.get('geometry'), e)
    encode_properties(data, feature.properties, feature_json.get('properties'), keys, values)


def encode(obj, precision=6, dim=2):

    data = geobuf_pb2.Data()

    data.precision = precision
    data.dimensions = dim

    e = pow(10, precision) # multiplier for converting coordinates into integers
    keys = collections.OrderedDict()
    values = collections.OrderedDict()

    data_type = obj['type']

    if data_type == 'FeatureCollection':
        for feature_json in obj.get('features'):
            encode_feature(data, data.feature_collection.features.add(), feature_json, e, keys, values)

    elif data_type == 'Feature':
        encode_feature(data, data.feature, obj, e, keys, values)

    else: encode_geometry(data.geometry, obj, e)

    return data.SerializeToString();


if __name__ == '__main__':
    filename = sys.argv[1]
    data = open(filename,'rb').read()
    json_object = json.loads(data)

    if len(sys.argv) > 3:
        proto = encode(json_object, int(sys.argv[2]), int(sys.argv[3]))
    elif len(sys.argv) > 2:
        proto = encode(json_object, int(sys.argv[2]))
    else:
        proto = encode(json_object)

    print 'Encoded in %d bytes out of %d (%d%%)' % (len(proto), len(data), 100 * len(proto) / len(data))

    open(filename.replace('.json', '.pbf'), 'wb').write(proto)
