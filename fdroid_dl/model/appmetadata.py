#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import collections
import copy
import json
from ..json import GenericJSONEncoder


logger = logging.getLogger('model.AppMetadata')
class AppMetadata(collections.MutableMapping):
    def __init__(self, appid, cfg={}, json={}, default_locale='en-US'):
        if appid is None: raise KeyError("no appid defined")
        self.__id = appid
        self.__cfg = cfg
        if not json is None: self.__store = self.__merge(copy.deepcopy(cfg),copy.deepcopy(json))
        else: self.__store = copy.deepcopy(cfg)
        self.__default_locale = default_locale

    def __merge(self,source,destination):
        for key, value in source.items():
            if isinstance(value, dict):
                node = destination.setdefault(key, {})
                self.__merge(value, node)
            else:
                destination[key] = value
        return destination

    @property
    def id(self):
        return str(self.__id)

    @property
    def appid(self):
        return str(self.__id)

    def merge(self,appmetadata):
        ''' used for adding addition data from e.g. index '''
        if not isinstance(appmetadata,AppMetadata) and not isinstance(appmetadata,dict):
            raise NotImplementedError("I can only merge two instances of AppMetadata at the moment")
        self.__store = self.__merge(self.__store,copy.deepcopy(appmetadata))
        return self

    def update(self,appmetadata):
        ''' apply manual changes and save tose in config '''
        if not isinstance(appmetadata,AppMetadata) and not isinstance(appmetadata,dict):
            raise NotImplementedError("I can only merge two instances of AppMetadata at the moment")
        self.__store = self.__merge(copy.deepcopy(appmetadata),self.__store)
        self.__cfg = self.__merge(copy.deepcopy(appmetadata),self.__cfg)
        return self

    def localized(self,locale=None):
        return self.__store.get('localized',{}).get(locale,{})

    def full_description(self,locale=None):
        return self.localized(locale).get('description',None)

    def short_description(self,locale=None):
        return self.localized(locale).get('summary',None)

    def title(self,locale=None):
        return self.localized(locale).get('name',None)

    def featureGraphic(self,locale=None):
        return self.localized(locale).get('featureGraphic',None)

    def icon(self,locale=None):
        return self.localized(locale).get('icon',None)

    def promoGraphic(self,locale=None):
        return self.localized(locale).get('promoGraphic',None)

    def tvBanner(self,locale=None):
        return self.localized(locale).get('tvBanner',None)

    def phoneScreenshots(self,locale=None):
        return self.localized(locale).get('phoneScreenshots',[])

    def sevenInchScreenshots(self,locale=None):
        return self.localized(locale).get('sevenInchScreenshots',[])

    def tenInchScreenshots(self,locale=None):
        return self.localized(locale).get('tenInchScreenshots',[])

    def tvScreenshots(self,locale=None):
        return self.localized(locale).get('tvScreenshots',[])

    def wearScreenshots(self,locale=None):
        return self.localized(locale).get('wearScreenshots',[])

    @property
    def locales(self):
        if 'localized' in self:
            return list(self['localized'].keys())
        return []

    def __repr__(self):
        return "<AppMetadata: %s>"%str(json.dumps(self.__store, indent=4, cls=GenericJSONEncoder))

    @property
    def __json__(self):
        ''' make Metadata json serializable '''
        return self.__cfg

    #######################
    # implement hash
    #######################
    def __hash__(self):
        return self.__id.__hash__()

    #######################
    # implement "dict"
    #######################
    def __getitem__(self, key):
        return self.__store[key]
    def __setitem__(self, key, value):
        self.__cfg[key] = value
        self.__store[key] = value
    def __delitem__(self, key):
        if key in self.__cfg: del self.__cfg[key]
        del self.__store[key]
    def __iter__(self):
        return iter(self.__store)
    def __len__(self):
        return len(self.__store)
