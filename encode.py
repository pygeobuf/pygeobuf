#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import json
import geobuf_pb2
import collections


def add_point(line, point, e):
    for x in point: line.values.append(int(round(x * e)))


def populate_line(line, seq, e):
    p0 = [0 for i in seq[0]]
    r = range(len(p0))
    for p in seq:
        # delta-encode coordinates
        add_point(line, [p[i] - p0[i] for i in r], e)
        p0 = p


def populate_arcs(arc_string, indexes):
    i0 = 0
    for i in indexes:
        # delta-encode arc indexes
        arc_string.values.append(i - i0)
        i0 = i


def encode_properties(data, properties, props_json, keys, values):

    if props_json is None: return

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


def encode_id(obj, id):
    if id is not None:
        if isinstance(id, int): obj.int_id = id
        else: obj.id = str(id)


geometry_types = {
    'Point': 0,
    'MultiPoint': 1,
    'LineString': 2,
    'MultiLineString': 3,
    'Polygon': 4,
    'MultiPolygon': 5,
    'GeometryCollection': 6
}

def encode_geometry(geometry, geometry_json, e):

    gt = geometry_json['type']
    coords = geometry_json.get('coordinates')

    geometry.type = geometry_types[gt]

    if gt == 'GeometryCollection':
        for single_geom in geometry_json.get('geometries'):
            encode_geometry(geometry.geometry_collection.geometries.add(), single_geom, e)

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


def encode_topo_geometry(geometry, data, name, geometry_json, e, keys, values):
    gt = geometry_json['type']
    arcs = geometry_json.get('arcs')
    coords = geometry_json.get('coordinates')

    geometry.type = geometry_types[gt]

    if name is not None: geometry.name = name

    encode_id(geometry, geometry_json.get('id'))
    encode_properties(data, geometry.properties, geometry_json.get('properties'), keys, values)

    if gt == 'GeometryCollection':
        for single_geom in geometry_json.get('geometries'):
            encode_topo_geometry(geometry.geometry_collection.geometries.add(),
                    data, None, single_geom, e, keys, values)

    elif gt == 'Point':
        add_point(geometry.line_string, coords, e)

    elif gt == 'MultiPoint':
        populate_line(geometry.line_string, coords, e)

    elif gt == 'LineString':
        if len(arcs) == 1: geometry.arc_index = arcs[0]
        else: populate_arcs(geometry.line_string, arcs)

    elif gt == 'MultiLineString' or gt == 'Polygon':
        if len(arcs) == 1 and len(arcs[0]) == 1: geometry.arc_index = arcs[0][0]
        else:
            line_strings = geometry.multi_line_string.line_strings
            for seq in arcs: populate_arcs(line_strings.add(), seq)

    elif gt == 'MultiPolygon':
        for polygons in arcs:
            poly = geometry.multi_polygon.polygons.add()
            for seq in polygons: populate_arcs(poly.line_strings.add(), seq)


def encode_feature(data, feature, feature_json, e, keys, values):
    encode_id(feature, feature_json.get('id'))
    encode_properties(data, feature.properties, feature_json.get('properties'), keys, values)
    encode_geometry(feature.geometry, feature_json.get('geometry'), e)


def encode_topology(data, data_json, e, keys, values):

    transform_json = data_json.get('transform')

    if transform_json:
        scale_json = transform_json.get('scale')
        translate_json = transform_json.get('translate')

        transform = data.transform
        transform.scale_x = scale_json[0]
        transform.scale_y = scale_json[1]
        transform.translate_x = translate_json[0]
        transform.translate_y = translate_json[1]

        e = 1 # if we have a transform, arc coords are already integers

    for arc in data_json.get('arcs'): populate_line(data.arcs.add(), arc, e)

    data.geometry.type = geometry_types['GeometryCollection']

    for name, geom in data_json.get('objects').viewitems():
        encode_topo_geometry(data.geometry.geometry_collection.geometries.add(), data, name, geom, e, keys, values)


def encode(data_json, precision=6, dim=2):

    data = geobuf_pb2.Data()

    data.precision = precision
    data.dimensions = dim

    e = pow(10, precision) # multiplier for converting coordinates into integers
    keys = collections.OrderedDict()
    values = collections.OrderedDict()

    data_type = data_json['type']

    if data_type == 'FeatureCollection':
        for feature_json in data_json.get('features'):
            encode_feature(data, data.feature_collection.features.add(), feature_json, e, keys, values)

    elif data_type == 'Feature':
        encode_feature(data, data.feature, data_json, e, keys, values)

    elif data_type == 'Topology':
        encode_topology(data, data_json, e, keys, values)

    else: encode_geometry(data.geometry, data_json, e)

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
