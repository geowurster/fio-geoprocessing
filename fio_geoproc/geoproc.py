"""
Main CLI group
"""


from pkg_resources import iter_entry_points

import click
from click_plugins import with_plugins
from fio_geoproc import __version__


@with_plugins(list(iter_entry_points('fio_geoproc.commands')) +
              list(iter_entry_points('fio_geoproc.plugins')))
@click.group(name='geoproc', chain=True)
@click.version_option(prog_name='fio-buffer', version=__version__)
@click.pass_context
def geoproc(ctx):

    """
    Streaming geoprocessing operations.

    Powered by Shapely.

    \b
    Example:
    \b
        $ fio geoproc cat ${INFILE} \\
            centroid \\
            reproject --dst-crs EPSG:3857 \\
            buffer --dist \\
            reproject --dst-crs EPSG:4326 \\
            load ${OUTFILE}
    """

    ctx.obj = {'meta': {}}


@geoproc.resultcallback()
def process_commands(processors):
    """This result callback is invoked with an iterable of all the chained
    subcommands.  As in this example each subcommand returns a function
    we can chain them together to feed one into the other, similar to how
    a pipe on unix works.
    """
    # Start with an empty iterable.
    stream = ()

    # Pipe it through all stream processors.
    for processor in processors:
        stream = processor(stream)

    # # Evaluate the stream and throw away the items.
    for _ in stream or ():
        pass
