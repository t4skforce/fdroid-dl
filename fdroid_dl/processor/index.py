#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import time
import json
import os
from datetime import timedelta
from concurrent.futures import as_completed, ThreadPoolExecutor
from ..model import Index


logger = logging.getLogger('processor.IndexFileProcessor')
class IndexFileProcessor(ThreadPoolExecutor):

    def __init__(self,*args,**kwargs):
        super(IndexFileProcessor, self).__init__(*args, **kwargs)
        self.__futures = []

    @staticmethod
    def __persist_format(file,repo):
        file.seek(0) # reset fp to beginning
        startchar = file.read(1).decode("utf-8")
        if startchar == '<': repo['format']='xml'
        else: repo['format']='json'
        file.seek(0)

    @staticmethod
    def __process(file,repo,*args):
        start = time.time()
        index=None
        IndexFileProcessor.__persist_format(file,repo)
        with file as f:
            if repo['format'] == 'json':
                index = Index.fromJSON(f,key=repo.url).monkeypatch().save(filename=repo.filename)
            else:
                index = Index.fromXML(f,key=repo.url).monkeypatch().save(filename=repo.filename)
        elapsed = time.time() - start
        return (index,timedelta(seconds=elapsed))+args

    def process(self, file, repo, *args):
        if not hasattr(file,'read'): raise IOError('file error!')
        if repo is None: raise AttributeError('repo is missing')
        args = (file,repo) + args
        self.__futures.append(self.submit(IndexFileProcessor.__process,*args))

    def completed(self):
        for future in as_completed(self.__futures):
            yield future

    #######################
    # implement "with"
    #######################
    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.shutdown()
