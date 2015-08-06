"""
fio geoproc load
"""


import click
import fiona as fio

from fio_geoproc.helpers import processor
from fio_geoproc import _sequence as seq


GEOM_TYPES = [
    'Point',
    'MultiPoint',
    'LineString',
    'MultiLineString',
    'Polygon',
    'MultiPolygon',
    'GeometryCollection'
]


@click.command(name='load')
@click.option(
    '-o', '--outfile', required=True,
    help="Output file."
)
@click.option(
    '-f', '--format', '--driver',
    help="Output format driver name.  Defaults to same as input file."
)
@click.option(
    '--gtype', type=click.Choice(GEOM_TYPES),
    help="Set geometry type of output file.  Defaults to previous command."
)
@click.option(
    '--sequence', is_flag=True,
    help="Write a GeoJSON feature sequence."
)
@click.option(
    '--rs', 'use_rs', is_flag=True,
    help="Use record separators when writing a feature sequence."
)
@processor
def load(features, outfile, driver, gtype, sequence, use_rs):

    """
    Load the feature stream into a file on disk.
    """

    meta = next(features)
    meta.update(driver=driver or meta['driver'])
    meta['schema'].update(geometry=gtype or meta['schema']['geometry'])

    with seq.open(outfile, 'w', use_rs=use_rs) if sequence else \
            fio.open(outfile, 'w', **meta) as dst:
        for feat in features:
            dst.write(feat)
