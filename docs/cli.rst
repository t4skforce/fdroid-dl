Command Line Interface
==================================

**Main command parameters**

.. code-block:: none

  Usage: fdroid-dl [OPTIONS] COMMAND [ARGS]...

    Is a python based f-droid mirror generation and update utility. Point at
    one or more existing f-droid repositories and the utility will download
    the metadata (pictures, descriptions,..) for you and place it in your
    local system.

    Simply run "fdroid-dl update && fdroid update" in your folder with repo
    and you are set.

  Options:
    -d, --debug               enable debug level logging
    -c, --config FILE         location of your fdroid-dl.json configuration file
                              [default: fdroid-dl.json]
    -r, --repo DIRECTORY      location of your fdroid repository to store the
                              apk files  [default: ./repo]
    -m, --metadata DIRECTORY  location of your fdroid metadata to store the
                              asset files  [default: ./metadata]
    --cache DIRECTORY         location for fdroid-dl to store cached data
                              [default: ./.cache]
    --help                    Show this message and exit.

  Commands:
    update  starts updating process

**Update command parameters**

.. code-block:: none

  Usage: fdroid-dl update [OPTIONS] COMMAND [ARGS]...

  Options:
    --index / --no-index        download repository index files  [default: True]
    --metadata / --no-metadata  download metadata assset files  [default: True]
    --apk / --no-apk            download apk files  [default: True]
    --apk-versions INTEGER      how many versions of apk to download  [default:
                                1]
    --src / --no-src            download src files  [default: True]
    --threads INTEGER           configure number of parallel threads used for
                                download  [default: 10]
    --head-timeout INTEGER      maximum time in seconds a HEAD request is
                                allowed to take  [default: 10]
    --index-timeout INTEGER     maximum time in seconds index file download is
                                allowed to take  [default: 60]
    --download-timeout INTEGER  maximum time in seconds file download is allowed
                                to take  [default: 60]
    --help                      Show this message and exit.
