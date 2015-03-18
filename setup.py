from codecs import open as codecs_open
from setuptools import setup, find_packages


# Get the long description from the relevant file
with codecs_open('README.md', encoding='utf-8') as f:
    long_description = f.read()

setup(name='pygeobuf',
      version='1.0',
      description=(
        u"Geobuf is a compact binary geospatial format for lossless "
        u"compression of GeoJSON and TopoJSON data."),
      long_description=long_description,
      classifiers=[],
      keywords='data gis geojson topojson protobuf',
      author=u"Vladimir Agafonkin",
      author_email='vladimir@mapbox.com',
      url='https://github.com/mapbox/pygeobuf',
      license='MIT',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'protobuf',
      ],
      extras_require={
          'test': ['pytest'],
      })
