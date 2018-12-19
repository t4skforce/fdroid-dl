#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import time
import os.path
import time
from datetime import timedelta
from urllib.parse import urlparse
from .selector import Selector
from ..download import FuturesSessionVerifiedDownload, FuturesSessionFlex

logger = logging.getLogger('update.ApkUpdate')
class ApkUpdate(Selector):
    def __init__(self,config,download_timeout=600,max_workers=10):
        super(ApkUpdate,self).__init__(config)
        self.__config = config
        self.__download_timeout = download_timeout
        self.__max_workers = max_workers

    def allPackage(self,session=None):
        downloads = {}
        logging.info("collecting apps to download")
        start = time.time()
        apkcnt = 0
        # search pkgs
        for repo,appid in self.allApps(dupes=True):
            self.applySessionSettings(repo, session)
            packages = repo.index.get('packages',{}).get(appid,[])
            if not appid in downloads: downloads[appid]=[]
            for pkg in packages:
                if not pkg.get('apkName') is None and not pkg.get('hash') is None and not pkg.get('hashType') is None:
                    downloads[appid].append(pkg)
                    apkcnt += 1
        elapsed = time.time() - start
        logging.info("found (%s) apk files to download (%s)"%(apkcnt,timedelta(seconds=elapsed)))

        for appid in downloads.keys():
            # sort newest first
            packages = sorted(downloads[appid], key=lambda e:e.get('versionCode',0), reverse=True)
            for idx,pkg in enumerate(packages):
                if idx >= self.__config.apk_versions: break # only download number of confgured files
                url = pkg.get('apkName')
                filename = os.path.basename(str(urlparse(url).path))
                filepath = os.path.join(self.__config.repo_dir,filename)
                yield (url, filepath, pkg.get('hash'), pkg.get('hashType'))

    def update(self):
        meta = self.__config.metadata
        logger.info("UPDATING apk files")
        start = time.time()
        cnt = 0
        ecnt = 0
        with FuturesSessionVerifiedDownload(max_workers=self.__max_workers) as session:
            for url, filename, hash, hashType in self.allPackage(session=session):
                if os.path.exists(filename):
                    start2 = time.time()
                    if FuturesSessionVerifiedDownload.verify(filename,hashType,hash):
                        elapsed = time.time() - start2
                        logger.info("hash verified %s [%s] (%s) ✔"%(os.path.basename(filename),timedelta(seconds=elapsed),FuturesSessionFlex.h_size(os.stat(filename).st_size)))
                    else:
                        session.download(url,filename,timeout=self.__download_timeout,hash=hash,hashType=hashType)
                else:
                    session.download(url,filename,timeout=self.__download_timeout,hash=hash,hashType=hashType)

            dlsum = 0
            for ok,filename,bytes,hbytes,elapsed in session.completed():
                if ok:
                    cnt += 1
                    dlsum += bytes
                else:
                    ecnt += 1
        elapsed = time.time() - start
        logger.info("UPDATED apk files, files(%s) errors(%s) [%s] (%s)"%(cnt,ecnt,FuturesSessionFlex.h_size(dlsum),timedelta(seconds=elapsed)))
