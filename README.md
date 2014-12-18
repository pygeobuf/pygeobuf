## pygeobuf

Reference encoding/decoding implementation (in Python) of the [new revision](https://github.com/mapbox/geobuf/issues/27) of [Geobuf](https://github.com/mapbox/geobuf/), a compact geospatial format that supports lossless compression of GeoJSON and TopoJSON data.

#### Sample compression sizes

                    | normal    | gzipped
------------------- | --------- | --------
us-zips.json 	    | 101.85 MB | 26.67 MB
us-zips.pbf         | 12.43 MB  | 10.61 MB
us-zips.topo.json   | 15.02 MB  | 3.19 MB
us-zips.topo.pbf    | 5.69 MB   | 2.92 MB
idaho.json          | 10.92 MB  | 2.57 MB
idaho.pbf           | 1.37 MB   | 1.17 MB
world-50m.topo.json | 727 KB    | 228 KB
world-50m.topo.pbf  | 212 KB    | 167 KB

### Usage

Command line:

```bash
./encode.py sample.json # -> sample.pbf
./decode.py sample.pbf  # -> sample.pbf.json
```

As a module:

```python
import geobuf

pbf = geobuf.encode(my_json) # GeoJSON or TopoJSON -> Geobuf string
my_json = geobuf.decode(pbf) # Geobuf string -> GeoJSON or TopoJSON
```

The `encode` function accepts a dict-like object, for example the result of `json.loads(json_str)`.

Both `encode.py` and `geobuf.encode` accept two optional arguments:

- **precision** &mdash; max number of digits after the decimal point in coordinates, `6` by default.
- **dimensions** &mdash; number of dimensions in coordinates, `2` by default.

### Tests

```bash
python test.py -v
```

The tests run through all `.json` files in the `fixtures` directory,
comparing each original GeoJSON with an encoded/decoded one.
