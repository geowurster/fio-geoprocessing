"""
Helper objects used by multiple commands
"""


def set_verbosity(ctx, log):
    # fio has a -v flag so just use that to set the logging level
    # Extra checks are so this plugin doesn't just completely crash due
    # to upstream changes.
    if isinstance(getattr(ctx, 'obj'), dict) and isinstance(ctx.obj.get('verbosity'), int):
        log.setLevel(ctx.obj['verbosity'])
