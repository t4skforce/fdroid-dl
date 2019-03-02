.. fdroid-dl documentation master file, created by
   sphinx-quickstart on Fri Jul 20 15:18:50 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to fdroid-dl's documentation!
=====================================

fdroid-dl is a python based f-droid mirror generation and update utility.
Point at one or more existing f-droid repositories and the utility will
download the metadata (pictures, descriptions,..) for you and place it in your
local system.

.. code-block:: none

  Usage: fdroid-dl [OPTIONS] COMMAND [ARGS]...

  # fdroid-dl update && fdroid update

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   cli
   fdroid_dl/model
   fdroid_dl/update
   fdroid_dl/download
   fdroid_dl/json
   fdroid_dl/processor

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
