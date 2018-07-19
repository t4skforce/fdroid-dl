#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from .index import IndexUpdate
from .metadata import MetadataUpdate
from .apk import ApkUpdate
from .src import SrcUpdate

logger = logging.getLogger('update.Update')
class Update:
    ''' handels downloading of repo related data '''
    def __init__(self,config,max_workers=10,head_timeout=10,index_timeout=60,download_timeout=60):
        self.__config = config
        self.__head_timeout = head_timeout
        self.__index_timeout = index_timeout
        self.__download_timeout = download_timeout
        self.__max_workers = max_workers
        self.__index = IndexUpdate(config,head_timeout=head_timeout,index_timeout=index_timeout,max_workers=max_workers)
        self.__meta = None
        self.__apk = ApkUpdate(config,download_timeout=download_timeout,max_workers=max_workers)
        self.__src = SrcUpdate(config,download_timeout=download_timeout,max_workers=max_workers)

    def index(self):
        self.__index.download(*self.__index.required(self.__config.repos,timeout=self.__head_timeout),timeout=self.__index_timeout)
        return self

    def metadata(self):
        self.__meta = MetadataUpdate(self.__config,download_timeout=self.__download_timeout,max_workers=self.__max_workers)
        self.__meta.updateYAML()
        self.__meta.updateAssets()
        return self

    def apk(self):
        self.__apk.update()
        return self

    def src(self):
        self.__src.update()
        return self
