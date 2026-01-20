from setuptools import setup, find_packages
from pathlib import Path

setup(name='geobuf',
      version='2.0.1',
      description=(
          u"Geobuf is a compact binary geospatial format for lossless "
          u"compression of GeoJSON."),
      long_description=Path('README.md').read_text(),
      long_description_content_type='text/markdown',
      classifiers=[],
      keywords='data gis geojson protobuf',
      author=u"Vladimir Agafonkin",
      author_email='vladimir@mapbox.com',
      url='https://github.com/mapbox/pygeobuf',
      license='MIT',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=['click', 'protobuf', 'six'],
      extras_require={
          'test': ['pytest'],
      },
      entry_points="""
      [console_scripts]
      geobuf=geobuf.scripts.cli:cli
      """)
