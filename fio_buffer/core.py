#!/usr/bin/env python


"""
Core components for fio-buffer
"""


import copy
import logging

import click
import fiona as fio
from fiona.transform import transform_geom
from shapely.geometry import CAP_STYLE
from shapely.geometry import JOIN_STYLE
from shapely.geometry import mapping
from shapely.geometry import asShape


logging.basicConfig()
log = logging.getLogger('fio-buffer')


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
    '-f', '--format', '--driver', metavar='NAME',
    help="Output driver name. (default: infile's driver)"
)
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
    '--src-crs', help="Specify CRS for input data."
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
@click.option(
    '--skip-failures', is_flag=True,
    help="Skip geometries that fail somewhere in the processing pipeline."
)
@click.pass_context
def buffer_geometries(ctx, infile, outfile, driver, cap_style, join_style, res, mitre_limit,
                      dist, src_crs, buf_crs, dst_crs, output_geom_type, skip_failures):

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

    # fio has a -v flag so just use that to set the logging level
    # Extra checks are so this plugin doesn't just completely crash due
    # to upstream changes.
    if isinstance(getattr(ctx, 'obj'), dict) and isinstance(ctx.obj.get('verbosity'), int):
        log.setLevel(ctx.obj['verbosity'])

    with fio.open(infile, 'r') as src:

        src_crs = src_crs or src.crs
        buf_crs = buf_crs or src_crs
        dst_crs = dst_crs or buf_crs

        log.debug("Resolving CRS fall backs")
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

        with fio.open(outfile, 'w', **meta) as dst, click.progressbar(src) as features:
            for feat in features:

                try:
                    # src_crs -> buf_crs
                    reprojected = transform_geom(
                        src_crs, buf_crs, feat['geometry'],
                        antimeridian_cutting=True
                    )

                    # buffering operation
                    buffered = asShape(reprojected).buffer(
                        distance=dist,
                        resolution=res,
                        cap_style=cap_style,
                        join_style=join_style,
                        mitre_limit=mitre_limit
                    )

                    # buf_crs -> dst_crs
                    feat['geometry'] = transform_geom(
                        buf_crs, dst_crs, mapping(buffered),
                        antimeridian_cutting=True
                    )

                    dst.write(feat)

                except Exception:
                    log.exception("Feature %s failed" % feat.get('id'))
                    if not skip_failures:
                        raise


if __name__ == '__main__':
    buffer_geometries()
