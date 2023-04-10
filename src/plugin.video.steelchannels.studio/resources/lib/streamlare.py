# -*- coding: utf-8 -*-
import requests
from resources.lib.loggers import debug
from resources.lib.addon import USERAGENT
import xbmcgui
from resources.lib.database import *
#Para resolver la url del video para el servidor Streamlare consultando el API y verificando su respuesta
#Ejemplo de Respuesta del API
# {
#     "status":"success",
#     "message":"OK",
#     "type":"hls",
#     "token":"2e93a46d18e357bd39f5654b6f66ff9f",
#     "result":{
#         "file":"https:\/\/www-y8a75370.ssl0d.com\/hls2\/UgNc94cupJ6DETLx-2js4A\/1678159835\/-7xHKFKrx_8YTsh0ly7DT6L0bX-08EhzX3mU-JxDivk\/master.m3u8",
#         "type":"application\/x-mpegURL",
#         "title":"Snow.Day.2022.1080P-Dual-Lat.mp4"
#     }
# }
# Retorna el url final del streaming
def streamlare(url,headers,movie_id):
    
    try:
        # consultar el API
        response = requests.post(url, timeout=30,headers=headers)
        file = None

        if response.status_code == 200:
            #obtener la respuesta en json
            response_json = response.json()        
            debug("response code: "+ str(response.status_code))
            debug("Respuesta Obtenida: " +str(response_json))

            if response_json['type'] == "mp4":
                if not (response_json['result'].get("1080p") is None):
                    file = response_json['result']["1080p"]['file']
                elif not (response_json['result'].get("720p") is None):
                    file = response_json['result']["720p"]['file']
                elif not (response_json['result'].get("480p") is None):
                    file = response_json['result']["480p"]['file']
                elif not (response_json['result'].get("360p") is None):
                    file = response_json['result']["360p"]['file']

                #si file no esta definido entonces es un unico url
                if not file:
                    file = response_json['result']['Original']['file']
                    debug("Streamlare url original")

                #ahora extraemos el url final del video
                try:
                    new_response = requests.get(file, timeout=30, allow_redirects=False,headers=headers)
                    
                    debug("nuevo response code: "+ str(new_response.status_code))
                    debug("Nueva URL Obtenida: " +str(new_response.headers['Location']))
                    
                    return new_response.headers['Location']
                
                except requests.exceptions.Timeout:
                    debug("Tiempo exedido para acceder al Servidor fembed")
                    return False
                except requests.exceptions.RequestException as e:    
                    debug("Servidor fembed Excepcion: " +str(e))
                    return False

            else:
                file = response_json['result']['file']

            return file

        else:
            debug("response code: "+ str(response.status_code))
            return False

    except requests.exceptions.Timeout:
        debug("Tiempo exedido para acceder al Servidor Streamlare")
        return False
    except requests.exceptions.RequestException as e:    
        debug("Servidor Streamlare Excepcion: " +str(e))
        return False   

def create_list(url,headers,movie_id):
    file = streamlare(url,headers,movie_id)

    if file:

        #extraer del url final el timestamp
        if ".mp4" in file:
            timestamp = file.split("/")[4]
        else:
            timestamp = file.split("/")[5]
        #grabamos en la base de datos la ultima url usada                
        set_last_url_movie(movie_id,file,timestamp,"streamlare")

        #creamos el list item vacio
        debug("creating list item for url {}".format(file))
        post = "|user-agent="+headers["User-Agent"]+"&referer="+headers["Referer"]
        list_item = xbmcgui.ListItem("", path=file+post)
        list_item.setInfo(type='Video', infoLabels={'Title': "", 'plot': ""})

        if ".mp4" in file:
            list_item.setMimeType("video/mp4")
        elif ".m3u8" in file:
            list_item.setProperty('inputstream', 'inputstream.adaptive')
            list_item.setProperty('inputstream.adaptive.manifest_type', "hls")  
            #list_item.setProperty('inputstream.adaptive.stream_headers', 'user-agent='+USERAGENT)            
            list_item.setProperty('inputstream.adaptive.stream_selection_type', 'adaptive')
            list_item.setProperty('inputstream.adaptive.manifest_update_parameter', 'full')

        return list_item

    else:
        return False