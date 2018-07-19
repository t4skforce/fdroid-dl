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
from .repoconfig import RepoConfig
from .metadata import Metadata
from .index import Index
from ..json import GenericJSONEncoder


logger = logging.getLogger('model.Config')
class Config(collections.MutableMapping):
    DEFAULTS = {"f-droid":{'https://f-droid.org/repo/':{"apps":["org.fdroid.fdroid"]}},"metadata":{}}

    def __init__(self, filename, repo_dir='./repo', metadata_dir='./metadata', cache_dir='.cache', versions=1, src_download=False, metadata_download=False, default_locale='en-US'):
        self.__filename = filename
        self.__repo = repo_dir
        self.__metadata_dir = metadata_dir
        self.__cache = cache_dir
        self.__src_download = src_download
        self.__metadata_download = metadata_download
        self.__default_locale = default_locale
        self.__versions = versions
        self.__store = {}
        self.__indices={}
        self.__init_defaults()
        self.__prepare_fs()

    @property
    def filename(self):
        return str(self.__filename)

    @property
    def repo_dir(self):
        return str(self.__repo)

    @property
    def metadata_dir(self):
        return str(self.__metadata_dir)

    @property
    def metadata(self):
        return self.__metadata

    @property
    def cache(self):
        return str(self.__cache)

    @property
    def src_download(self):
        return self.__src_download == True

    @property
    def metadata_download(self):
        return self.__metadata_download == True

    @property
    def default_locale(self):
        return str(self.__default_locale)

    @property
    def versions(self):
        return int(self.__versions)

    @property
    def store(self):
        return str(self.__store)

    @property
    def cache_dir(self):
        return str(self.__cache)

    @property
    def size(self):
        return len(self.__store.keys())

    def __init_defaults(self):
        self.__store = copy.deepcopy(Config.DEFAULTS)
        for key in Config.DEFAULTS['f-droid'].keys():
            cfg = RepoConfig(key,self.__store['f-droid'][key],self)
            self.__store['f-droid'][cfg.url]=cfg
        self.__metadata = Metadata(self,Config.DEFAULTS.get('metadata',{}),self.__default_locale)


    def __prepare_fs(self):
        os.makedirs(self.__repo, exist_ok = True)
        os.makedirs(self.__metadata_dir, exist_ok = True)
        os.makedirs(self.__cache, exist_ok = True)

    def load(self):
        if os.path.isfile(self.__filename):
            with open(self.__filename) as config_file:
                try:
                    file_data = json.load(config_file)
                    if 'f-droid' in file_data:
                        for key in file_data['f-droid'].keys():
                            cfg = RepoConfig(key,file_data['f-droid'][key],self)
                            self.__store['f-droid'][cfg.url] = cfg
                    if 'metadata' in file_data:
                        self.__metadata = Metadata(self,file_data['metadata'],self.__default_locale)
                        self.__store['metadata']=self.__metadata
                except Exception:
                    logger.exception("Fatal error reading %s",config_file)


    def save(self):
        with NamedTemporaryFile(mode='w') as tmp:
            json.dump(self.__store, tmp, sort_keys=True, indent=4, cls=GenericJSONEncoder)
            tmp.flush()
            shutil.copy(tmp.name,self.__filename)
        return self

    @property
    def repos(self):
        for key in self.__store['f-droid'].keys():
            cfg = self.__store['f-droid'][key]
            if not isinstance(cfg,RepoConfig):
                self.__store['f-droid'][key] = RepoConfig(key,cfg,self)
            yield cfg

    @property
    def indices(self):
        for repo in self.repos:
            if repo.key in self.__indices:
                yield self.__indices[repo.key]
            elif os.path.exists(repo.filename):
                with Index.fromJSON(repo.filename,key=repo.key,default_locale=self.__default_locale) as idx:
                    self.__indices[repo.key]=idx
                    yield idx

    def repo(self,key):
        if key in self.__store['f-droid']:
            cfg = self.__store['f-droid'][key]
            if not isinstance(cfg,RepoConfig):
                self.__store['f-droid'][key] = RepoConfig(key,cfg,self)
            if not 'error' in cfg:
                return cfg
        raise KeyError("repo with key: %s not found"%key)

    def index(self,key):
        repo = self.repo(key)
        if repo.key in self.__indices:
            return self.__indices[repo.key]
        if os.path.exists(repo.filename):
            with Index.fromJSON(repo.filename,key=repo.key,default_locale=self.__default_locale) as idx:
                self.__indices[repo.key] = idx
            return self.__indices[repo.key]
        raise KeyError("index with key: %s not found on filesystem file: %s"%(key,repo.filename))

    def __repr__(self):
        return "<Config: %s>"%str(self.__store)
    #######################
    # implement "dict"
    #######################
    def __getitem__(self, key):
        return self.__store[key]
    def __setitem__(self, key, value):
        self.__store[key] = value
    def __delitem__(self, key):
        del self.__store[key]
    def __iter__(self):
        return iter(self.__store)
    def __len__(self):
        return len(self.__store)
    #######################
    # implement "with"
    #######################
    def __enter__(self):
        self.load()
        return self

    def __exit__(self, type, value, traceback):
        self.save()
