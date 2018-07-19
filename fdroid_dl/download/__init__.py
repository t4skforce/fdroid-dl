#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from .futuressession import FuturesSessionFlex
from .verifieddownload import FuturesSessionVerifiedDownload

# disable insecure warning
# https://stackoverflow.com/questions/27981545/suppress-insecurerequestwarning-unverified-https-request-is-being-made-in-pytho
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

__all__ = ['FuturesSessionFlex','FuturesSessionVerifiedDownload']
