#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import json
import geobuf_pb2
import collections


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

        data_type = obj['type']

        if data_type == 'FeatureCollection':
            for feature_json in obj.get('features'):
                self.encode_feature(data.feature_collection.features.add(), feature_json)

        elif data_type == 'Feature':
            self.encode_feature(data.feature, obj)

        elif data_type == 'Topology':
            self.encode_topology(data, obj)

        else: self.encode_geometry(data.geometry, obj)

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

        for arc in data_json.get('arcs'):
            line = data.arcs.add()
            # encode first point as is and delta-encode the rest
            self.add_point(line, arc[0])
            self.populate_line(line, arc[1:])

        data.geometry.type = self.geometry_types['GeometryCollection']

        for name, geom in data_json.get('objects').viewitems():
            self.encode_topo_geometry(data.geometry.geometry_collection.geometries.add(), name, geom)


    def encode_geometry(self, geometry, geometry_json):

        gt = geometry_json['type']
        coords = geometry_json.get('coordinates')

        geometry.type = self.geometry_types[gt]

        if gt == 'GeometryCollection':
            for single_geom in geometry_json.get('geometries'):
                self.encode_geometry(geometry.geometry_collection.geometries.add(), single_geom)

        elif gt == 'Point':
            self.add_point(geometry.line_string, coords)

        elif gt == 'MultiPoint' or gt == 'LineString':
            self.populate_line(geometry.line_string, coords)

        elif gt == 'MultiLineString' or gt == 'Polygon':
            line_strings = geometry.multi_line_string.line_strings
            for seq in coords: self.populate_line(line_strings.add(), seq)

        elif gt == 'MultiPolygon':
            for polygons in coords:
                poly = geometry.multi_polygon.polygons.add()
                for seq in polygons: self.populate_line(poly.line_strings.add(), seq)


    def encode_topo_geometry(self, geometry, name, geometry_json):
        gt = geometry_json['type']
        arcs = geometry_json.get('arcs')
        coords = geometry_json.get('coordinates')

        geometry.type = self.geometry_types[gt]

        if name is not None: geometry.name = name

        self.encode_id(geometry, geometry_json.get('id'))
        self.encode_properties(geometry.properties, geometry_json.get('properties'))

        if gt == 'GeometryCollection':
            for geom in geometry_json.get('geometries'):
                self.encode_topo_geometry(geometry.geometry_collection.geometries.add(), None, geom)

        elif gt == 'Point':
            self.add_point(geometry.line_string, coords)

        elif gt == 'MultiPoint':
            self.populate_line(geometry.line_string, coords)

        elif gt == 'LineString':
            if len(arcs) == 1: geometry.arc_index = arcs[0]
            else: self.populate_arcs(geometry.line_string, arcs)

        elif gt == 'MultiLineString' or gt == 'Polygon':
            if len(arcs) == 1 and len(arcs[0]) == 1: geometry.arc_index = arcs[0][0]
            else:
                line_strings = geometry.multi_line_string.line_strings
                for seq in arcs: self.populate_arcs(line_strings.add(), seq)

        elif gt == 'MultiPolygon':
            for polygons in arcs:
                poly = geometry.multi_polygon.polygons.add()
                for seq in polygons: self.populate_arcs(poly.line_strings.add(), seq)


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


    def add_point(self, line, point):
        if self.transformed: line.values.extend(point) # transformed TopoJSON coords
        else:
            for x in point: line.values.append(int(round(x * self.e)))


    def populate_line(self, line, seq):
        p0 = [0 for i in seq[0]]
        r = range(len(p0))
        for p in seq:
            # delta-encode coordinates
            self.add_point(line, [p[i] - p0[i] for i in r])
            p0 = p


    def populate_arcs(self, arc_string, indexes):
        i0 = 0
        for i in indexes:
            # delta-encode arc indexes
            arc_string.values.append(i - i0)
            i0 = i


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
