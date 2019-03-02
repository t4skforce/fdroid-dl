#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from tempfile import NamedTemporaryFile
from concurrent.futures import as_completed
import os.path
import time
import shutil
import hashlib
from datetime import timedelta
from .futuressession import FuturesSessionFlex


LOGGER = logging.getLogger('download.FuturesSessionVerifiedDownload')
class FuturesSessionVerifiedDownload(FuturesSessionFlex):
    BLOCKSIZE = 65536

    def __init__(self, *args, **kwargs):
        super(FuturesSessionVerifiedDownload, self).__init__(*args, **kwargs)
        self.__futures = []
        self.__files = {}

    def download(self, url, filename, timeout=600, hash_type=None, hash=None):
        request = self.get(url, stream=True, timeout=timeout)
        request.filename = filename
        request.hash_type = hash_type
        request.hash = hash
        request.request_url = url
        self.__futures.append(request)

    @staticmethod
    def verify(filename, hash_type, hash):
        tmphash = hashlib.new(hash_type)
        with open(filename, 'rb') as file:
            while True:
                byte = file.read(FuturesSessionVerifiedDownload.BLOCKSIZE)
                if not byte:
                    break
                tmphash.update(byte)
        file_hash = tmphash.hexdigest()
        return file_hash == hash

    def completed(self):
        for future in as_completed(self.__futures):
            url = future.request_url
            filename = future.filename
            foldername = os.path.dirname(filename)
            hash_type = future.hash_type
            hash = future.hash
            try:
                response = future.result()
                response.raise_for_status()
                start = time.time()
                with NamedTemporaryFile(mode='wb') as tmp:
                    for chunk in response.iter_content(chunk_size=FuturesSessionVerifiedDownload.BLOCKSIZE):
                        if chunk:
                            tmp.write(chunk)
                    tmp.flush()
                    bytes = os.stat(tmp.name).st_size
                    hbytes = FuturesSessionVerifiedDownload.h_size(bytes)
                    if not hash_type is None:
                        elapsed = time.time() - start
                        LOGGER.info("downloaded %s [%s] (%s) ✔", response.request.url, timedelta(seconds=elapsed), hbytes)
                        tmp.seek(0)
                        if FuturesSessionVerifiedDownload.verify(tmp.name, hash_type, hash):
                            if not os.path.exists(foldername):
                                os.makedirs(foldername)
                            shutil.copy(tmp.name, filename)
                            elapsed = time.time() - start
                            LOGGER.info("hash verified %s [%s] (%s) ✔", response.request.url, timedelta(seconds=elapsed), hbytes)
                            yield (True, filename, bytes, hbytes, timedelta(seconds=elapsed))
                        else:
                            elapsed = time.time() - start
                            LOGGER.warning("hash verification failed %s [%s] (%s) ❌", response.request.url, timedelta(seconds=elapsed), hbytes)
                            yield (False, filename, bytes, hbytes, timedelta(seconds=elapsed))
                    else:
                        if not os.path.exists(foldername):
                            os.makedirs(foldername)
                        shutil.copy(tmp.name, filename)
                        elapsed = time.time() - start
                        LOGGER.info("downloaded %s [%s] (%s) ✔", response.request.url, timedelta(seconds=elapsed), hbytes)
                        yield (True, filename, bytes, hbytes, timedelta(seconds=elapsed))
            except Exception as ex:
                if logging.getLogger().isEnabledFor(logging.DEBUG):
                    LOGGER.exception("Error downloading %s to file %s", url, filename)
                else:
                    LOGGER.warning("Error downloading %s to file %s: %s", url, filename, str(ex))
                elapsed = time.time() - start
                yield (False, filename, bytes, hbytes, timedelta(seconds=elapsed))


    #######################
    # implement "with"
    #######################
    def __enter__(self):
        super(FuturesSessionVerifiedDownload, self).__enter__()
        return self

    def __exit__(self, type, value, traceback):
        super(FuturesSessionVerifiedDownload, self).__exit__(type, value, traceback)
        self.__futures = []
        self.__files = {}
