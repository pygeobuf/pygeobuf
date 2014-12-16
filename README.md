## pygeobuf

Reference encoding/decoding implementation (in Python) of the [new revision](https://github.com/mapbox/geobuf/issues/27) of [Geobuf](https://github.com/mapbox/geobuf/), a compact geospatial format (essentially a binary form of GeoJSON).

The format is designed to be able to store any GeoJSON or TopoJSON data losslessly.

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
