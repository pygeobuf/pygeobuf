#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import json
import geobuf_pb2
import collections


class Decoder:

    geometry_types = ('Point', 'MultiPoint', 'LineString', 'MultiLineString',
                      'Polygon', 'MultiPolygon', 'GeometryCollection')


    def decode(self, data_str):

        data = self.data = geobuf_pb2.Data()
        data.ParseFromString(data_str)

        self.e = pow(10, data.precision)
        self.dim = data.dimensions
        self.transformed = False

        if len(data.arcs) > 0: return self.decode_topology(data)

        data_type = data.WhichOneof('data_type')

        if data_type == 'feature_collection':
            obj = {'type': 'FeatureCollection', 'features': []}
            for feature in data.feature_collection.features:
                obj['features'].append(self.decode_feature(feature))
            return obj

        elif data_type == 'feature': return self.decode_feature(data.feature)
        elif data_type == 'geometry': return self.decode_geometry(data.geometry)


    def decode_feature(self, feature):
        obj = collections.OrderedDict()
        obj['type'] = 'Feature'

        self.decode_id(feature, obj)
        obj['geometry'] = self.decode_geometry(feature.geometry)
        if feature.properties: obj['properties'] = self.decode_properties(feature.properties)

        return obj


    def decode_topology(self, data):
        obj = collections.OrderedDict()
        obj['type'] = 'Topology'

        if data.HasField('transform'):
            tr = data.transform
            obj['transform'] = {
                'scale': [tr.scale_x, tr.scale_y],
                'translate': [tr.translate_x, tr.translate_y]
            }
            self.transformed = True

        objects = obj['objects'] = {}
        for geom in data.geometry.geometry_collection.geometries:
            objects[geom.name] = self.decode_topo_geometry(geom)

        obj['arcs'] = [[self.decode_point(arc.values[0:self.dim])] + self.decode_line(arc, 1) for arc in data.arcs]

        return obj


    def decode_properties(self, properties):
        obj = {}
        for i, prop in enumerate(properties):
            if i % 2 == 0:
                key = self.data.keys[properties[i]]
                val = self.data.values[properties[i + 1]]

                value_type = val.WhichOneof('value_type')
                if value_type == 'string_value': obj[key] = val.string_value
                elif value_type == 'double_value': obj[key] = val.double_value
                elif value_type == 'int_value': obj[key] = val.int_value
                elif value_type == 'bool_value': obj[key] = val.bool_value
                elif value_type == 'json_value': obj[key] = json.loads(val.json_value)
        return obj


    def decode_id(self, obj, obj_json):
        id_type = obj.WhichOneof('id_type')
        if id_type == 'id': obj_json['id'] = obj.id
        elif id_type == 'int_id': obj_json['id'] = obj.int_id


    def decode_geometry(self, geometry):
        obj = {}
        gt = obj['type'] = self.geometry_types[geometry.type]

        if gt == 'GeometryCollection':
            obj['geometries'] = [self.decode_geometry(geom) for geom in geometry.geometry_collection.geometries]

        elif gt == 'Point':
            obj['coordinates'] = self.decode_point(geometry.line_string.values)

        elif gt == 'MultiPoint' or gt == 'LineString':
            obj['coordinates'] = self.decode_line(geometry.line_string)

        elif (gt == 'MultiLineString') or (gt == 'Polygon'):
            line_strings = geometry.multi_line_string.line_strings
            obj['coordinates'] = [self.decode_line(line) for line in line_strings]

        elif gt == 'MultiPolygon':
            obj['coordinates'] = []
            for polygon in geometry.multi_polygon.polygons:
                obj['coordinates'].append([self.decode_line(line) for line in polygon.line_strings])

        return obj


    def decode_topo_geometry(self, geometry):
        obj = collections.OrderedDict()
        gt = obj['type'] = self.geometry_types[geometry.type]

        self.decode_id(geometry, obj)

        if gt == 'GeometryCollection':
            obj['geometries'] = [self.decode_topo_geometry(g) for g in geometry.geometry_collection.geometries]

        elif gt == 'Point':
            obj['coordinates'] = self.decode_point(geometry.line_string.values)

        elif gt == 'MultiPoint':
            obj['coordinates'] = self.decode_line(geometry.line_string)

        elif gt == 'LineString':
            if len(geometry.line_string.values) == 0: obj['arcs'] = [geometry.arc_index]
            else: obj['arcs'] = self.decode_arcs(geometry.line_string)

        elif (gt == 'MultiLineString') or (gt == 'Polygon'):
            if len(geometry.multi_line_string.line_strings) == 0: obj['arcs'] = [[geometry.arc_index]]
            else: obj['arcs'] = [self.decode_arcs(line) for line in geometry.multi_line_string.line_strings]

        elif gt == 'MultiPolygon':
            obj['arcs'] = []
            for polygon in geometry.multi_polygon.polygons:
                obj['arcs'].append([self.decode_arcs(line) for line in polygon.line_strings])

        if geometry.properties: obj['properties'] = self.decode_properties(geometry.properties)

        return obj


    def decode_point(self, coords):
        if self.transformed: return coords # TopoJSON with transform
        return [float(x) / self.e for x in coords]


    def decode_line(self, line, k=0):
        obj = []
        coords = line.values
        dim = self.dim
        r = range(dim)
        p0 = [0 for i in r]

        for i in xrange(k * dim, len(coords), dim):
            p = [p0[j] + coords[i + j] for j in r]
            obj.append(self.decode_point(p))
            p0 = p

        return obj


    def decode_arcs(self, line):
        obj = []
        i0 = 0
        for i in line.values:
            obj.append(i0 + i)
            i0 += i
        return obj


if __name__ == "__main__":
    filename = sys.argv[1]
    data_str = open(filename,'rb').read()
    obj = Decoder().decode(data_str)
    open(filename.replace('.pbf', '.pbf.json'), 'wb').write(json.dumps(obj))

