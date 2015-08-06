"""
This command is temporary and only exists to help with debugging

fio geoproc printer
"""


import json

import click

from fio_geoproc.helpers import processor


@click.command()
@processor
def printer(features):

    """
    TEMP: Print features like 'fio cat'.
    """

    # Throw away the meta object
    next(features)

    for feat in features:
        click.echo(json.dumps(feat))
