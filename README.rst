=================
fio-geoprocessing
=================

Because intermediary files are boring.

.. image:: https://travis-ci.org/geowurster/fio-geoprocessing.svg?branch=master
    :target: https://travis-ci.org/geowurster/fio-geoprocessing?branch=master

.. image:: https://coveralls.io/repos/geowurster/fio-geoprocessing/badge.svg?branch=master
    :target: https://coveralls.io/r/geowurster/fio-geoprocessing?branch=master

A Fiona CLI plugin for streaming geoprocessing operations.  Powered by `Shapely <https://github.com/toblerity/shapely>`_.


Commandline Interface
=====================

.. code-block:: console

    Usage: fio geoproc [OPTIONS] COMMAND1 [ARGS]... [COMMAND2 [ARGS]...]...

      Streaming geoprocessing operations.

      Powered by Shapely.

      Example:

          $ fio geoproc cat ${INFILE} \
              centroid \
              reproject --dst-crs EPSG:3857 \
              buffer --dist \
              reproject --dst-crs EPSG:4326 \
              load ${OUTFILE}

    Options:
      --version  Show the version and exit.
      --help     Show this message and exit.

    Commands:
      buffer     Buffer geometries on all sides by a fixed distance.
      cat        Stream features into the pipeline.
      centroid   Compute geometric centroid of geometries.
      load       Load the feature stream into a file on disk.
      reproject  Reproject geometries.
      simplify   Generalize geometries.


Installing
==========

Via pip:

.. code-block:: console

    $ pip install fio-geoprocessing

From source:

.. code-block:: console

    $ git clone https://github.com/geowurster/fio-geoprocessing
    $ cd fio-geoprocessing
    $ python setup.py install


Developing
==========

.. code-block:: console

    $ git clone https://github.com/geowurster/fio-geoprocessing
    $ cd fio-geoprocessing
    $ virtualenv venv
    $ source venv/bin/activate
    $ pip install -e .\[dev\]
    $ py.test tests --cov fio_geoprocessing --cov-report term-missing


License
=======

See ``LICENSE.txt``
