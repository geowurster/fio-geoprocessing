"""
Core components for fio-buffer
"""


import click
import fiona as fio
from shapely.geometry import CAP_STYLE
from shapely.geometry import JOIN_STYLE


def _cb_cap_style(ctx, param, value):

    """
    Click callback to transform `--cap-style` to an `int`.
    """

    return getattr(CAP_STYLE, value)


def _cb_join_style(ctx, param, value):

    """
    Click callback to transform `--join-style` to an `int`.
    """

    return getattr(JOIN_STYLE, value)


def _cb_res(ctx, param, value):

    """
    Click callback to ensure `--res` is `>= 0`.
    """

    if value < 0:
        raise click.BadParameter("must be a positive value")

    return value


@click.command(name='buffer')
@click.argument('infile')
@click.argument('outfile')
@click.option(
    '-f', '--format', '--driver', metavar='NAME', default='ESRI Shapefile',
    help="Output driver name. (default: ESRI Shapefile)"
)
@click.option(
    '--cap-style', type=click.Choice(['flat', 'round', 'square']),
    callback=_cb_cap_style, help="Where geometries terminate, use this style."
)
@click.option(
    '--join-style', type=click.Choice(['round', 'mitre', 'bevel']),
    callback=_cb_join_style, help="Where geometries touch, use this style."
)
@click.option(
    '--res', type=click.INT, callback=_cb_res,
    help="Resolution of the buffer around each vertex of the object."
)
@click.option(
    '--mitre-limit', type=click.FLOAT,
    help="When using a mitre join, limit the maximum length of the join corner according to "
         "this ratio."
)
@click.option(
    '--dist', type=click.FLOAT,
    help="Buffer distance."
)
def buffer_geometries(infile, outfile, driver, cap_style, join_style, res, mitre_limit, dist):

    """
    Buffer geometries.
    """
