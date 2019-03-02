#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import requests


LOGGER = logging.getLogger('update.Selector')
class Selector(object):
    def __init__(self, config):
        self.__config = config

    def __meta_repos(self):
        for repo in self.__config.repos:
            if not 'error' in repo: # ignore repos with download error
                yield repo

    def all_apps(self, dupes=False, session=None):
        yielded = set()
        for repo in self.__meta_repos():
            Selector.apply_session_settings(repo, session)
            for selector in repo.apps:
                if not repo.index is None:
                    for appid in repo.index.find_appids(selector):
                        if not appid in yielded or dupes:
                            yielded.add(appid)
                            yield (repo, appid)

    @staticmethod
    def apply_session_settings(repo, session):
        ''' apply security settings for basic auth and ssl verification '''
        if not session is None:
            if not repo.auth is None or repo.verify is False:
                thread_session = requests.Session()
                thread_session.auth = repo.auth
                thread_session.verify = repo.verify
                session.map(repo.url, thread_session)
