### pygeobuf

Reference encoding/decoding Python implementation of the [new revision](https://github.com/mapbox/geobuf/issues/27) of [Geobuf](https://github.com/mapbox/geobuf/), our compact geospatial format (binary GeoJSON equivalent).

#### Usage

Command line:

```bash
./encode.py us-states.json 6 # encodes into us-states.pbf; 2nd optional argument is precision (num of digits)
./decode.py us-states.pbf    # decodes into us-states.pbf.json
```

As a module:

```python
import geobuf

pbf_str = geobuf.encode(json, 6) # encode a GeoJSON object into a Geobuf string, optionally specifying precision
geojson = geobuf.decode(pbf_str) # decode a Geobuf string to a GeJSON object
```

#### Tests

```bash
python test.py -v
```

The tests run through all `.json` files in the `fixtures` directory,
comparing each original GeoJSON with an encoded/decoded one.
