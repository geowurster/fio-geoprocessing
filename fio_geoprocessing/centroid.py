#!/usr/bin/env python


"""
Core components for `fio centroid`.
"""


import copy
import logging
from multiprocessing import Pool

import click
import fiona as fio
from shapely.geometry import asShape
from shapely.geometry import mapping

from . import options
from . import helpers


logging.basicConfig()
log = logging.getLogger('fio-geoproc-centroid')


def _processor(args):

    """
    Given a GeoJSON feature, compute its centroid and return the feature with
    updated geometry.

    Parameters
    ----------
    args : dict
        feat : dict
            A GeoJSON feature.
        skip_failures : bool
            Specifies whether failures should crash or just be logged.

    Returns
    -------
    dict
    """

    feat = args['feat']
    skip_failures = args['skip_failures']
    try:
        feat['geometry'] = mapping(asShape(feat['geometry']).centroid())
        return feat
    except Exception:
        log.exception("Feature with ID %s failed" % feat.get('id'))
        if not skip_failures:
            raise


@click.command(name='centroid')
@options.infile
@options.outfile
@options.driver
@options.jobs
@options.skip_failures
@click.pass_context
def centroid(ctx, infile, outfile, driver, skip_failures, jobs):

    """
    Compute geometric centroids.
    """

    helpers.set_verbosity(ctx, log)

    with fio.open(infile, 'r') as src:

        meta = copy.deepcopy(src.meta)
        meta.update(
            driver=driver or src.driver,
        )

        log.debug("Creating output file %s" % outfile)
        log.debug("Meta=%s" % meta)

        with fio.open(outfile, 'w', **meta) as dst:

            task_generator = ({
                'feat': feat,
                'skip_failures': skip_failures
            } for feat in src)

            for o_feat in Pool(jobs).imap_unordered(_processor, task_generator):
                if o_feat is not None:
                    dst.write(o_feat)


if __name__ == '__main__':
    centroid()
