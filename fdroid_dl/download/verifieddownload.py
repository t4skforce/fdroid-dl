#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from .futuressession import FuturesSessionFlex
from tempfile import NamedTemporaryFile
from concurrent.futures import as_completed
import os.path
import time
import shutil
import hashlib
from datetime import timedelta


logger = logging.getLogger('download.FuturesSessionVerifiedDownload')
class FuturesSessionVerifiedDownload(FuturesSessionFlex):
    BLOCKSIZE = 65536

    def __init__(self, *args, **kwargs):
        super(FuturesSessionVerifiedDownload, self).__init__(*args, **kwargs)
        self.__futures=[]

    def download(self,url,filename,timeout=600,hashType=None,hash=None):
        request = self.get(url,stream=True,timeout=timeout)
        request.filename=filename
        request.hashType=hashType
        request.hash=hash
        request.request_url=url
        self.__futures.append(request)

    @staticmethod
    def verify(filename,hashType,hash):
        h = hashlib.new(hashType)
        with open(filename, 'rb') as file:
            while True:
                byte = file.read(FuturesSessionVerifiedDownload.BLOCKSIZE)
                if not byte:
                    break
                h.update(byte)
        file_hash = h.hexdigest()
        return file_hash == hash

    def completed(self):
        for future in as_completed(self.__futures):
            url = future.request_url
            filename = future.filename
            foldername = os.path.dirname(filename)
            hashType = future.hashType
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
                    if hashType != None:
                        elapsed = time.time() - start
                        logger.info("downloaded %s [%s] (%s) ✔"%(response.request.url,timedelta(seconds=elapsed),hbytes))
                        tmp.seek(0)
                        if FuturesSessionVerifiedDownload.verify(tmp.name,hashType,hash):
                            if not os.path.exists(foldername):
                                os.makedirs(foldername)
                            shutil.copy(tmp.name,filename)
                            elapsed = time.time() - start
                            logger.info("hash verified %s [%s] (%s) ✔"%(response.request.url,timedelta(seconds=elapsed),hbytes))
                            yield (True,filename,bytes,hbytes,timedelta(seconds=elapsed))
                        else:
                            elapsed = time.time() - start
                            logger.warn("hash verification failed %s [%s] (%s) ❌"%(response.request.url,timedelta(seconds=elapsed),hbytes))
                            yield (False,filename,bytes,hbytes,timedelta(seconds=elapsed))
                    else:
                        if not os.path.exists(foldername):
                            os.makedirs(foldername)
                        shutil.copy(tmp.name,filename)
                        elapsed = time.time() - start
                        logger.info("downloaded %s [%s] (%s) ✔"%(response.request.url,timedelta(seconds=elapsed),hbytes))
                        yield (True,filename,bytes,hbytes,timedelta(seconds=elapsed))
            except Exception as e:
                if logging.getLogger().isEnabledFor(logging.DEBUG): logger.exception("Error downloading %s to file %s",url,filename)
                else: logger.warn("Error downloading %s to file %s: %s",url,filename,e.message if hasattr(e,'message') else str(e))
                elapsed = time.time() - start
                yield (False,filename,bytes,hbytes,timedelta(seconds=elapsed))


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
