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

from . import helpers
from . import options


logging.basicConfig()
log = logging.getLogger('fio-geoproc-reproject')


def _processor(args):

    """
    Reproject a single feature's geometry.

    Parameters
    ----------
    args : dict
        feat : dict
            A GeoJSON feature to process.
        src_crs : str
            The geometry's CRS.
        dst_crs : str
            Reproject buffered geometry to this CRS before returning.
        skip_failures : bool
            If True then Exceptions don't stop processing.

    Returns
    -------
    dict
        GeoJSON feature with updated geometry.
    """

    feat = args['feat']
    src_crs = args['src_crs']
    dst_crs = args['dst_crs']
    skip_failures = args['skip_failures']

    try:
        feat['geometry'] = transform_geom(src_crs, dst_crs, feat['geometry'])
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
    '--src-crs', help="Specify CRS for input data.  Not needed if specified in infile."
)
@click.option(
    '--dst-crs', help="CRS for output file and geometries.", required=True
)
@options.skip_failures
@options.jobs
@click.pass_context
def reproject(ctx, infile, outfile, driver, src_crs, dst_crs, skip_failures, jobs):

    """
    Reproject geometries in one CRS to another.
    """

    helpers.set_verbosity(ctx, log)

    with fio.open(infile, 'r') as src:

        src_crs = src_crs or src.crs

        log.debug("src_crs=%s" % src_crs)
        log.debug("dst_crs=%s" % dst_crs)

        meta = copy.deepcopy(src.meta)
        meta.update(
            driver=driver or src.driver,
            crs=dst_crs
        )

        log.debug("Creating output file %s" % outfile)
        log.debug("Meta=%s" % meta)

        with fio.open(outfile, 'w', **meta) as dst:

            # A generator that produces the arguments required for `_processor()`
            task_generator = (
                {
                    'feat': feat,
                    'src_crs': src_crs,
                    'dst_crs': dst_crs,
                    'skip_failures': skip_failures,
                } for feat in src)

            for o_feat in Pool(jobs).imap_unordered(_processor, task_generator):
                if o_feat is not None:
                    dst.write(o_feat)


if __name__ == '__main__':
    reproject()
