#!/usr/bin/env python


"""
Setup script for fio-geoprocessing
"""


import os
from setuptools import setup
from setuptools import find_packages


with open('README.rst') as f:
    readme = f.read().strip()


version = None
author = None
email = None
source = None
with open(os.path.join('fio_geoproc', '__init__.py')) as f:
    for line in f:
        if line.strip().startswith('__version__'):
            version = line.split('=')[1].strip().replace('"', '').replace("'", '')
        elif line.strip().startswith('__author__'):
            author = line.split('=')[1].strip().replace('"', '').replace("'", '')
        elif line.strip().startswith('__email__'):
            email = line.split('=')[1].strip().replace('"', '').replace("'", '')
        elif line.strip().startswith('__source__'):
            source = line.split('=')[1].strip().replace('"', '').replace("'", '')
        elif None not in (version, author, email, source):
            break


setup(
    author=author,
    author_email=email,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Topic :: Scientific/Engineering :: GIS'
    ],
    description="A Fiona CLI plugin for performing streaming geoprocessing operations.",
    entry_points="""
        [fiona.fio_plugins]
        geoproc=fio_geoproc.geoproc:geoproc

        [fio_geoproc.commands]
        buffer=fio_geoproc.buffer:buffer
        cat=fio_geoproc.cat:cat
        centroid=fio_geoproc.centroid:centroid
        load=fio_geoproc.load:load
        reproject=fio_geoproc.reproject:reproject
        simplify=fio_geoproc.simplify:simplify

        # This command will be removed
        printer=fio_geoproc.printer:printer
    """,
    extras_require={
        'dev': [
            'pytest',
            'pytest-cov',
            'coveralls'
        ]
    },
    include_package_data=True,
    install_requires=[
        'click>=0.3',
        'shapely',
        'fiona>=1.6',
        'click_plugins'
    ],
    keywords='Fiona GIS command line plugin',
    license="New BSD",
    long_description=readme,
    name='fio-geoprocessing',
    packages=find_packages(),
    url=source,
    version=version,
    zip_safe=True
)
