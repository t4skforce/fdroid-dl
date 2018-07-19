#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from json import JSONEncoder


logger = logging.getLogger('json.GenericJSONEncoder')
class GenericJSONEncoder(JSONEncoder):
    ''' custom encoder so we can serialize Config to json '''
    def default(self, obj):
        if hasattr(obj, '__json__'):
            return getattr(obj, '__json__')
        return JSONEncoder.default(self,obj)
