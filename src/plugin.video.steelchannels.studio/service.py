# -*- coding: utf-8 -*-

import xbmc

from resources.lib.addon import SERVICE_FREQUENCY
from resources.lib.loggers import showInfoNotification
from resources.lib.database import create as create_database
create_database()
from resources.lib.aggregator import aggregate

MONITOR = xbmc.Monitor()

if __name__ == '__main__':
    while not MONITOR.abortRequested():        
        showInfoNotification('Ejecutando el servicio')        
        aggregate(30201)#descargar
        if MONITOR.waitForAbort(SERVICE_FREQUENCY * 3600):
            break
