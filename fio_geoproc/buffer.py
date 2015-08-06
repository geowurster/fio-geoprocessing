"""
fio geoproc buffer
"""


import click
from shapely.geometry import CAP_STYLE
from shapely.geometry import JOIN_STYLE
from shapely.geometry import mapping
from shapely.geometry import shape

from fio_geoproc.helpers import generator


def _cb_dist(ctx, param, value):

    """
    Click callback to ensure `--distance` can be either a float or a field name.
    """

    try:
        return float(value)
    except ValueError:
        return value


@click.command(short_help="Buffer geometries on all sides by a fixed distance.")
@click.option(
    '--cap-style', type=click.Choice(['flat', 'round', 'square']),
    default='round', show_default=True,
    help="Where geometries terminate, use this style."
)
@click.option(
    '--join-style', type=click.Choice(['round', 'mitre', 'bevel']),
    default='round', show_default=True,
    help="Where geometries touch, use this style."
)
@click.option(
    '--res', type=click.INT, default=16, show_default=True,
    help="Resolution of the buffer around each vertex of the geometry."
)
@click.option(
    '--mitre-limit', type=click.FLOAT, default=5.0, show_default=True,
    help="When using a mitre join, limit the maximum length of the join corner according to "
         "this ratio."
)
@click.option(
    '--distance', metavar='FLOAT|FIELD', required=True, callback=_cb_dist,
    help="Buffer distance or field containing distance values.  Units match --buf-crs.  "
         "When buffering with a field, feature's with a null value are unaltered."
)
@generator
def buffer(features, cap_style, join_style, res, mitre_limit, distance):

    """
    Geometries can be dilated with a positive distance, eroded with a negative
    distance, and in some cases cleaned or repaired with a distance of 0.
    """

    meta = next(features)
    meta['schema'].update(geometry='MultiPolygon')
    yield meta

    for feat in features:

        if not isinstance(distance, float):
            dist_val = distance
        else:
            try:
                dist_val = feat['properties'][distance]
            except ValueError:
                raise click.BadParameter("Distance field '{}' not in feature".format(distance))

        g = shape(feat['geometry'])
        feat['geometry'] = mapping(g.buffer(
            distance=dist_val,
            resolution=res,
            cap_style=getattr(CAP_STYLE, cap_style),
            join_style=getattr(JOIN_STYLE, join_style),
            mitre_limit=mitre_limit
        ))

        yield feat
