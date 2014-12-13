#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import json
import geobuf_pb2
import collections


def decode_point(line, dim, precision):
    return [float(x) / precision for x in line.coords]


def decode_linestring(line, dim, precision):
    obj = []
    point = []
    int_coords = []
    for i, x in enumerate(line.coords):
        coord = float(x)
        if i >= dim: coord += int_coords[i - dim]
        int_coords.append(coord)
        point.append(coord / precision)
        if (i + 1) % dim == 0:
            obj.append(point)
            point = []
    return obj


geometry_types = ('Point', 'MultiPoint', 'LineString', 'MultiLineString', 'Polygon', 'MultiPolygon')

def decode_geometry(geometry, dim, digits):
    obj = {}
    gt = obj['type'] = geometry_types[geometry.type]
    precision = pow(10, digits)

    if gt == 'Point':
        obj['coordinates'] = decode_point(geometry.line_string, precision)

    elif gt == 'MultiPoint' or gt == 'LineString':
        obj['coordinates'] = decode_linestring(geometry.line_string, dim, precision)

    elif (gt == 'MultiLineString') or (gt == 'Polygon'):
        line_strings = geometry.multi_line_string.line_strings
        obj['coordinates'] = [decode_linestring(line, dim, precision) for line in line_strings]

    elif gt == 'MultiPolygon':
        obj['coordinates'] = []
        for polygon in geometry.multi_polygon.polygons:
            obj['coordinates'].append([decode_linestring(line, dim, precision) for line in polygon.line_strings])

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


def decode_geometry_collection(geometry_collection, dimensions, precision):
    obj = {'type': 'GeometryCollection'}
    geometries = obj['geometries'] = []
    for geometry in geometry_collection.geometries:
        geometries.append(decode_geometry(geometry, dimensions, precision))
    return obj


def decode_feature(data, feature):
    obj = collections.OrderedDict()

    id_type = feature.WhichOneof('id_type')
    if id_type == 'id': obj['id'] = feature.id
    elif id_type == 'uint_id': obj['id'] = feature.uint_id

    obj['type'] = 'Feature'

    geometry_type = feature.WhichOneof('geometry_type')

    if geometry_type == 'geometry_collection':
        obj['geometry'] = decode_geometry_collection(feature.geometry_collection, data.dimensions, data.precision)

    else: obj['geometry'] = decode_geometry(feature.geometry, data.dimensions, data.precision)

    obj['properties'] = decode_properties(data, feature.properties)

    return obj


def decode(data):

    data_type = data.WhichOneof('data_type')

    if data_type == 'feature_collection':
        obj = {}
        obj['type'] = 'FeatureCollection'
        features = obj['features'] = []
        for feature in data.feature_collection.features:
            features.append(decode_feature(data, feature))

    elif data_type == 'feature':
        obj = decode_feature(data, data.feature)

    elif data_type == 'geometry_collection':
        obj = decode_geometry_collection(data.geometry_collection, data.dimensions, data.precision)

    elif data_type == 'geometry':
        obj = decode_geometry(geometry, data.dimensions, data.precision)

    return obj


if __name__ == "__main__":
    filename = sys.argv[1]
    data_str = open(filename,'rb').read()

    data = geobuf_pb2.Data()
    data.ParseFromString(data_str)

    obj = decode(data)
    open(filename.replace('.pbf', '.decoded.json'), 'wb').write(json.dumps(obj))

