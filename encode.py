#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import json
import geobuf_pb2
import collections
# import google.protobuf.text_format as tf


class Encoder:

    geometry_types = {
        'Point': 0,
        'MultiPoint': 1,
        'LineString': 2,
        'MultiLineString': 3,
        'Polygon': 4,
        'MultiPolygon': 5,
        'GeometryCollection': 6
    }

    def encode(self, data_json, precision=6, dim=2):
        obj = self.json = data_json
        data = self.data = geobuf_pb2.Data()

        self.precision = precision
        self.dim = dim
        self.e = pow(10, precision) # multiplier for converting coordinates into integers

        self.keys = collections.OrderedDict()
        self.values = collections.OrderedDict()
        self.transformed = False
        self.is_topo = False

        data_type = obj['type']

        if data_type == 'FeatureCollection':
            for feature_json in obj.get('features'):
                self.encode_feature(data.feature_collection.features.add(), feature_json)

        elif data_type == 'Feature':
            self.encode_feature(data.feature, obj)

        elif data_type == 'Topology':
            self.is_topo = True
            self.encode_topology(data, obj)

        else: self.encode_geometry(data.geometry, obj)

        # print tf.MessageToString(data)

        return data.SerializeToString()


    def encode_feature(self, feature, feature_json):
        self.encode_id(feature, feature_json.get('id'))
        self.encode_properties(feature.properties, feature_json.get('properties'))
        self.encode_geometry(feature.geometry, feature_json.get('geometry'))


    def encode_topology(self, data, data_json):

        transform_json = data_json.get('transform')

        if transform_json:
            scale_json = transform_json.get('scale')
            translate_json = transform_json.get('translate')

            transform = data.transform
            transform.scale_x = scale_json[0]
            transform.scale_y = scale_json[1]
            transform.translate_x = translate_json[0]
            transform.translate_y = translate_json[1]

            self.transformed = True

        arcs = data_json.get('arcs')
        for arc in arcs: data.arc_lengths.append(len(arc))
        for arc in arcs:
            for p in arc: self.add_point(data.arc_coords, p)

        data.geometry.type = self.geometry_types['GeometryCollection']

        for name, geom in data_json.get('objects').viewitems():
            self.encode_geometry(data.geometry.geometry_collection.geometries.add(), geom, name)


    def encode_geometry(self, geometry, geometry_json, name=None):

        gt = geometry_json['type']
        coords = geometry_json.get('coordinates')
        coords_or_arcs = coords

        geometry.type = self.geometry_types[gt]

        if self.is_topo:
            if name is not None: geometry.name = name
            coords_or_arcs = geometry_json.get('arcs')
            self.encode_id(geometry, geometry_json.get('id'))
            self.encode_properties(geometry.properties, geometry_json.get('properties'))

        if gt == 'GeometryCollection':
            geometries = geometry.geometry_collection.geometries
            for geom in geometry_json.get('geometries'): self.encode_geometry(geometries.add(), geom)

        elif gt == 'Point':
            self.add_point(geometry.coords, coords)

        elif gt == 'MultiPoint':
            self.add_line(geometry.coords, coords)

        elif gt == 'LineString':
            self.add_line(geometry.coords, coords_or_arcs)

        elif gt == 'MultiLineString' or gt == 'Polygon':
            self.add_multi_line(geometry, coords_or_arcs)

        elif gt == 'MultiPolygon':
            self.add_multi_polygon(geometry, coords_or_arcs)


    def encode_properties(self, properties, props_json):

        if props_json is None: return

        keys = self.keys
        values = self.values
        data = self.data

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


    def encode_id(self, obj, id):
        if id is not None:
            if isinstance(id, int): obj.int_id = id
            else: obj.id = str(id)


    def add_coord(self, coords, coord):
        coords.append(coord if self.transformed else int(round(coord * self.e)))

    def add_point(self, coords, point):
        for x in point: self.add_coord(coords, x)

    def add_line(self, coords, points):
        for i, p in enumerate(points):
            if self.is_topo: coords.append(p - (points[i - 1] if i else 0)) # delta-encode arc indexes
            else: # delta-encode coordinates
                for j in range(self.dim): self.add_coord(coords, p[j] - (points[i - 1][j] if i else 0))


    def add_multi_line(self, geometry, lines):
        if len(lines) != 1:
            for points in lines: geometry.lengths.append(len(points))

        for points in lines: self.add_line(geometry.coords, points)


    def add_multi_polygon(self, geometry, polygons):
        if len(polygons) != 1 or len(polygons[0]) != 1 or len(polygons[0][0]) != 1:
            geometry.lengths.append(len(polygons))
            for rings in polygons:
                geometry.lengths.append(len(rings))
                for points in rings: geometry.lengths.append(len(points))

        for rings in polygons:
            for points in rings: self.add_line(geometry.coords, points)


if __name__ == '__main__':
    filename = sys.argv[1]
    data = open(filename,'rb').read()
    json_object = json.loads(data)

    if len(sys.argv) > 3:
        proto = Encoder().encode(json_object, int(sys.argv[2]), int(sys.argv[3]))
    elif len(sys.argv) > 2:
        proto = Encoder().encode(json_object, int(sys.argv[2]))
    else:
        proto = Encoder().encode(json_object)

    print 'Encoded in %d bytes out of %d (%d%%)' % (len(proto), len(data), 100 * len(proto) / len(data))

    open(filename.replace('.json', '.pbf'), 'wb').write(proto)
