#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import json
import geobuf_pb2
import collections


def decode_point(line, dim, e):
    if e == 1: return line
    return [float(x) / e for x in line]


def decode_line(line, dim, e):
    obj = []
    coords = line.values
    r = range(dim)
    p0 = [0 for i in r]

    for i in xrange(0, len(coords), dim):
        p = [p0[j] + coords[i + j] for j in r]
        obj.append(decode_point(p, dim, e))
        p0 = p

    return obj


def decode_arcs(line):
    obj = []
    i0 = 0
    for i in line.values:
        obj.append(i0 + i)
        i0 += i
    return obj


geometry_types = ('Point', 'MultiPoint', 'LineString', 'MultiLineString',
                  'Polygon', 'MultiPolygon', 'GeometryCollection')

def decode_geometry(geometry, dim, e):
    obj = {}
    gt = obj['type'] = geometry_types[geometry.type]

    if gt == 'GeometryCollection':
        obj['geometries'] = [decode_geometry(geom, dim, e) for geom in geometry.geometry_collection.geometries]

    elif gt == 'Point':
        obj['coordinates'] = decode_point(geometry.line_string.values, dim, e)

    elif gt == 'MultiPoint' or gt == 'LineString':
        obj['coordinates'] = decode_line(geometry.line_string, dim, e)

    elif (gt == 'MultiLineString') or (gt == 'Polygon'):
        line_strings = geometry.multi_line_string.line_strings
        obj['coordinates'] = [decode_line(line, dim, e) for line in line_strings]

    elif gt == 'MultiPolygon':
        obj['coordinates'] = []
        for polygon in geometry.multi_polygon.polygons:
            obj['coordinates'].append([decode_line(line, dim, e) for line in polygon.line_strings])

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
            elif value_type == 'json_value': obj[key] = json.loads(val.json_value)
    return obj


def decode_id(obj, obj_json):
    id_type = obj.WhichOneof('id_type')
    if id_type == 'id': obj_json['id'] = obj.id
    elif id_type == 'int_id': obj_json['id'] = obj.int_id


def decode_feature(data, feature, dim, e):
    obj = collections.OrderedDict()
    obj['type'] = 'Feature'

    decode_id(feature, obj)
    obj['geometry'] = decode_geometry(feature.geometry, dim, e)
    if feature.properties: obj['properties'] = decode_properties(data, feature.properties)

    return obj


def decode_topo_geometry(geometry, data, dim, e):
    obj = collections.OrderedDict()
    gt = obj['type'] = geometry_types[geometry.type]

    decode_id(geometry, obj)

    if gt == 'GeometryCollection':
        obj['geometries'] = [decode_topo_geometry(g, data, dim, e) for g in geometry.geometry_collection.geometries]

    elif gt == 'Point':
        obj['coordinates'] = decode_point(geometry.line_string.values, dim, e)

    elif gt == 'MultiPoint':
        obj['coordinates'] = decode_line(geometry.line_string, dim, e)

    elif gt == 'LineString':
        obj['arcs'] = decode_arcs(geometry.line_string)

    elif (gt == 'MultiLineString') or (gt == 'Polygon'):
        obj['arcs'] = [decode_arcs(line) for line in geometry.multi_line_string.line_strings]

    elif gt == 'MultiPolygon':
        obj['arcs'] = []
        for polygon in geometry.multi_polygon.polygons:
            obj['arcs'].append([decode_arcs(line) for line in polygon.line_strings])

    if geometry.properties: obj['properties'] = decode_properties(data, geometry.properties)

    return obj


def decode_topology(data, dim, e):
    obj = collections.OrderedDict()

    obj['type'] = 'Topology'

    tr = data.transform
    if tr:
        obj['transform'] = {
            'scale': [tr.scale_x, tr.scale_y],
            'translate': [tr.translate_x, tr.translate_y]
        }
        e = 1

    objects = obj['objects'] = {}
    for geom in data.geometry.geometry_collection.geometries:
        objects[geom.name] = decode_topo_geometry(geom, data, dim, e)

    obj['arcs'] = [decode_line(arc, dim, e) for arc in data.arcs]

    return obj


def decode(data_str):

    data = geobuf_pb2.Data()
    data.ParseFromString(data_str)

    e = pow(10, data.precision)
    dim = data.dimensions

    if data.is_topojson: return decode_topology(data, dim, e)

    data_type = data.WhichOneof('data_type')

    if data_type == 'feature_collection':
        obj = {'type': 'FeatureCollection', 'features': []}
        for feature in data.feature_collection.features:
            obj['features'].append(decode_feature(data, feature, dim, e))
        return obj

    elif data_type == 'feature': return decode_feature(data, data.feature, dim, e)
    elif data_type == 'geometry': return decode_geometry(data.geometry, dim, e)


if __name__ == "__main__":
    filename = sys.argv[1]
    data_str = open(filename,'rb').read()
    obj = decode(data_str)
    open(filename.replace('.pbf', '.pbf.json'), 'wb').write(json.dumps(obj))

