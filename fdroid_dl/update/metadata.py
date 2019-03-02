#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import time
from datetime import timedelta
import os.path
try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse
import yaml
from .selector import Selector
from ..download import FuturesSessionVerifiedDownload


LOGGER = logging.getLogger('update.MetadataUpdate')
class MetadataUpdate(Selector):
    def __init__(self, config, download_timeout=600, max_workers=10):
        super(MetadataUpdate, self).__init__(config)
        self.__config = config
        self.__download_timeout = download_timeout
        self.__max_workers = max_workers
        self.__loaded = False
        self.__load_all()

    def __load_all(self):
        if not self.__is_loaded():
            self.__config.metadata.load_all()
            self.__loaded = True

    def __is_loaded(self):
        return self.__loaded is True

    @staticmethod
    def _setyamlattr(yaml_key, json_key, yaml_data, app_meta):
        value = app_meta.get(json_key)
        if not value is None:
            yaml_data[yaml_key] = value

    def update_yaml(self):
        meta = self.__config.metadata
        LOGGER.info("UPDATING YAML metadata")
        start = time.time()
        cnt = 0
        for repo, appid in self.all_apps():
            try:
                app_meta = meta[appid]
                yaml_file = os.path.join(self.__config.metadata_dir, appid+'.yml')
                yaml_data = {}
                if os.path.exists(yaml_file):
                    with open(yaml_file, 'r') as yfl:
                        yaml_data = yaml.load(yfl, Loader=yaml.SafeLoader)
                    if yaml_data is None:
                        yaml_data = {}
                MetadataUpdate._setyamlattr('Categories', 'categories', yaml_data, app_meta)
                MetadataUpdate._setyamlattr('AuthorName', 'authorName', yaml_data, app_meta)
                MetadataUpdate._setyamlattr('AuthorEmail', 'authorEmail', yaml_data, app_meta)
                MetadataUpdate._setyamlattr('License', 'license', yaml_data, app_meta)
                #self._setyamlattr('Name','name',yaml_data,app_meta)
                MetadataUpdate._setyamlattr('WebSite', 'webSite', yaml_data, app_meta)
                MetadataUpdate._setyamlattr('SourceCode', 'sourceCode', yaml_data, app_meta)
                MetadataUpdate._setyamlattr('IssueTracker', 'issueTracker', yaml_data, app_meta)
                MetadataUpdate._setyamlattr('Changelog', 'changelog', yaml_data, app_meta)
                MetadataUpdate._setyamlattr('Donate', 'donate', yaml_data, app_meta)
                MetadataUpdate._setyamlattr('FlattrID', 'flattr', yaml_data, app_meta)
                MetadataUpdate._setyamlattr('LiberapayID', 'liberapay', yaml_data, app_meta)
                MetadataUpdate._setyamlattr('Bitcoin', 'bitcoin', yaml_data, app_meta)
                MetadataUpdate._setyamlattr('Litecoin', 'litecoin', yaml_data, app_meta)
                MetadataUpdate._setyamlattr('AntiFeatures', 'antiFeatures', yaml_data, app_meta)
                with open(yaml_file, 'w') as stream:
                    yaml.safe_dump(yaml_data, stream, default_flow_style=False, encoding='utf-8', allow_unicode=True)
                cnt += 1
            except Exception as ex:
                if logging.getLogger().isEnabledFor(logging.DEBUG):
                    LOGGER.exception()
                else:
                    LOGGER.warning(str(ex))
        elapsed = time.time() - start
        LOGGER.info("UPDATED YAML metadata, %s files (%s)", cnt, timedelta(seconds=elapsed))

    @staticmethod
    def __write_text(text, filename, foldername):
        if not text is None:
            text = text.encode('utf-8')
            if not os.path.exists(foldername):
                os.makedirs(foldername)
            with open(os.path.join(foldername, filename), "w") as text_file:
                text_file.write(text)

    def __download_image(self, url, filename, session):
        if not url is None:
            session.download(url, filename, timeout=self.__download_timeout)

    def __download_images(self, urls, foldername, session):
        for url in urls:
            filename = os.path.basename(urlparse(url).path)
            filename = os.path.join(foldername, filename)
            self.__download_image(url, filename, session)

    def update_assets(self):
        meta = self.__config.metadata
        LOGGER.info("UPDATING Assets metadata")
        start = time.time()
        cnt = 0
        ecnt = 0
        with FuturesSessionVerifiedDownload(max_workers=self.__max_workers) as session:
            for repo, appid in self.all_apps(session=session):
                try:
                    loc_appid = os.path.join(self.__config.metadata_dir, appid)
                    app_meta = meta[appid]
                    for locale in app_meta.locales:
                        loc_path = os.path.join(loc_appid, locale)
                        imags_path = os.path.join(loc_path, 'images')
                        # TODO: chech if we need to download really all images & clean folder before/after?
                        MetadataUpdate.__write_text(app_meta.full_description(locale), 'full_description.txt', loc_path)
                        MetadataUpdate.__write_text(app_meta.short_description(locale), 'short_description.txt', loc_path)
                        MetadataUpdate.__write_text(app_meta.title(locale), 'title.txt', loc_path)

                        self.__download_image(app_meta.icon(locale), os.path.join(imags_path, 'icon.png'), session)
                        self.__download_image(app_meta.feature_graphic(locale), os.path.join(imags_path, 'featureGraphic.png'), session)
                        self.__download_image(app_meta.promo_graphic(locale), os.path.join(imags_path, 'promoGraphic.png'), session)
                        self.__download_image(app_meta.tv_banner(locale), os.path.join(imags_path, 'tvBanner.png'), session)

                        self.__download_images(app_meta.phone_screenshots(locale), os.path.join(loc_path, 'phoneScreenshots'), session)
                        self.__download_images(app_meta.seven_inch_screenshots(locale), os.path.join(loc_path, 'sevenInchScreenshots'), session)
                        self.__download_images(app_meta.ten_inch_screenshots(locale), os.path.join(loc_path, 'tenInchScreenshots'), session)
                        self.__download_images(app_meta.tv_screenshots(locale), os.path.join(loc_path, 'tvScreenshots'), session)
                        self.__download_images(app_meta.wear_screenshots(locale), os.path.join(loc_path, 'wearScreenshots'), session)
                except Exception:
                    LOGGER.exception("Error processing Asset download for %s", appid)
            for success, filename, bts, hbts, elapsed in session.completed():
                if success:
                    cnt += 1
                else:
                    ecnt += 1
        elapsed = time.time() - start
        LOGGER.info("UPDATED Assets metadata, %s files, %s errors (%s)", cnt, ecnt, timedelta(seconds=elapsed))
