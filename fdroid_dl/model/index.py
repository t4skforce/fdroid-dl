#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import collections
import os
import re
import json
import xml.etree.ElementTree as ET
from time import mktime, strptime
import logging
from urllib.parse import urljoin
from ..json import GenericJSONEncoder
from tempfile import NamedTemporaryFile
import shutil

logger = logging.getLogger('model.Index')


class Index(collections.MutableMapping):
    """
    Main Class responsible for handling the f-droid's index.xml and
    index-v1.json files.
    """

    def __init__(self, key=None, filename=None, format='json', default_locale='en-US', store={}):
        self.__key = key
        self.__filename = filename
        self.__format = format
        self.__default_locale = default_locale
        self.__store = store

    @classmethod
    def fromJSON(cls, source, **kwargs):
        if not hasattr(source, "read"):
            source = open(source, "r")
        kwargs['format'] = 'json'
        kwargs['filename'] = source.name
        return cls(**kwargs).load(source)

    @classmethod
    def fromXML(cls, source, **kwargs):
        if not hasattr(source, "read"):
            source = open(source, "r")
        kwargs['format'] = 'xml'
        kwargs['filename'] = source.name
        return cls(**kwargs).load(source)

    @property
    def filename(self):
        return str(self.__filename)

    @property
    def key(self):
        return str(self.__key)

    @property
    def repo_url(self):
        return str(self.__key)

    @property
    def format(self):
        return str(self.__format)

    @property
    def default_locale(self):
        return str(self.__default_locale)

    def findAppIds(self, key):
        if key is None:
            raise KeyError("key must not be empty")
        retVal = set()
        if key.startswith('regex:'):
            c = re.compile(key[6:], re.I | re.S)
            for app in self.__store['apps']:
                m = c.match(app['packageName'])
                if not m is None:
                    retVal.add(app['packageName'])
        elif key in ['*', '.*', 'all']:
            for app in self.__store['apps']:
                retVal.add(app['packageName'])
        else:
            for app in self.__store['apps']:
                if app == key:
                    retVal.add(app['packageName'])
        return list(retVal)

    def defaultnum(self, value):
        if value.isnumeric():
            return int(value)
        return value

    def custom_func(self, xpath):
        if not xpath is None:
            p = re.compile('(.*?):(.*)$', re.I | re.S)
            m = p.match(xpath)
            if not m is None:
                return (m.group(1), m.group(2))
            return (xpath, None)
        return (None, None)

    def run_custom_func(self, method, value):
        if method is None or value is None:
            return None
        try:
            return eval(method, {'mktime': mktime, 'strptime': strptime}, {'value': value})
        except:
            logger.exception("error in eval(%s)", method)

    def xmlattr(self, node, xml_node, key=None, xpath=None):
        if xpath is None and key is None:
            return None
        if xpath is None and not key is None:
            xpath = key
        value = self.xmlattrval(xml_node, xpath)
        if not value is None:
            if not key is None:
                node[key] = value
            else:
                node = value

    def xmlattrval(self, xml_node, xpath):
        if not xml_node is None:
            p = re.compile('^.*?\[@([^\]]+)\]$')
            m = p.match(xpath)
            if not m is None:
                attr_name = m.group(1)
            else:
                attr_name = xpath
            (xpath, func) = self.custom_func(xpath)
            if not xpath is None:
                xml_node = xml_node.find(xpath)
            if not xml_node is None:
                value = xml_node.get(attr_name, None)
                #print(xml_node,attr_name,value)
                if not value is None:
                    if not func is None:
                        return self.run_custom_func(func, self.defaultnum(value.strip()))
                    else:
                        return self.defaultnum(value.strip())
        return None

    def xmltext(self, node, xml_node, key=None, xpath=None):
        if xpath is None and key is None:
            return None
        if xpath is None and not key is None:
            xpath = key
        value = self.xmltextval(xml_node, xpath)
        if not value is None:
            if not key is None:
                node[key] = value
            else:
                node = value

    def xmltextval(self, xml_node, xpath=None):
        (xpath, func) = self.custom_func(xpath)
        if not xpath is None:
            xml_node = xml_node.find(xpath)
        if not xml_node is None:
            value = xml_node.text
            if not value is None:
                if not func is None:
                    return self.run_custom_func(func, self.defaultnum(value.strip()))
                else:
                    return self.defaultnum(value.strip())

    def xmllist(self, root, xpath):
        retVal = []
        p = re.compile('^.*?\[@([^\]]+)\]$')
        m = p.match(xpath)
        if not m is None:
            attr_name = m.group(1)
            matches = root.findall(xpath)
            if not matches is None:
                for match in matches:
                    value = match.get(attr_name, None)
                    if not value is None:
                        retVal.append(self.defaultnum(value.strip()))
        else:
            matches = root.findall(xpath)
            if not matches is None:
                for match in matches:
                    value = self.xmltextval(match)
                    if not value is None:
                        retVal.append(value)
        return retVal

    def convert(self, root):
        self.__store = {}
        store = self.__store
        repo = root.find('repo')
        if not repo is None:
            sr = store['repo'] = {}
            self.xmlattr(sr, root, 'timestamp', './repo[@timestamp]')
            self.xmlattr(sr, root, 'version', './repo[@version]')
            self.xmlattr(sr, root, 'maxage', './repo[@maxage]')
            self.xmlattr(sr, root, 'name', './repo[@name]')
            self.xmlattr(sr, root, 'icon', './repo[@icon]')
            self.xmlattr(sr, root, 'url', './repo[@address]')
            self.xmltext(sr, root, 'description', './description')
            sr['mirrors'] = self.xmllist(repo, './mirror')
        rq = store['requests'] = {}
        rq['install'] = self.xmllist(root, './install[@packageName]')
        rq['uninstall'] = self.xmllist(root, './uninstall[@packageName]')
        apps = store['apps'] = []
        pkgs = store['packages'] = {}
        applications = root.findall('application[@id]')
        for xmlapp in applications:
            appVal = {}
            self.xmltext(appVal, xmlapp, 'authorEmail', './email')
            self.xmltext(appVal, xmlapp, 'authorName', './author')
            self.xmltext(appVal, xmlapp, 'authorWebSite', './web')
            self.xmltext(appVal, xmlapp, 'bitcoin', './bitcoin')
            self.xmltext(appVal, xmlapp, 'donate', './donate')
            self.xmltext(appVal, xmlapp, 'flattr', './flattr')
            self.xmltext(appVal, xmlapp, 'liberapay', './liberapay')
            self.xmltext(appVal, xmlapp, 'litecoin', './litecoin')
            cat = self.xmltextval(xmlapp, 'categories')
            if not cat is None and len(cat) > 0:
                appVal['categories'] = cat.split(',')
            afaet = self.xmltextval(xmlapp, 'antiFeatures')
            if not afaet is None and len(afaet) > 0:
                appVal['antiFeatures'] = afaet.split(',')
            self.xmltext(appVal, xmlapp, 'suggestedVersionName',
                         './marketversion')
            self.xmltext(appVal, xmlapp, 'suggestedVersionCode',
                         './marketvercode')
            self.xmltext(appVal, xmlapp, 'issueTracker', './tracker')
            self.xmltext(appVal, xmlapp, 'changelog', './changelog')
            self.xmltext(appVal, xmlapp, 'license', './license')
            self.xmltext(appVal, xmlapp, 'name', './name')
            self.xmltext(appVal, xmlapp, 'sourceCode', './source')
            self.xmltext(appVal, xmlapp, 'webSite', './web')
            self.xmltext(appVal, xmlapp, 'added',
                         './added:int(mktime(strptime(value, "%Y-%m-%d")))')
            self.xmltext(appVal, xmlapp, 'icon', './icon')
            self.xmltext(appVal, xmlapp, 'packageName', './id')
            self.xmltext(appVal, xmlapp, 'lastUpdated',
                         './lastupdated:int(mktime(strptime(value, "%Y-%m-%d")))')
            loc = appVal['localized'] = {}
            dloc = loc[self.default_locale] = {}
            self.xmltext(dloc, xmlapp, 'description', './desc')
            self.xmltext(dloc, xmlapp, 'summary', './summary')

            appId = self.xmltextval(xmlapp, './id')
            if not appId is None:
                pkg = pkgs[appId] = []
                packages = xmlapp.findall('./package')
                for xmlpkg in packages:
                    pkgVal = {}
                    self.xmltext(
                        pkgVal, xmlpkg, 'added', './added:int(mktime(strptime(value, "%Y-%m-%d")))')
                    self.xmltext(pkgVal, xmlpkg, 'apkName', './apkname')
                    self.xmltext(pkgVal, xmlpkg, 'hash', './hash')
                    self.xmlattr(pkgVal, xmlpkg, 'hashType', './hash[@type]')
                    self.xmltext(pkgVal, xmlpkg, 'minSdkVersion', './sdkver')
                    self.xmltext(pkgVal, xmlpkg, 'targetSdkVersion',
                                 './targetSdkVersion')
                    pkgVal['packageName'] = appId
                    self.xmltext(pkgVal, xmlpkg, 'sig', './sig')
                    self.xmltext(pkgVal, xmlpkg, 'versionName', './version')
                    self.xmltext(pkgVal, xmlpkg, 'versionCode',
                                 './versioncode')
                    self.xmltext(pkgVal, xmlpkg, 'size', './size')
                    perm = xmlpkg.find('permissions')
                    if not perm is None:
                        up = pkgVal['uses-permission'] = []
                        npstr = perm.text.split(",")
                        for ps in npstr:
                            up.append(['android.permission.'+ps.strip(), None])
                    if len(pkgVal) > 0:
                        pkg.append(pkgVal)
            if len(appVal) > 1:
                apps.append(appVal)

    def monkeypatch(self):
        ''' fixup metadata paths -> url '''
        if not '_monkeypatched' in self.__store:
            if self.__key is None:
                raise AttributeError('key not defined')
            self.__store['_monkeypatched'] = True
            if 'packages' in self.__store:
                for key in self.__store['packages']:
                    for pkg in self.__store['packages'][key]:
                        pkg['apkName'] = urljoin(self.__key, pkg['apkName'])
                        if not pkg.get('srcname') is None:
                            pkg['srcname'] = urljoin(
                                self.__key, pkg['srcname'])

            if 'apps' in self.__store:
                for app in self.__store['apps']:
                    if 'icon' in app:
                        app['icon'] = urljoin(self.__key, "icons/"+app['icon'])
                    locs = app.get('localized', {})
                    for k in locs.keys():
                        loc = locs[k]
                        if 'icon' in loc:
                            loc['icon'] = urljoin(
                                self.__key, app['packageName']+'/'+k+'/'+loc['icon'])
                        if 'featureGraphic' in loc:
                            loc['featureGraphic'] = urljoin(
                                self.__key, app['packageName']+'/'+k+'/'+loc['featureGraphic'])
                        if 'promoGraphic' in loc:
                            loc['promoGraphic'] = urljoin(
                                self.__key, app['packageName']+'/'+k+'/'+loc['promoGraphic'])
                        if 'tvBanner' in loc:
                            loc['tvBanner'] = urljoin(
                                self.__key, app['packageName']+'/'+k+'/'+loc['tvBanner'])
                        if 'phoneScreenshots' in loc:
                            loc['phoneScreenshots'] = [urljoin(
                                self.__key, app['packageName']+'/'+k+'/phoneScreenshots/'+value) for value in loc['phoneScreenshots']]
                        if 'sevenInchScreenshots' in loc:
                            loc['sevenInchScreenshots'] = [urljoin(
                                self.__key, app['packageName']+'/'+k+'/sevenInchScreenshots/'+value) for value in loc['sevenInchScreenshots']]
                        if 'tenInchScreenshots' in loc:
                            loc['tenInchScreenshots'] = [urljoin(
                                self.__key, app['packageName']+'/'+k+'/tenInchScreenshots/'+value) for value in loc['tenInchScreenshots']]
                        if 'tvScreenshots' in loc:
                            loc['tvScreenshots'] = [urljoin(
                                self.__key, app['packageName']+'/'+k+'/tvScreenshots/'+value) for value in loc['tvScreenshots']]
                        if 'wearScreenshots' in loc:
                            loc['wearScreenshots'] = [urljoin(
                                self.__key, app['packageName']+'/'+k+'/wearScreenshots/'+value) for value in loc['wearScreenshots']]
        return self

    def load(self, file, format=None):
        if not hasattr(file, 'read'):
            file = open(file, 'r')
        if not format is None:
            self.__format = format

        if self.__format == 'json':
            with file as idxfl:
                self.__store = json.load(idxfl)
        elif self.__format == 'xml':
            # we have no json verison we need som transformation to apply
            tree = ET.parse(file)
            file.close()
            root = tree.getroot()
            self.convert(root)
            self.__format = 'json'
        else:
            # try loading json anyway
            try:
                self.load(file, format='json')
            except:
                self.load(file, format='xml')
        return self

    def save(self, filename=None):
        if not filename is None:
            self.__filename = filename
        with NamedTemporaryFile(mode='w') as tmp:
            json.dump(self.__store, tmp, sort_keys=True,
                      indent=4, cls=GenericJSONEncoder)
            tmp.flush()
            shutil.copy(tmp.name, self.__filename)
        return self

    def __repr__(self):
        return "<Index: %s>" % str(json.dumps(self.__store, indent=4))

    @property
    def __json__(self):
        ''' make Index json serializable '''
        return self.__store
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
        self.load(self.__filename)
        return self

    def __exit__(self, type, value, traceback):
        self.save()
