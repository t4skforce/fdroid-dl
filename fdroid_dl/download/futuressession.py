#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from requests_futures.sessions import FuturesSession
import hashlib
import time
import copy
from datetime import timedelta
from zipfile import ZipFile
from tempfile import NamedTemporaryFile
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import os

logger = logging.getLogger('download.FuturesSessionFlex')
class FuturesSessionFlex(FuturesSession):
    BLOCKSIZE = 65536
    SUFFIXES = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']

    def __init__(self, max_workers=1, user_agent='Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)', *args, **kwargs):
        kwargs.update({'max_workers':max_workers})
        super(FuturesSessionFlex, self).__init__(*args, **kwargs)
        self.__sessions={}
        self.__sessions_keys=[]

        self.__fs_kwargs={}
        self.__fs_kwargs.update(kwargs)

        _adapter_kwargs = {'pool_connections': max_workers,'pool_maxsize': max_workers,'pool_block':True}
        self.mount('https://', HTTPAdapter(**_adapter_kwargs))
        self.mount('http://', HTTPAdapter(**_adapter_kwargs))
        if self.headers is None:
            self.headers={}
        self.headers.update({'User-Agent': user_agent})

    def map(self,pattern='http://',session=None):
        ''' if called with session None -> default session for ctor is used '''
        kwargs = copy.deepcopy(self.__fs_kwargs)
        kwargs['session']=session
        if not pattern in self.__sessions: self.__sessions_keys.append(pattern)
        self.__sessions[pattern]=FuturesSessionFlex(*(), **kwargs)
        self.__sessions_keys=sorted(self.__sessions_keys, key=len, reverse=True)

    def set_headers(self,headers):
        self.headers.update(headers)

    @staticmethod
    def h_size(nbytes):
        i = 0
        while nbytes >= 1024 and i < len(FuturesSessionFlex.SUFFIXES)-1:
            nbytes /= 1024.
            i += 1
        f = ('%.2f' % nbytes).rstrip('0').rstrip('.')
        return '%s %s' % (f, FuturesSessionFlex.SUFFIXES[i])

    @staticmethod
    def add_size(response, *args, **kwargs):
        if 'Content-Length' in response.headers:
            response.size=int(response.headers.get('Content-Length',0))
        else:
            logger.warn("Content-Length Header not provided by %s"%response.url)
            response.size=len(response.content)
        response.h_size=FuturesSessionFlex.h_size(response.size)
        return response

    @staticmethod
    def add_hash(response, *args, **kwargs):
        response.hash=None
        if response.ok:
            ts = str(time.time())
            cv = response.headers.get('Last-Modified',ts)+response.headers.get('ETag',ts)
            response.hash=hashlib.sha1(str(cv).encode('UTF-8')).hexdigest()
        return response

    @staticmethod
    def extract_jar(response, *args, **kwargs):
        if response.ok:
            start = time.time()
            response = FuturesSessionFlex.add_size(response, *args, **kwargs)
            response.index=NamedTemporaryFile()
            with NamedTemporaryFile() as f:
                for chunk in response.iter_content(chunk_size=FuturesSessionFlex.BLOCKSIZE):
                    if chunk: f.write(chunk)
                zip_file = ZipFile(f)
                idxfile = 'index-v1.json' if 'index-v1.json' in zip_file.namelist() else 'index.xml'
                with zip_file.open(idxfile) as file:
                    while True:
                        byte = file.read(FuturesSessionFlex.BLOCKSIZE)
                        if not byte: break
                        response.index.write(byte)
            logging.debug("%s - %s - (%s)"%(response.index.name,response.url,FuturesSessionFlex.h_size(os.stat(response.index.name).st_size)))
            elapsed = time.time() - start
            response.elapsed+=timedelta(seconds=elapsed)
        return response

    def __lookup_fs_session(self,url):
        # fast direct matches
        if url in self.__sessions:
            return self.__sessions[url]
        # slower pattern search depends on pattern count and size
        for k in self.__sessions_keys:
            if url.find(k) == 0:
                return self.__sessions[k]
        return None

    def request(self, *args, **kwargs):
        session = self.__lookup_fs_session(args[1])
        if not session is None:
            return session.request(*args, **kwargs)
        return super(FuturesSessionFlex, self).request(*args, **kwargs)

    def close(self):
        try:
            for key, session in self.__sessions.items():
                session.close()
        except Exception as e:
            logging.exception("Error closing sessions")
