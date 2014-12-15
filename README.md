### pygeobuf

Reference encoding/decoding Python implementation of the [new revision](https://github.com/mapbox/geobuf/issues/27) of [Geobuf](https://github.com/mapbox/geobuf/), our compact geospatial format (binary GeoJSON equivalent).

#### Usage

Command line:

```bash
./encode.py us-states.json # generates us-states.pbf
./decode.py us-states.pbf  # generates us-states.pbf.json
```

As a module:

```python
import geobuf

pbf_str = geobuf.encode(json)    # encode a GeoJSON object into a Geobuf string
geojson = geobuf.decode(pbf_str) # decode a Geobuf string to a GeJSON object
```

#### Tests

```bash
python test.py -v
```

The tests run through all `.json` files in the `fixtures` directory,
comparing each original GeoJSON with an encoded/decoded one.
