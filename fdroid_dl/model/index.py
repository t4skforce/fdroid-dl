#!/usr/bin/env python3
# -*- coding: utf-8 -*-

try:
    from collections.abc import MutableMapping
except ImportError:
    from collections import MutableMapping
import re
import json
import xml.etree.ElementTree as ET
from time import mktime, strptime
import logging
try:
    from urllib.parse import urljoin
except ImportError:
    from urlparse import urljoin
from tempfile import NamedTemporaryFile
import shutil
from ..json import GenericJSONEncoder


LOGGER = logging.getLogger('model.Index')
class Index(MutableMapping):
    """
    Main Class responsible for handling the f-droid's index.xml and
    index-v1.json files.
    """

    def __init__(self, key=None, filename=None, format='json', default_locale='en-US', store=dict()):
        self.__key = key
        self.__filename = filename
        self.__format = format
        self.__default_locale = default_locale
        self.__store = store

    @classmethod
    def from_json(cls, source, **kwargs):
        if not hasattr(source, "read"):
            source = open(source, "r")
        kwargs['format'] = 'json'
        kwargs['filename'] = source.name
        return cls(**kwargs).load(source)

    @classmethod
    def from_xml(cls, source, **kwargs):
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

    def find_appids(self, key):
        if key is None:
            raise KeyError("key must not be empty")
        ret_val = set()
        if key.startswith('regex:'):
            regexc = re.compile(key[6:], re.I | re.S)
            for app in self.__store['apps']:
                match = regexc.match(app['packageName'])
                if not match is None:
                    ret_val.add(app['packageName'])
        elif key in ['*', '.*', 'all']:
            for app in self.__store['apps']:
                ret_val.add(app['packageName'])
        else:
            for app in self.__store['apps']:
                if app['packageName'] == key:
                    ret_val.add(app['packageName'])
        return list(ret_val)

    def defaultnum(self, value):
        if value.isnumeric():
            return int(value)
        return value

    def custom_func(self, xpath):
        if not xpath is None:
            regexc = re.compile(r'(.*?):(.*)$', re.I | re.S)
            match = regexc.match(xpath)
            if not match is None:
                return (match.group(1), match.group(2))
            return (xpath, None)
        return (None, None)

    def run_custom_func(self, method, value):
        if method is None or value is None:
            return None
        try:
            return eval(method, {'mktime': mktime, 'strptime': strptime}, {'value': value})
        except:
            LOGGER.exception("error in eval(%s)", method)

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
            regexc = re.compile(r'^.*?\[@([^\]]+)\]$')
            match = regexc.match(xpath)
            if not match is None:
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
        ret_val = []
        regexc = re.compile(r'^.*?\[@([^\]]+)\]$')
        match = regexc.match(xpath)
        if not match is None:
            attr_name = match.group(1)
            matches = root.findall(xpath)
            if not matches is None:
                for match in matches:
                    value = match.get(attr_name, None)
                    if not value is None:
                        ret_val.append(self.defaultnum(value.strip()))
        else:
            matches = root.findall(xpath)
            if not matches is None:
                for match in matches:
                    value = self.xmltextval(match)
                    if not value is None:
                        ret_val.append(value)
        return ret_val

    def convert(self, root):
        self.__store = {}
        store = self.__store
        repo = root.find('repo')
        if not repo is None:
            srepo = store['repo'] = {}
            self.xmlattr(srepo, root, 'timestamp', './repo[@timestamp]')
            self.xmlattr(srepo, root, 'version', './repo[@version]')
            self.xmlattr(srepo, root, 'maxage', './repo[@maxage]')
            self.xmlattr(srepo, root, 'name', './repo[@name]')
            self.xmlattr(srepo, root, 'icon', './repo[@icon]')
            self.xmlattr(srepo, root, 'url', './repo[@address]')
            self.xmltext(srepo, root, 'description', './description')
            srepo['mirrors'] = self.xmllist(repo, './mirror')
        requ = store['requests'] = {}
        requ['install'] = self.xmllist(root, './install[@packageName]')
        requ['uninstall'] = self.xmllist(root, './uninstall[@packageName]')
        apps = store['apps'] = []
        pkgs = store['packages'] = {}
        applications = root.findall('application[@id]')
        for xmlapp in applications:
            app_val = {}
            self.xmltext(app_val, xmlapp, 'authorEmail', './email')
            self.xmltext(app_val, xmlapp, 'authorName', './author')
            self.xmltext(app_val, xmlapp, 'authorWebSite', './web')
            self.xmltext(app_val, xmlapp, 'bitcoin', './bitcoin')
            self.xmltext(app_val, xmlapp, 'donate', './donate')
            self.xmltext(app_val, xmlapp, 'flattr', './flattr')
            self.xmltext(app_val, xmlapp, 'liberapay', './liberapay')
            self.xmltext(app_val, xmlapp, 'litecoin', './litecoin')
            cat = self.xmltextval(xmlapp, 'categories')
            if not cat is None and len(cat) > 0:
                app_val['categories'] = cat.split(',')
            afaet = self.xmltextval(xmlapp, 'antiFeatures')
            if not afaet is None and len(afaet) > 0:
                app_val['antiFeatures'] = afaet.split(',')
            self.xmltext(app_val, xmlapp, 'suggestedVersionName',
                         './marketversion')
            self.xmltext(app_val, xmlapp, 'suggestedVersionCode',
                         './marketvercode')
            self.xmltext(app_val, xmlapp, 'issueTracker', './tracker')
            self.xmltext(app_val, xmlapp, 'changelog', './changelog')
            self.xmltext(app_val, xmlapp, 'license', './license')
            self.xmltext(app_val, xmlapp, 'name', './name')
            self.xmltext(app_val, xmlapp, 'sourceCode', './source')
            self.xmltext(app_val, xmlapp, 'webSite', './web')
            self.xmltext(app_val, xmlapp, 'added',
                         './added:int(mktime(strptime(value, "%Y-%m-%d")))')
            self.xmltext(app_val, xmlapp, 'icon', './icon')
            self.xmltext(app_val, xmlapp, 'packageName', './id')
            self.xmltext(app_val, xmlapp, 'lastUpdated',
                         './lastupdated:int(mktime(strptime(value, "%Y-%m-%d")))')
            loc = app_val['localized'] = {}
            dloc = loc[self.default_locale] = {}
            self.xmltext(dloc, xmlapp, 'description', './desc')
            self.xmltext(dloc, xmlapp, 'summary', './summary')

            app_id = self.xmltextval(xmlapp, './id')
            if not app_id is None:
                pkg = pkgs[app_id] = []
                packages = xmlapp.findall('./package')
                for xmlpkg in packages:
                    pkg_val = {}
                    self.xmltext(
                        pkg_val, xmlpkg, 'added', './added:int(mktime(strptime(value, "%Y-%m-%d")))')
                    self.xmltext(pkg_val, xmlpkg, 'apkName', './apkname')
                    self.xmltext(pkg_val, xmlpkg, 'hash', './hash')
                    self.xmlattr(pkg_val, xmlpkg, 'hashType', './hash[@type]')
                    self.xmltext(pkg_val, xmlpkg, 'minSdkVersion', './sdkver')
                    self.xmltext(pkg_val, xmlpkg, 'targetSdkVersion',
                                 './targetSdkVersion')
                    pkg_val['packageName'] = app_id
                    self.xmltext(pkg_val, xmlpkg, 'sig', './sig')
                    self.xmltext(pkg_val, xmlpkg, 'versionName', './version')
                    self.xmltext(pkg_val, xmlpkg, 'versionCode',
                                 './versioncode')
                    self.xmltext(pkg_val, xmlpkg, 'size', './size')
                    perm = xmlpkg.find('permissions')
                    if not perm is None:
                        user_permission = pkg_val['uses-permission'] = []
                        user_permission_split = perm.text.split(",")
                        for user_permission_str in user_permission_split:
                            user_permission.append(['android.permission.'+user_permission_str.strip(), None])
                    if len(pkg_val) > 0:
                        pkg.append(pkg_val)
            if len(app_val) > 1:
                apps.append(app_val)

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
