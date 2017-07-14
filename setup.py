from codecs import open as codecs_open
import distutils.log
import os.path
import shutil
from setuptools import setup, find_packages
import subprocess


# Try to convert README markdown to restructured text using pandoc.
try:
    subprocess.call(
        'pandoc --from=markdown --to=rst --output=README README.md',
        shell=True)
    assert os.path.exists('README')
except:
    distutils.log.warn(
        "Conversion of README.md to restructured text was not successful.")
    shutil.copy('README.md', 'README')

# Get the long description from the relevant file
with codecs_open('README', encoding='utf-8') as f:
    long_description = f.read()

setup(name='geobuf',
      version='2.0.0',
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
      install_requires=['click', 'protobuf', 'six'],
      extras_require={
          'test': ['pytest'],
      },
      entry_points="""
      [console_scripts]
      geobuf=geobuf.scripts.cli:cli
      """)
