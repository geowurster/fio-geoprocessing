#!/usr/bin/env python


"""
Core components for `fio buffer`.
"""


import copy
import logging
from multiprocessing import Pool

import click
import fiona as fio
from fiona.transform import transform_geom
from shapely.geometry import CAP_STYLE
from shapely.geometry import JOIN_STYLE
from shapely.geometry import mapping
from shapely.geometry import asShape

from . import helpers
from . import options


logging.basicConfig()
log = logging.getLogger('fio-geoproc-buffer')


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


def _processor(args):

    """
    Process a single feature

    Parameters
    ----------
    args : dict
        feat - A GeoJSON feature to process.
        src_crs - The geometry's CRS.
        buf_crs - Apply buffer after reprojecting to this CRS.
        dst_crs - Reproject buffered geometry to this CRS before returning.
        skip_failures - If True then Exceptions don't stop processing.
        buf_args - Keyword arguments for the buffer operation.

    Returns
    -------
    dict
        GeoJSON feature with updated geometry.
    """

    feat = args['feat']
    src_crs = args['src_crs']
    buf_crs = args['buf_crs']
    dst_crs = args['dst_crs']
    skip_failures = args['skip_failures']
    buf_args = args['buf_args']

    try:
        # src_crs -> buf_crs
        reprojected = transform_geom(
            src_crs, buf_crs, feat['geometry'],
            antimeridian_cutting=True
        )

        # buffering operation
        buffered = asShape(reprojected).buffer(**buf_args)

        # buf_crs -> dst_crs
        feat['geometry'] = transform_geom(
            buf_crs, dst_crs, mapping(buffered),
            antimeridian_cutting=True
        )

        return feat

    except Exception:
        log.exception("Feature with ID %s failed" % feat.get('id'))
        if not skip_failures:
            raise


@click.command()
@click.argument('infile')
@click.argument('outfile')
@options.driver
@click.option(
    '--cap-style', type=click.Choice(['flat', 'round', 'square']), default='round',
    callback=_cb_cap_style, help="Where geometries terminate, use this style. (default: round)"
)
@click.option(
    '--join-style', type=click.Choice(['round', 'mitre', 'bevel']), default='round',
    callback=_cb_join_style, help="Where geometries touch, use this style. (default: round)"
)
@click.option(
    '--res', type=click.INT, callback=_cb_res, default=16,
    help="Resolution of the buffer around each vertex of the object. (default: 16)"
)
@click.option(
    '--mitre-limit', type=click.FLOAT, default=5.0,
    help="When using a mitre join, limit the maximum length of the join corner according to "
         "this ratio. (default: 0.5)"
)
@click.option(
    '--dist', type=click.FLOAT, required=True,
    help="Buffer distance in georeferenced units.  If `--buf-crs` is supplied, then units "
         "must match that CRS."
)
@click.option(
    '--src-crs', help="Specify CRS for input data.  Not needed if specified in infile."
)
@click.option(
    '--buf-crs', help="Perform buffer operations in a different CRS.  Defaults to `--src-crs` "
                      "if not specified."
)
@click.option(
    '--dst-crs', help="Reproject geometries to a different CRS before writing.  Defaults to "
                      "`--buf-crs` if not specified."
)
@click.option(
    '--otype', 'output_geom_type', default='MultiPolygon',
    help="Specify output geometry type. (default: MultiPolygon)"
)
@options.skip_failures
@options.jobs
@click.pass_context
def buffer(ctx, infile, outfile, driver, cap_style, join_style, res, mitre_limit,
           dist, src_crs, buf_crs, dst_crs, output_geom_type, skip_failures, jobs):

    """
    Buffer geometries with shapely.

    Default settings - buffer geometries in the input CRS:
    \b
        $ fio buffer ${INFILE} ${OUTFILE} --dist 10

    Read geometries from one CRS, buffer in another, and then write to a third:
    \b
        $ fio buffer ${INFILE} ${OUTFILE} \\
            --dist 10 \\
            --buf-crs EPSG:3857 \\
            --dst-crs EPSG:32618

    Control cap style, mitre limit, segment resolution, and join style:
    \b
        $ fio buffer ${INFILE} ${OUTFILE} \\
            --dist 0.1 \\
            --res 5 \\
            --cap-style flat \\
            --join-style mitre \\
            --mitre-limit 0.1\\
    """

    helpers.set_verbosity(ctx, log)

    with fio.open(infile, 'r') as src:

        log.debug("Resolving CRS fall backs")

        src_crs = src_crs or src.crs
        buf_crs = buf_crs or src_crs
        dst_crs = dst_crs or buf_crs

        log.debug("src_crs=%s" % src_crs)
        log.debug("buf_crs=%s" % buf_crs)
        log.debug("dst_crs=%s" % dst_crs)

        meta = copy.deepcopy(src.meta)
        meta.update(
            driver=driver or src.driver,
            crs=dst_crs
        )
        if output_geom_type:
            meta['schema'].update(geometry=output_geom_type)

        log.debug("Creating output file %s" % outfile)
        log.debug("Meta=%s" % meta)

        with fio.open(outfile, 'w', **meta) as dst:

            # Keyword arguments for `<Geometry>.buffer()`
            buf_args = {
                'distance': dist,
                'resolution': res,
                'cap_style': cap_style,
                'join_style': join_style,
                'mitre_limit': mitre_limit
            }

            # A generator that produces the arguments required for `_processor()`
            task_generator = (
                {
                    'feat': feat,
                    'src_crs': src_crs,
                    'buf_crs': buf_crs,
                    'dst_crs': dst_crs,
                    'skip_failures': skip_failures,
                    'buf_args': buf_args
                } for feat in src)

            for o_feat in Pool(jobs).imap_unordered(_processor, task_generator):
                if o_feat is not None:
                    dst.write(o_feat)


if __name__ == '__main__':
    buffer()
