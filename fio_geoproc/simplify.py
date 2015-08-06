"""
fio geoproc simplify
"""


import click

from shapely.geometry import mapping
from shapely.geometry import shape

from fio_geoproc.helpers import processor


@click.command()
@click.option(
    '--tolerance', type=click.FLOAT, required=True,
    help="Simplify to within this distance."
)
@click.option(
    '--preserve-topology / --no-preserve-topology', default=True, show_default=True,
    help="If enabled, avoid creating invalid geometries and preserve general geometric shape."
)
@processor
def simplify(features, preserve_topology, tolerance):

    """
    Generalize geometries.

    All points in the simplified object will be within the tolerance distance
    of the original geometry.  By default a slower algorithm is used that
    preserves topology.  If preserve topology is disabled the much quicker
    Douglas-Peucker algorithm, which may produce self-intersecting or otherwise
    invalid geometries.
    """

    yield next(features)

    for feat in features:

        feat['geometry'] = mapping(shape(feat['geometry']).simplify(
            tolerance=tolerance,
            preserve_topology=preserve_topology
        ))

        yield feat
