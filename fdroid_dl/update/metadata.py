#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import time
from datetime import timedelta
import os.path
import yaml
from .selector import Selector
from ..download import FuturesSessionVerifiedDownload
from urllib.parse import urlparse
import requests

logger = logging.getLogger('update.MetadataUpdate')
class MetadataUpdate(Selector):
    def __init__(self,config,download_timeout=600,max_workers=10):
        super(MetadataUpdate,self).__init__(config)
        self.__config = config
        self.__download_timeout = download_timeout
        self.__max_workers = max_workers
        self.__loaded = False
        self.__loadAll()

    def __loadAll(self):
        if not self.__is_loaded():
            self.__config.metadata.loadAll()
            self.__loaded = True

    def __is_loaded(self):
        return self.__loaded == True

    def _setyamlattr(sefl,yaml_key,json_key,yaml_data,app_meta):
        value = app_meta.get(json_key)
        if not value is None:
            yaml_data[yaml_key]=value

    def updateYAML(self):
        meta = self.__config.metadata
        logger.info("UPDATING YAML metadata")
        start = time.time()
        cnt = 0
        for repo,appid in self.allApps():
            try:
                app_meta = meta[appid]
                yaml_file = os.path.join(self.__config.metadata_dir,appid+'.yml')
                yaml_data = {}
                if os.path.exists(yaml_file):
                    with open(yaml_file, 'r') as yfl:
                        yaml_data = yaml.load(yfl)
                    if yaml_data is None:
                        yaml_data = {}
                self._setyamlattr('Categories','categories',yaml_data,app_meta)
                self._setyamlattr('AuthorName','authorName',yaml_data,app_meta)
                self._setyamlattr('AuthorEmail','authorEmail',yaml_data,app_meta)
                self._setyamlattr('License','license',yaml_data,app_meta)
                #self._setyamlattr('Name','name',yaml_data,app_meta)
                self._setyamlattr('WebSite','webSite',yaml_data,app_meta)
                self._setyamlattr('SourceCode','sourceCode',yaml_data,app_meta)
                self._setyamlattr('IssueTracker','issueTracker',yaml_data,app_meta)
                self._setyamlattr('Changelog','changelog',yaml_data,app_meta)
                self._setyamlattr('Donate','donate',yaml_data,app_meta)
                self._setyamlattr('FlattrID','flattr',yaml_data,app_meta)
                self._setyamlattr('LiberapayID','liberapay',yaml_data,app_meta)
                self._setyamlattr('Bitcoin','bitcoin',yaml_data,app_meta)
                self._setyamlattr('Litecoin','litecoin',yaml_data,app_meta)
                self._setyamlattr('AntiFeatures','antiFeatures',yaml_data,app_meta)
                with open(yaml_file,'w') as stream:
                    yaml.dump(yaml_data,stream,default_flow_style=False)
                cnt+=1
            except Exception as e:
                if logging.getLogger().isEnabledFor(logging.DEBUG): logger.exception()
                else: logger.warn(str(e.message) if hasattr(e,'message') else str(e))
        elapsed = time.time() - start
        logger.info("UPDATED YAML metadata, %s files (%s)"%(cnt,timedelta(seconds=elapsed)))

    def __write_text(self,text,filename,foldername):
        if not text is None:
            text = str(text)
            if not os.path.exists(foldername):
                os.makedirs(foldername)
            with open(os.path.join(foldername,filename), "w") as text_file:
                text_file.write(text)

    def __download_image(self,url,filename,session):
        if not url is None:
            session.download(url,filename,timeout=self.__download_timeout)

    def __download_images(self,urls,foldername,session):
        for url in urls:
            filename = os.path.basename(urlparse(url).path)
            filename = os.path.join(foldername,filename)
            self.__download_image(url,filename,session)

    def updateAssets(self):
        meta = self.__config.metadata
        logger.info("UPDATING Assets metadata")
        start = time.time()
        cnt = 0
        ecnt = 0
        with FuturesSessionVerifiedDownload(max_workers=self.__max_workers) as session:
            for repo,appid in self.allApps(session=session):
                try:
                    loc_appid = os.path.join(self.__config.metadata_dir,appid)
                    app_meta = meta[appid]
                    for locale in app_meta.locales:
                        loc_path = os.path.join(loc_appid,locale)
                        imags_path = os.path.join(loc_path,'images')
                        # TODO: chech if we need to download really all images & clean folder before/after?
                        self.__write_text(app_meta.full_description(locale),'full_description.txt',loc_path)
                        self.__write_text(app_meta.short_description(locale),'short_description.txt',loc_path)
                        self.__write_text(app_meta.title(locale),'title.txt',loc_path)

                        self.__download_image(app_meta.icon(locale),os.path.join(imags_path,'icon.png'),session)
                        self.__download_image(app_meta.featureGraphic(locale),os.path.join(imags_path,'featureGraphic.png'),session)
                        self.__download_image(app_meta.promoGraphic(locale),os.path.join(imags_path,'promoGraphic.png'),session)
                        self.__download_image(app_meta.tvBanner(locale),os.path.join(imags_path,'tvBanner.png'),session)

                        self.__download_images(app_meta.phoneScreenshots(locale),os.path.join(loc_path,'phoneScreenshots'),session)
                        self.__download_images(app_meta.sevenInchScreenshots(locale),os.path.join(loc_path,'sevenInchScreenshots'),session)
                        self.__download_images(app_meta.tenInchScreenshots(locale),os.path.join(loc_path,'tenInchScreenshots'),session)
                        self.__download_images(app_meta.tvScreenshots(locale),os.path.join(loc_path,'tvScreenshots'),session)
                        self.__download_images(app_meta.wearScreenshots(locale),os.path.join(loc_path,'wearScreenshots'),session)
                except Exception as e:
                    logger.exception("Error processing Asset download for",appid)
            for ok,filename,bytes,hbytes,elapsed in session.completed():
                if ok: cnt+=1
                else: ecnt+=1
        elapsed = time.time() - start
        logger.info("UPDATED Assets metadata, %s files, %s errors (%s)"%(cnt,ecnt,timedelta(seconds=elapsed)))
