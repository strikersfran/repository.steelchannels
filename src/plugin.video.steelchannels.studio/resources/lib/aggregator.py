# -*- coding: utf-8 -*-

import xbmcgui
import time

from .addon import *
from .loggers import log
from resources.servers.cinecalidad import cinecalidad

PG = 0


def progress_update(dialog):
    def inner(current):
        dialog.update(current)

    return inner


def progress_info(dialog):
    def inner(current, total, start=False, end=False):
        global PG
        dialog.update(PG + current)
        if current + 1 == total and end is True:
            PG += total

    return inner


def get_dialog_header():
    return '%s - %s' % (ADDON_NAME, ADDON_VERSION)


def create_dialog(message):
    dialog = xbmcgui.DialogProgressBG()
    dialog.create(get_dialog_header(), message)
    return dialog


def aggregate(action):
    dialog = create_dialog(get_message(action))
    callback = progress_update(dialog)

    callback(5)

    cinecalidad(action,callback)

    dialog.close()
    #log("agregate")
