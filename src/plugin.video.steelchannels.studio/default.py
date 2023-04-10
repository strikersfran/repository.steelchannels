# -*- coding: utf-8 -*-

import sys

import xbmc

from resources.lib.loggers import showInfoNotification
from resources.lib.loggers import showErrorNotification
from resources.lib.aggregator import aggregate

try:    
    param = sys.argv[1]
    if param == "action=download":
        aggregate(30201)#descargar
    else:
        aggregate(30202)#actualizar

    showInfoNotification("Contenido Actualizado")
    #xbmc.executebuiltin('RestartApp')
except:
    showErrorNotification("Error al ejecutar la descarga")