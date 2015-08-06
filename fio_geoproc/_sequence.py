from codecs import open as codecs_open
import json
import os
import sys

import fiona


FIELD_TYPES_MAP_REV = dict([(v, k) for k, v in fiona.FIELD_TYPES_MAP.items()])


def open(path, mode='r', **kwargs):

    """
    Open a file containing GeoJSON feature sequences.
    Parameters
    ----------
    path : str
        Path to file to open.  use '-' for stdin and stdout.
    mode : str, optional
        Read, write, or append data with r, w, and a.
    kwargs : **kwargs, optional
        Additional keyword arguments for `FeatureStream()`.
    Returns
    -------
    FeatureStream
    """

    if path == '-' and mode == 'r':
        f = sys.stdin
    elif path == '-' and mode in ('w', 'a'):
        f = sys.stdout
    else:
        f = codecs_open(path, mode=mode, encoding='utf-8')

    return FeatureStream(f, mode=mode, **kwargs)


class FeatureStream(object):

    """
    A file-like interface for operating on a stream of GeoJSON features.
    """

    def __init__(self, f, mode='r', crs='EPSG:4326', use_rs=False, schema=None):

        """
        Parameters
        ----------
        f : file
            A file-like object opened in a mode that compliments `mode`.
        mode : str, optional
            Read, write, or append data with r, w, and a.
        use_rs : bool, optional
            When writing, prepend each feature with a record separator (0x1E).
            Ignored when reading.
        kwargs : **kwargs, optional
            Additional arguments for `json.loads()` or `json.dumps()`.
        """

        if mode not in ('r', 'w', 'a'):
            raise ValueError(
                "mode string must be one of 'r', 'w', or 'a', not %s" % mode)

        self._f = f
        self._mode = mode
        self._use_rs = use_rs
        self._geom_type = None
        self._crs = crs
        self._schema = schema

        self._first_line = None
        if self._mode == 'r':
            self._first_line = json.loads(next(self._f))

            self._schema = {'geometry': self._first_line['geometry']['type']}
            self._schema['properties'] = dict(
                [(k, FIELD_TYPES_MAP_REV.get(type(v)) or 'str')
                 for k, v in self._first_line['properties'].items()])

    def __repr__(self):
        return "<%s FeatureStream '%s', mode '%s' at %s>" % (
            self.closed and "closed" or "open",
            str(self.name), self.mode, hex(id(self)))

    def __iter__(self):
        return self

    def __next__(self):
        """Returns the next feature from the underlying file."""

        if self.closed:
            raise ValueError("I/O operation on closed file")
        elif self.mode != 'r':
            raise IOError("File not open for reading")

        if self._first_line:
            line = self._first_line
            self._first_line = None
        else:
            line = next(self._f)

            # Cut down on some overhead
            if self._use_rs:
                line = line.strip(u'\x1e')
            line = json.loads(line)

        return line

    next = __next__

    @property
    def mode(self):
        """I/O mode"""
        return self._mode

    @property
    def name(self):
        """Path/name of file on disk."""
        return getattr(self._f, 'name', '<UNKNOWN>')

    @property
    def crs(self):
        return self._crs

    @property
    def geom_type(self):
        return self._geom_type

    @property
    def meta(self):
        return {
            'crs': self._crs,
            'driver': 'GeoJSON',
            'schema': self._schema
        }

    def write(self, feature):
        """Write a feature to disk."""

        if self.closed:
            raise ValueError("I/O operation on closed file")
        if self.mode not in ('a', 'w'):
            raise IOError("File not open for writing")

        if self._use_rs:
            self._f.write(u'\u001e')

        self._f.write(json.dumps(feature) + os.linesep)

    def close(self):
        """Close file and sync to disk."""
        self._f.close()

    @property
    def closed(self):
        """``False`` if data can be accessed, otherwise ``True``."""
        return self._f.closed

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()

    def __del__(self):
        # Note: you can't count on this being called. Call close() explicitly
        # or use the context manager protocol ("with").
        self.__exit__(None, None, None)
