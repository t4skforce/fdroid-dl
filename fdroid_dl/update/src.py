#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging


LOGGER = logging.getLogger('update.SrcUpdate')
class SrcUpdate(object):
    def __init__(self, config, download_timeout=600, max_workers=10):
        self.__config = config
        self.__download_timeout = download_timeout
        self.__max_workers = max_workers

    def update(self):
        pass
