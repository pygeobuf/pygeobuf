## pygeobuf

Reference encoding/decoding Python implementation of the [new revision](https://github.com/mapbox/geobuf/issues/27) of [Geobuf](https://github.com/mapbox/geobuf/), our compact geospatial format (binary GeoJSON equivalent).

### Usage

Command line:

```bash
./encode.py sample.json 6 # -> sample.pbf, with 6-digit precision
./decode.py sample.pbf    # -> sample.pbf.json
```

As a module:

```python
import geobuf

pbf = geobuf.encode(geojson, 6) # GeoJSON -> Geobuf string
geojson = geobuf.decode(pbf)    # Geobuf string -> GeoJSON
```

Precision (number of digits after the decimal point) is optional, `6` by default.

### Tests

```bash
python test.py -v
```

The tests run through all `.json` files in the `fixtures` directory,
comparing each original GeoJSON with an encoded/decoded one.
