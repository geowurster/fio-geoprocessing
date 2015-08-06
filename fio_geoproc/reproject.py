"""
fio geoproc reproject
"""


import click
from fiona.transform import transform_geom

from fio_geoproc.helpers import processor


@click.command()
@click.option(
    '--src-crs', help="Specify CRS for input data.  Defaults to previous command.")
@click.option(
    '--dst-crs', help="CRS for output geometries.", required=True
)
@click.option(
    '--clip-antimeridian', is_flag=True,
    help="Clip geometries at the antimeridian."
)
@click.option(
    '--precision', type=click.FLOAT, default=-1,
    help="Output coordinate precision."
)
@processor
def reproject(features, src_crs, dst_crs, clip_antimeridian, precision):

    """
    Reproject geometries.
    """

    meta = next(features)
    src_crs = src_crs or meta.get('crs')
    meta.update(crs=dst_crs)

    yield meta

    for feat in features:

        feat['geometry'] = transform_geom(
            src_crs=src_crs,
            dst_crs=dst_crs,
            geom=feat['geometry'],
            antimeridian_cutting=clip_antimeridian,
            precision=precision
        )

        yield feat
