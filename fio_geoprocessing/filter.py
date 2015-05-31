#!/usr/bin/env python


"""
Core components for `fio filter`.
"""


import copy
import logging
from multiprocessing import Pool

import click
import fiona as fio

from . import options
from . import helpers


logging.basicConfig()
log = logging.getLogger('fio-geoproc-filter')


def _cb_bbox(ctx, param, value):

    """
    Click callback to validate `--bbox`.
    """

    if value:
        x_min, y_min, x_max, y_max = value
        if (x_min > x_max) or (y_min > y_max):
            raise click.BadParameter(
                'self-intersection: {bbox}'.format(bbox=value))

    return value


def _processor(args):

    """
    Apply filter expressions to a filter to determine if it should be written.

    Expressions are evaluated with `eval()`, a limited global scope, and the
    feature's properties as the local scope with an additional `feat` key that
    contains the entire feature and a `props` key that contains the properties
    dictionary.

    Parameters
    ----------
    args : dict
        feat : dict
            GeoJSON feature to test against.
        skip_failures : bool
            Specifies whether failures should crash or just be logged.
        expressions : str
            Pythonic expressions that evaluate as `True` or `False`.  Expressions
            are evaluated in order and the feature will only be returned if all
            evaluate as `True`.
        global_scope : dict
            A dictionary like `globals()` but without access to objects like
            `exec()`, `execfile()`, `eval()`, `globals()`, etc.

    Returns
    -------
    dict or None
        A GeoJSON feature if the expressions passed or `None` if something failed.
    """

    feat = args['feat']
    skip_failures = args['skip_failures']
    expressions = args['expressions']
    global_scope = args['global_scope']

    props = feat.get('properties', {}).copy()
    local_scope = props
    if 'feat' not in local_scope:
        local_scope['feat'] = feat
    if 'props' not in local_scope:
        local_scope['props'] = props

    try:
        for expr in expressions:
            result = eval(expr, global_scope, local_scope)
            if not result:
                break
        else:
            return feat
    except Exception:
        log.exception("Feature with ID %s failed" % feat.get('id'))
        if not skip_failures:
            raise


@click.command()
@options.infile
@options.outfile
@click.argument(
    '--expr', 'expressions', multiple=True,
    help="Python expression that evaluates as boolean.  Multiple expressions can be specified "
         "and are evaluated in order.  Only features that pass all expressoins are written."
)
@click.option(
    '--bbox', nargs=4, type=click.FLOAT, metavar="X_MIN Y_MIN X_MAX Y_MAX", callback=_cb_bbox,
    help="Only process features intersecting the specified bounding box."
)
@options.driver
@options.skip_failures
@options.jobs
@click.pass_context
def filter(ctx, infile, outfile, driver, expressions, skip_failures, jobs, bbox):

    """
    Filter features by expression.
    """

    helpers.set_verbosity(ctx, log)

    scope_blacklist = ('eval', 'compile', 'exec', 'execfile', 'builtin', 'builtins',
                       '__builtin__', '__builtins__', 'globals', 'locals')

    global_scope = {
        k: v for k, v in globals().items() if k not in ('builtins', '__builtins__')}
    global_scope['__builtins__'] = {
        k: v for k, v in globals()['__builtins__'].items() if k not in scope_blacklist}
    global_scope['builtins'] = global_scope['__builtins__']

    with fio.open(infile, 'r') as src:

        meta = copy.deepcopy(src.meta)
        meta.update(
            driver=driver or src.driver,
        )

        log.debug("Creating output file %s" % outfile)
        log.debug("Meta=%s" % meta)

        with fio.open(outfile, 'w', **meta) as dst:

            task_generator = (
                {
                    'feat': feat,
                    'skip_failures': skip_failures,
                    'expressions': expressions,
                    'global_scope': global_scope
                } for feat in src.filter(bbox))

            for o_feat in Pool(jobs).imap_unordered(_processor, task_generator):
                if o_feat is not None:
                    dst.write(o_feat)


if __name__ == '__main__':
    filter()
