#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import collections
import copy
import json
import os, os.path
import hashlib
from urllib.parse import urlparse, urljoin
import shutil
from tempfile import NamedTemporaryFile
from .metadata import Metadata
from .index import Index
from ..json import GenericJSONEncoder


logger = logging.getLogger('model.RepoConfig')
class RepoConfig(collections.MutableMapping):
    EMPTY = {"apps":[]}

    def __init__(self,url,cfg,config):
        self.__config = config
        self.__url = self.__clean_url(url)
        self.__store = {**RepoConfig.EMPTY,**cfg}
        self.__store['id'] = hashlib.sha1(str(self.__url).encode('UTF-8')).hexdigest()

    def __clean_url(self,url):
        p = urlparse(url)
        url = "%s://%s%s"%(p.scheme,p.netloc,p.path)
        if url.endswith('index.xml'): url = url[:-9]
        if url.endswith('index.jar'): url = url[:-9]
        if url.endswith('index-v1.jar'): url = url[:-12]
        if url.endswith('index-v1.json'): url = url[:-13]
        if not url.endswith('/'): url += '/'
        return url

    @property
    def index(self):
        return self.__config.index(self.url)

    @property
    def auth(self):
        auth = self.__store.get('auth',None)
        if auth is None or len(auth) != 2:
            return None
        return (auth[0],auth[1])

    @property
    def verify(self):
        return self.__store.get('ssl_verify',True)

    @property
    def id(self):
        return self.__store.get('id',None)

    @property
    def key(self):
        return self.url

    @property
    def url(self):
        return str(self.__url)

    @property
    def hash(self):
        return self.__store.get('hash',None)

    @property
    def filename(self):
        return os.path.join(self.__config.cache_dir,self.id+".cache")

    @property
    def format(self):
        if 'format' in self.__store:
            return self.__store['format']
        return None

    @property
    def url_index(self):
        return urljoin(self.__url,'index.jar')

    @property
    def url_index_v1(self):
        return urljoin(self.__url,'index-v1.jar')

    @property
    def src_download(self):
        if 'src_download' in self.__store: return self.__store['src_download'] == True
        return self.__config.src_download == True

    @property
    def metadata_download(self):
        if 'metadata_download' in self.__store: return self.__store['metadata_download'] == True
        return self.__config.metadata_download == True

    @property
    def default_locale(self):
        if 'default_locale' in self.__store: return str(self.__store['default_locale'])
        return self.__config.default_locale

    @property
    def versions(self):
        if 'versions' in self.__store: return int(self.__store['versions'])
        return int(self.__config.versions)

    @property
    def apps(self):
        if 'apps' in self.__store:
            if isinstance(self.__store['apps'],str):
                yield self.__store['apps']
            elif isinstance(self.__store['apps'],list):
                for app in self.__store['apps']:
                    yield app

    @property
    def __json__(self):
        ''' make RepoConfig json serializable '''
        return self.__store

    def __repr__(self): return "<RepoConfig: %s>: %s"%(self.__url,self.__store)

    #######################
    # implement hash
    #######################
    def __hash__(self):
        return self.__url.__hash__()

    #######################
    # implement "dict"
    #######################
    def __getitem__(self, key): return self.__store[key]
    def __setitem__(self, key, value): self.__store[key] = value
    def __delitem__(self, key): del self.__store[key]
    def __iter__(self): return iter(self.__store)
    def __len__(self): return len(self.__store)
