#!/usr/bin/env python3
# -*- coding: utf-8 -*-

try:
    from collections.abc import MutableMapping
except ImportError:
    from collections import MutableMapping
import logging
import json
import hashlib
import copy
import re
from ..json import GenericJSONEncoder
from .index import Index
from .appmetadata import AppMetadata

LOGGER = logging.getLogger('model.Metadata')
class Metadata(MutableMapping):
    def __init__(self, repoman, config={}, default_locale='en-US'):
        self.__repoman = repoman
        self.__config = config
        self.__store = {}
        self.__default_locale = default_locale
        self.__load()

    def __load(self):
        # load from config file
        for key in self.__config.keys():
            self.__config[key] = AppMetadata(key, self.__config[key], default_locale=self.__default_locale)
            self.__store[key] = AppMetadata(key, self.__config[key], default_locale=self.__default_locale)
        # load from index files

    def load(self, index):
        if not isinstance(index, Index) and not isinstance(index, dict) and not isinstance(index, str):
            raise NotImplementedError("I can only load instances of Index at the moment")
        if isinstance(index, str):
            index = self.__repoman.index(index)
        apps = index.get('apps', [])
        for app in apps:
            self.add(app)

    def load_all(self):
        for index in self.__repoman.indices:
            LOGGER.info("loading index: %s", index.key)
            apps = index.get('apps', [])
            for app in apps:
                appid = app.get('packageName', None)
                if not appid is None:
                    self.add(AppMetadata(appid, app, default_locale=self.__default_locale))
            LOGGER.info("loaded index: %s apps: %s", index.key, len(apps))
        return self

    def add(self, appmetadata):
        if appmetadata is None:
            return
        if appmetadata.id is None:
            KeyError('cant add metadata without id! %s'%appmetadata)
        if appmetadata.id in self.__store:
            self.__store[appmetadata.id].merge(appmetadata)
        else:
            self.__store[appmetadata.id] = appmetadata
        return self

    def find_all(self, key):
        if key is None:
            raise KeyError("key must not be empty")
        ret_val = set()
        if key.startswith('regex:'):
            regc = re.compile(key[6:], re.I|re.S)
            for k in self.__store:
                match = regc.match(k)
                if not match is None:
                    ret_val.add(self.__store[k])
        elif key in ['*', '.*', 'all']:
            for k in self.__store:
                ret_val.add(self.__store[k])
        elif key in self:
            ret_val.add(self[key])
        return list(ret_val)

    def __repr__(self):
        return "<Metadata: %s>"%str(json.dumps(self.__store, indent=4, cls=GenericJSONEncoder))

    @property
    def __json__(self):
        ''' make Metadata json serializable '''
        return self.__config

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
