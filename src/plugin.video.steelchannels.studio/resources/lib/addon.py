# -*- coding: utf-8 -*-

import json
import os

import xbmc
import xbmcaddon

KODISTUBS = False
try:
    KODISTUBS = xbmc.__kodistubs__
except:
    pass

USERAGENT = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'
ADDON = xbmcaddon.Addon()
ADDON_ID = ADDON.getAddonInfo('id')
ADDON_NAME = ADDON.getAddonInfo('name')
ADDON_VERSION = ADDON.getAddonInfo('version')
#ADDON_UUID = ADDON.getSetting('UUID')

FOLDER = ADDON.getSetting('path')
QUALITY = ADDON.getSetting('quality_default')

SERVICE_FREQUENCY = ADDON.getSetting('frequency')
PAUSE = ADDON.getSetting('pause')
TIMEOUT = ADDON.getSetting('timeout')

CINECALIDAD_SERIE_PAGE = ADDON.getSetting('serie_page')
CINECALIDAD_MOVIE_PAGE = ADDON.getSetting('movie_page')
CINECALIDAD_NUM_PAGE = ADDON.getSetting('num_page')

if KODISTUBS:
    with open(os.path.join('./', 'settings.json')) as f:
        settings = json.load(f)

    addon = settings['addon']
    ADDON_ID = addon['id']
    ADDON_NAME = addon['name']
    ADDON_VERSION = addon['version']
    #ADDON_UUID = addon['UUID']

    setting = settings['setting'][1]
    FOLDER = setting['path']
    QUALITY = setting['quality_default']

    SERVICE_FREQUENCY = setting['frequency']
    PAUSE = setting['pause']
    TIMEOUT = setting['timeout']

    CINECALIDAD_SERIE_PAGE = setting['serie_page']
    CINECALIDAD_MOVIE_PAGE = setting['movie_page']
    CINECALIDAD_NUM_PAGE = setting['num_page']


try:
    SERVICE_FREQUENCY = int(SERVICE_FREQUENCY)
except:
    SERVICE_FREQUENCY = 6

try:
    PAUSE = int(PAUSE) / 10
except:
    PAUSE = 0.5

try:
    TIMEOUT = int(TIMEOUT)
except:
    TIMEOUT = 10


def set_setting(key, value):
    if not KODISTUBS:
        ADDON.setSetting(key, value)


def get_message(id):
    if KODISTUBS:
        return ''
    return ADDON.getLocalizedString(id)