from setuptools import setup, find_packages
import sys, os

version = '0.6.2'

setup(name='tgext.geo',
      version=version,
      description="TurboGears Extension for Geographic Applications",
      long_description="""""",
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='TurboGears2 MapFish PCL GIS Geo',
      author='Sanjiv Singh',
      author_email='singhsanjivk@gmail.com',
      url='http://code.google.com/p/tgtools/',
      license='MIT',
      namespace_packages = ['tgext'],
      install_requires     = ['tg.devtools >= 2.0b4',
                              'MapFish >= 1.1',
                              'TileCache >= 2.0'],
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      entry_points="""
      [paste.paster_command]
      geo-controller = tgext.geo.commands:TGGeoControllerCommand
      geo-model = tgext.geo.commands:TGGeoModelCommand
      geo-layer = tgext.geo.commands:TGGeoLayerCommand
      geo-tilecache = tgext.geo.commands:TGGeoTileCacheCommand
      """,
      )

