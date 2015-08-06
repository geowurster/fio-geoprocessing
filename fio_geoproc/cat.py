"""
fio geoproc cat
"""


import click
import fiona as fio

from fio_geoproc.helpers import generator
from fio_geoproc import _sequence as seq


@click.command()
@click.option(
    '-i', '--infile', required=True,
    help="Input file to process."
)
@click.option(
    '--sequence', is_flag=True,
    help="Input is a sequence of GeoJSON features."
)
@click.option(
    '--crs',
    help="Specify CRS for input data."
)
@generator
def cat(infile, sequence, crs):

    """
    Stream features into the pipeline.
    """

    with seq.open(infile) if sequence else \
            fio.open(infile) as src:

        meta = src.meta.copy()
        meta.update(crs=crs or meta.get('crs'))

        yield src.meta

        for feat in src:
            yield feat
