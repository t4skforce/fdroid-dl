#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import os.path
from concurrent.futures import as_completed
import requests
from ..download import FuturesSessionFlex
from ..processor import IndexFileProcessor


LOGGER = logging.getLogger('update.IndexUpdate')
class IndexUpdate(object):
    def __init__(self, config, head_timeout=10, index_timeout=60, max_workers=10):
        self.config = config
        self.head_timeout = head_timeout
        self.index_timeout = index_timeout
        self.max_workers = max_workers

    def required(self, repos, timeout=60):
        # try new index
        head_futures = self.__future(repos=repos, timeout=timeout)
        # process result
        (new_index, notfound) = self.__head_response(head_futures)
        # retry old index
        head_futures = self.__future(repos=notfound, attr='url_index', timeout=timeout)
        # process result
        (old_index, notfound) = self.__head_response(head_futures)
        # new_index[] needs to be fetched with index-v1.jar
        # old_index[] needs to be fetched with index.jar
        return (new_index, old_index)

    def download(self, new_index, old_index, timeout=60):
        if new_index is None:
            raise AttributeError('new_index missing')
        if old_index is None:
            raise AttributeError('old_index missing')
        new_futures = self.__future(repos=new_index, timeout=timeout, http_method=FuturesSessionFlex.get, hooks={'response':[FuturesSessionFlex.extract_jar]}, stream=True)
        old_futures = self.__future(repos=old_index, timeout=timeout, http_method=FuturesSessionFlex.get, hooks={'response':[FuturesSessionFlex.extract_jar]}, attr='url_index', stream=True)
        self.__download_response(new_futures)
        self.__download_response(old_futures)

    def __future(self, repos=None, attr='url_index_v1', http_method=FuturesSessionFlex.head, hooks=None, timeout=60, **kwargs):
        if repos is None:
            raise AttributeError('repos missing %s'%repos)
        if hooks is None:
            hooks = {'response': [FuturesSessionFlex.add_hash]}
        futures = []
        with FuturesSessionFlex(max_workers=self.max_workers) as session:
            for repo in repos:
                if not repo.auth is None or repo.verify is False:
                    thread_session = requests.Session()
                    thread_session.auth = repo.auth
                    thread_session.verify = repo.verify
                    session.map(getattr(repo, attr), thread_session)
                request = http_method(session, getattr(repo, attr), hooks=hooks, timeout=timeout, **kwargs)
                request.repo = repo # pass repo ref to future processing
                futures.append(request)
        return futures

    def __as_completed(self, futures):
        for future in as_completed(futures):
            repo = future.repo
            try:
                response = future.result()
                response.raise_for_status()
                yield (repo, response, True)
            except requests.exceptions.HTTPError as ex:
                if ex.response.status_code == 404: # try old index file
                    if logging.getLogger().isEnabledFor(logging.DEBUG):
                        LOGGER.exception()
                    else:
                        LOGGER.warning(str(ex))
                    yield (repo, response, False)
                else:
                    repo['error'] = {
                        'code': ex.response.status_code if isinstance(ex, requests.exceptions.HTTPError) else 600,
                        'msg':str(ex)
                    }
                    LOGGER.exception()

    def __head_response(self, futures):
        success = []
        notfound = []
        for repo, response, okheader in self.__as_completed(futures):
            if okheader:
                # check cache
                LOGGER.info("HEAD %s (%s) ", response.url, response.elapsed)
                if not os.path.exists(repo.filename) or repo.hash != response.hash:
                    if 'error' in repo:
                        del repo['error']
                    repo['hash'] = response.hash
                    success.append(repo)
                    if not os.path.exists(repo.filename):
                        LOGGER.warning("CACHE - (miss) - %s.cache file not found!", repo.id)
                    else:
                        LOGGER.info("CACHE - (miss) - %s - %s)", repo.key, response.hash)
                else:
                    # skip do nothing for cache hits
                    LOGGER.info("CACHE - (hit) - %s - %s)", repo.key, response.hash)
            else:
                notfound.append(repo)
        return (success, notfound)

    def __download_response(self, futures):
        with IndexFileProcessor(max_workers=self.max_workers) as ifp:
            for repo, response, success in self.__as_completed(futures):
                if response.ok:
                    LOGGER.info("DOWNLOADED %s [%s] (%s) ", response.url, response.elapsed, response.h_size)
                    ifp.process(response.index, repo, repo.url, response.h_size)
            for future in ifp.completed():
                (index, elapsed, url, h_size) = future.result()
                repo_name = index.get('repo', {}).get('name')
                LOGGER.info("UPDATED %s - %s [%s] (%s) ", repo_name, url, elapsed, h_size)
