## pygeobuf

Reference encoding/decoding implementation (in Python) of the [new revision](https://github.com/mapbox/geobuf/issues/27) of [Geobuf](https://github.com/mapbox/geobuf/), a compact geospatial format that supports lossless compression of GeoJSON and TopoJSON data.

### Sample compression sizes

 | normal | gzipped
--- | --- | ---
US zips GeoJSON | 101.85 MB | 26.67 MB
US zips Geobuf | 12.43 MB | 10.62 MB
world-50m TopoJSON | 727 KB | 228 KB
world-50m Geobuf | 219 KB | 175 KB

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

Both `encode.py` and `geobuf.encode` accept two optional arguments:

- **precision** &mdash; max number of digits after the decimal point in coordinates, `6` by default.
- **dimensions** &mdash; number of dimensions in coordinates, `2` by default.

### Tests

```bash
python test.py -v
```

The tests run through all `.json` files in the `fixtures` directory,
comparing each original GeoJSON with an encoded/decoded one.
