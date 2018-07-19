#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import requests


logger = logging.getLogger('update.Selector')
class Selector:
    def __init__(self,config):
        self.__config = config

    def __metaRepos(self):
        for repo in self.__config.repos:
            if not 'error' in repo: # ignore repos with download error
                yield repo

    def allApps(self,dupes=False,session=None):
        yielded = set()
        for repo in self.__metaRepos():
            self.applySessionSettings(repo, session)
            for selector in repo.apps:
                for appid in repo.index.findAppIds(selector):
                    if not yielded in yielded or dupes:
                        yielded.add(appid)
                        yield (repo,appid)

    def applySessionSettings(self, repo, session):
        ''' apply security settings for basic auth and ssl verification '''
        if not session is None:
            if not repo.auth is None or repo.verify == False:
                ts = requests.Session()
                ts.auth=repo.auth
                ts.verify=repo.verify
                session.map(repo.url,ts)
