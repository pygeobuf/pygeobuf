#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import json
import geobuf_pb2
import collections


precision = 6 # TODO detect automatically and accept as a command line param


def add_point(line, point):
    for x in point: line.coords.append(int(round(x * pow(10, precision))))


def populate_line(line, seq):
    p0 = [0 for i in seq[0]]
    r = range(len(p0))
    for p in seq:
        add_point(line, [p[i] - p0[i] for i in r]) # delta encoding
        p0 = p


def encode_geometry(geometry, geometry_json):

    gt = geometry_json['type']

    Geometry = geobuf_pb2.Data.Geometry
    geometry.type = {
        'Point': Geometry.POINT,
        'MultiPoint': Geometry.MULTIPOINT,
        'LineString': Geometry.LINESTRING,
        'MultiLineString': Geometry.MULTILINESTRING,
        'Polygon': Geometry.POLYGON,
        'MultiPolygon': Geometry.MULTIPOLYGON
    }[gt]

    coords_json = geometry_json.get('coordinates')

    if gt == 'Point':
        add_point(geometry.line_string, coords_json)

    elif gt == 'MultiPoint' or gt == 'LineString':
        populate_line(geometry.line_string, coords_json)

    elif gt == 'MultiLineString' or gt == 'Polygon':
        line_strings = geometry.multi_line_string.line_strings
        for seq in coords_json: populate_line(line_strings.add(), seq)

    elif gt == 'MultiPolygon':
        for polygons in coords_json:
            poly = geometry.multi_polygon.polygons.add()
            for seq in polygons: populate_line(poly.line_strings.add(), seq)


def encode_properties(data, properties, props_json):

    keys = collections.OrderedDict()

    for key, val in props_json.viewitems():
        if not (key in keys):
            keys[key] = True
            data.keys.append(key)

        properties.append(keys.keys().index(key))
        properties.append(len(data.values))

        value = data.values.add()
        if isinstance(val, unicode): value.string_value = val
        elif isinstance(val, float): value.double_value = val
        elif isinstance(val, int) or isinstance(val, long): value.int_value = val
        elif isinstance(val, bool): value.bool_value = val


def encode_feature(data, feature, feature_json):

    if 'id' in feature_json:
        id = feature_json['id']
        if isinstance(id, int) and id >= 0: feature.uint_id = idts
        else: feature.id = id

    geometry_json = feature_json.get('geometry')

    if geometry_json['type'] == 'GeometryCollection':
        for single_geometry_json in geometry_json.get('geometries'):
            encode_geometry(feature.geometry_collection.geometries.add(), single_geometry_json)
    else:
        encode_geometry(feature.geometry, geometry_json)

    encode_properties(data, feature.properties, feature_json.get('properties'))


def encode(obj):

    data = geobuf_pb2.Data()
    data_type = obj['type']

    if data_type == 'FeatureCollection':
        for feature_json in obj.get('features'):
            encode_feature(data, data.feature_collection.features.add(), feature_json)

    elif data_type == 'Feature':
        encode_feature(data, data.feature, obj)

    elif data_type == 'GeometryCollection':
        for geometry_json in obj.get('geometries'):
            encode_geometry(data.geometry_collection.geometries.add(), geometry_json)

    else: encode_geometry(data.geometry, obj)

    return data.SerializeToString();


if __name__ == '__main__':
    filename = sys.argv[1]
    data = open(filename,'rb').read()
    json_object = json.loads(data)
    proto = encode(json_object)

    print 'Encoded in %d bytes out of %d (%d%%)' % (len(proto), len(data), 100 * len(proto) / len(data))

    open(filename.replace('.json', '.pbf'), 'wb').write(proto)
