#!/usr/bin/env python


"""
Core components for `fio centroid`.
"""


import click
from shapely.geometry import shape
from shapely.geometry import mapping

from fio_geoproc.helpers import processor


@click.command()
@processor
def centroid(features):

    """
    Compute geometric centroid of geometries.
    """

    meta = next(features)
    meta['schema'].update(geometry='Point')
    yield meta

    for feat in features:

        feat['geometry'] = mapping(shape(feat['geometry']).centroid())

        yield feat
