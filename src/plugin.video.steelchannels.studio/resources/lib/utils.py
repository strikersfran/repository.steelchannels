# -*- coding: utf-8 -*-
import sys
import xbmc
import xbmcgui
import xbmcplugin

from resources.lib.loggers import *
from inputstreamhelper import Helper
from resources.servers.cinecalidad import play as cinecalidad_play
#from resources.servers.cinecalidad import get_url_fembed, get_url_streamlare


#Esta funcion verifica si el url del streaming es de tipo HLS u otro soportado por kodi
def get_adaptive_type(url):
    supported_endings = [".m3u8", ".hls", ".mpd", ".rtmp", ".ism",'.mp4']
    file = url.split('/')[-1]
    for ending in supported_endings:
        if ending in file:
            # si el url del streaming es .m3u8 entonces el tipo es hls
            if ending  == ".m3u8":  
                return "hls"
            else:
                return ending.lstrip('.')
    log("Manifest type could not be identified for {}".format(file))
    return "mp4"
    return False

#Esta funcion verifica si kodi soporta el formato del streaming del url pasado 
def kodi_supports(url):

    adaptive_type = get_adaptive_type(url)

    if adaptive_type != 'mp4':
        is_helper = Helper(adaptive_type) 
        supported = is_helper.check_inputstream()
        if not supported:
            msg = "your kodi instance does not support the adaptive stream manifest of " + url + ", might need to install the adpative stream plugin"
            showInfoNotification(msg)
            log(msg=msg, level=xbmc.LOGWARNING)
    else:
        supported = True
        adaptive_type = False

    return adaptive_type, supported

#Funcion para crea la instancia del video a reproducir
def create_list_item(file):
    debug(file) 

    adaptive_type, supported = kodi_supports(file)

    if not supported:
        err_msg = "Formato de vido no soportado por KODI"
        log(err_msg)
        showInfoNotification(err_msg)
        raise Exception(err_msg)

    #creamos el list item vacio
    log("creating list item for url {}".format(file))
    list_item = xbmcgui.ListItem("", path=file)
    #+"|User-Agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36")
    list_item.setInfo(type='Video', infoLabels={'Title': "", 'plot': ""})  

    if adaptive_type:

        list_item.setProperty('inputstream', 'inputstream.adaptive')
        list_item.setProperty('inputstream.adaptive.manifest_type', adaptive_type)  
        list_item.setProperty('inputstream.adaptive.stream_headers', 'user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36')

        #verificamos si fue configurado el uso de stream adaptativo
        if xbmcplugin.getSetting(int(sys.argv[1]),"stream_enabled") == 'true' and adaptive_type: 
            list_item.setProperty('inputstream.adaptive.stream_selection_type', 'adaptive')
            list_item.setProperty('inputstream.adaptive.manifest_update_parameter', 'full')
            
        else:
            resolution = xbmcplugin.getSetting(int(sys.argv[1]),"quality_default")
            #reproducir solo el stream segun la calidad seleccionada en la configuracion
            log("Reproduciendo el video con maxima resolucion de " +str(resolution))
            #list_item.setProperty('inputstream', 'inputstream.ffmpegdirect')
            #list_item.setProperty('inputstream.ffmpegdirect.manifest_type', adaptive_type)
            #list_item.setProperty('http-reconnect', True)
            list_item.setProperty('inputstream.adaptive.stream_selection_type', 'fixed-res')
            list_item.setProperty('inputstream.adaptive.chooser_resolution_max', str(resolution))
    else:#para mp4
        #list_item.setProperty('inputstream', 'inputstream.ffmpegdirect')
        #list_item.setProperty('inputstream.ffmpegdirect.manifest_type', 'mp4')
        log("Archivo MP4 ")

    return list_item

#esta funcion permite identificar a que plataforma pertenece la url del video
#y redirigirla a la funcion correcta
def urlResolver(handle,url):
    #verificamos si el url pertenece a cinecalidad
    if 'http' not in url and "cinecalidad" in url:
        debug("Url proviene de cinecalidad")
        cinecalidad_play(handle,url)
    else:
        showErrorNotification("Plataforma no identificada")


#Esta funcion permite resolver el url identificando el tipo de plataforma a la que pertnece 
# def urlResolver_old(handle,url):
#     file = False
#     #url extructurado para los 3 servidores de cinecalidd
#     if 'http' not in url:
#         data= urllib.parse.parse_qs(url)
#         debug("data url: "+str(data))
#         debug("ok id: "+data["ok"][0])
#         #verificamos si tenemos mas de un servidor disponible
#         server_num = 0
#         list = []
#         index = 0 #seleccion por defecto
#         if data["ok"][0] != "0":
#             server_num+=1
#             list.append("Ok")
#             #index = 0 #seleccion por defecto
#         if data["streamlare"][0] != "0":
#             server_num+=1
#             list.append("Streamlare")
#             #index = 1 #seleccion por defecto
#         if data["fembed"][0] != "0":
#             server_num+=1
#             list.append("Fembed") 
#             #index = 2 #seleccion por defecto       
        
#         if server_num > 1:
#             #abrimos una ventana de seleecion
#             index = xbmcgui.Dialog().contextmenu(list)                        
        
#         if index >= 0:
#             if list[index] == "Ok" :
#                 debug("Seleccionado el servidor OK.ru")
#             elif list[index] == "Streamlare":
#                 debug("Seleccionado el servidor Streamlare")
#                 url = get_url_streamlare("trembed="+data["streamlare"][0]+"&trid="+data["trid"][0]+"&trtype="+data["trtype"][0])
#             elif list[index] == "Fembed":
#                 debug("Seleccionado el servidor Fembed")
#                 url = get_url_fembed("trembed="+data["fembed"][0]+"&trid="+data["trid"][0]+"&trtype="+data["trtype"][0])
    
#     debug("Resolviendo la URL: "+url)
#     #xbmc.executebuiltin('RestartApp')
#     #exit()  
#     #url directos
#     #para link del servidor streamlare final
#     if 'streamlare' in url:
#         file = streamlare(url)
#     if 'vanfem.com' in url:
#         file = fembed(url)
#         # Create a playable item with a path to play.
#         #play_item = xbmcgui.ListItem(path=file)
#         # Pass the item to the Kodi player.
#         #xbmcplugin.setResolvedUrl(handle, True, listitem=play_item)
      
	
#     if not file:
#         showErrorNotification("Video no encontrado")
#     else:
#     	xbmcplugin.setResolvedUrl(handle, True, listitem=create_list_item(file))
