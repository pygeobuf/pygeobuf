#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import json
import geobuf_pb2
import collections


def decode_point(line, dim, precision):
    return [float(x) / precision for x in line]


def decode_line(line, dim, precision):
    obj = []
    coords = line.coords
    r = range(dim)
    p0 = [0 for i in r]

    for i in xrange(0, len(coords), dim):
        p = [p0[j] + coords[i + j] for j in r]
        obj.append(decode_point(p, dim, precision))
        p0 = p

    return obj


geometry_types = ('Point', 'MultiPoint', 'LineString', 'MultiLineString', 'Polygon', 'MultiPolygon')

def decode_geometry(geometry, dim, precision):
    obj = {}
    gt = obj['type'] = geometry_types[geometry.type]

    if gt == 'Point':
        obj['coordinates'] = decode_point(geometry.line_string.coords, precision)

    elif gt == 'MultiPoint' or gt == 'LineString':
        obj['coordinates'] = decode_line(geometry.line_string, dim, precision)

    elif (gt == 'MultiLineString') or (gt == 'Polygon'):
        line_strings = geometry.multi_line_string.line_strings
        obj['coordinates'] = [decode_line(line, dim, precision) for line in line_strings]

    elif gt == 'MultiPolygon':
        obj['coordinates'] = []
        for polygon in geometry.multi_polygon.polygons:
            obj['coordinates'].append([decode_line(line, dim, precision) for line in polygon.line_strings])

    return obj


def decode_properties(data, properties):
    obj = {}
    for i, prop in enumerate(properties):
        if i % 2 == 0:
            key = data.keys[properties[i]]
            val = data.values[properties[i + 1]]

            value_type = val.WhichOneof('value_type')
            if value_type == 'string_value': obj[key] = val.string_value
            elif value_type == 'double_value': obj[key] = val.double_value
            elif value_type == 'int_value': obj[key] = val.int_value
            elif value_type == 'bool_value': obj[key] = val.bool_value

    return obj


def decode_geometry_collection(geometry_collection, dim, precision):
    obj = {'type': 'GeometryCollection'}
    geometries = obj['geometries'] = []
    for geometry in geometry_collection.geometries:
        geometries.append(decode_geometry(geometry, dim, precision))
    return obj


def decode_feature(data, feature, dim, precision):
    obj = collections.OrderedDict()
    obj['type'] = 'Feature'

    id_type = feature.WhichOneof('id_type')
    if id_type == 'id': obj['id'] = feature.id
    elif id_type == 'uint_id': obj['id'] = feature.uint_id

    geometry_type = feature.WhichOneof('geometry_type')

    if geometry_type == 'geometry_collection':
        obj['geometry'] = decode_geometry_collection(feature.geometry_collection, dim, precision)

    else: obj['geometry'] = decode_geometry(feature.geometry, dim, precision)

    obj['properties'] = decode_properties(data, feature.properties)

    return obj


def decode(data):

    data_type = data.WhichOneof('data_type')

    precision = pow(10, data.precision)
    dim = data.dimensions

    if data_type == 'feature_collection':
        obj = {'type': 'FeatureCollection'}
        features = obj['features'] = []
        for feature in data.feature_collection.features:
            features.append(decode_feature(data, feature, dim, precision))

    elif data_type == 'feature':
        obj = decode_feature(data, data.feature, dim, precision)

    elif data_type == 'geometry_collection':
        obj = decode_geometry_collection(data.geometry_collection, dim, precision)

    elif data_type == 'geometry':
        obj = decode_geometry(geometry, dim, precision)

    return obj


if __name__ == "__main__":
    filename = sys.argv[1]
    data_str = open(filename,'rb').read()

    data = geobuf_pb2.Data()
    data.ParseFromString(data_str)

    obj = decode(data)
    open(filename.replace('.pbf', '.decoded.json'), 'wb').write(json.dumps(obj))

