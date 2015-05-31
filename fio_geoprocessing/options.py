"""
Common CLI options
"""


from multiprocessing import cpu_count

import click


infile = click.argument('infile', required=True)
outfile = click.argument('outfile', required=True)
driver = click.option(
    '-f', '--format', '--driver', metavar='NAME',
    help="Output driver name. (default: infile's driver)"
)
skip_failures = click.option(
    '--skip-failures', is_flag=True,
    help="Skip geometries that fail somewhere in the processing pipeline."
)
jobs = click.option(
    '--jobs', type=click.IntRange(1, cpu_count()), default=1,
    help="Process geometries in parallel across N cores.  The goal of this flag is speed so "
         "feature order is not preserved. (default: 1)"
)
