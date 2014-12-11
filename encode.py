#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import json
import struct
import geobuf_pb2 as geobuf_pb2


def encode_coord(x): return int(x * 1e6)

def add_point(line_string, x, y):
    # TODO altitude
    line_string.coords.append(encode_coord(x))
    line_string.coords.append(encode_coord(y))

def populate_linestring(line_string, seq):
    for i, point in enumerate(seq):
        if i == 0:
            add_point(line_string, point[0], point[1])
        else:
            add_point(line_string, point[0] - prev_x, point[1] - prev_y) # delta encoding
        prev_x = point[0]
        prev_y = point[1]

def populate_multi_line_string(multi_line_string, line_strings_json):
    for seq in line_strings_json:
        populate_linestring(multi_line_string.line_strings.add(), seq)


def encode_geometry(geometry, geometry_json):

    gt = geometry_json['type']
    Geometry = geobuf_pb2.Data.Geometry

    coords_json = geometry_json.get('coordinates')

    geometry.type = {
        'Point': Geometry.POINT,
        'MultiPoint': Geometry.MULTIPOINT,
        'LineString': Geometry.LINESTRING,
        'MultiLineString': Geometry.MULTILINESTRING,
        'Polygon': Geometry.POLYGON,
        'MultiPolygon': Geometry.MULTIPOLYGON
    }[gt]

    if gt == 'Point':
        add_point(geometry.line_string, coords_json[0], coords_json[1])

    elif gt in ('MultiPoint', 'LineString'):
        populate_linestring(geometry.line_string, coords_json)

    elif gt in ('MultiLineString','Polygon'):
        populate_multi_line_string(geometry.multi_line_string, coords_json)

    elif gt in ('MultiPolygon'):
        for polygons in coords_json:
            populate_multi_line_string(geometry.multi_polygon.polygons.add(), polygons)


def encode_properties(feature, properties_json):
    pass # TODO


def encode_feature(feature, feature_json):

    if feature_json['id']:
        # TODO uint ids
        feature.id = feature_json['id']

    geometry_json = feature_json.get('geometry')

    if geometry_json['type'] == 'GeometryCollection':
        for single_geometry_json in geometry_json.get('geometries'):
            encode_geometry(feature.geometry_collection.geometries.add(), single_geometry_json)
    else:
        encode_geometry(feature.geometry, geometry_json)

    encode_properties(feature, feature_json.get('properties'))


def encode(obj):

    data = geobuf_pb2.Data()
    data_type = obj['type']

    if data_type == 'FeatureCollection':
        for feature_json in obj.get('features'):
            encode_feature(data.feature_collection.features.add(), feature_json)

    elif data_type == 'Feature':
        encode_feature(data.feature, obj)

    elif data_type == 'GeometryCollection':
        for geometry_json in obj.get('geometries'):
            encode_geometry(data.geometry_collection.geometries.add(), geometry_json)
    else:
        encode_geometry(data.geometry, obj)

    return data.SerializeToString();


if __name__ == "__main__":
    filename = sys.argv[1]
    data = open(filename,'rb').read()
    json_object = json.loads(data)

    proto = encode(json_object)

    print "%d bytes" % (len(proto))
    open(filename + '.pbf', 'wb').write(proto)
