# -*- coding: utf-8 -*-
import requests
from resources.lib.loggers import debug
from resources.lib.addon import USERAGENT
import xbmcplugin
import xbmcgui
import sys
from resources.lib.database import *

#Para resolver la url del video para el servidor fembed consultando el API y verificando su respuesta
#Ejemplo de Respuesta del API
#{
# "success":true,
# "data":[{
#   "file":"https:\/\/fvs.io\/redirector?token=Zm9uci9VbHUzWmJqTGhXdEVVejYyNE8xZEl0dzNrbW1QMkg0TWhqMzM2NjUyQVBJaTZiMFlEWG1rYS80U01pTE02UFRGWm5jOXZlOHU3WUZDNGwvUE1abklmYlh5V0tUMDJNVThwUVRoUDRHNy93UjM4N2U3ZkN5TUdqNU1iM09GYjdFOE52SVAwemI1cDgwL1M4eE9naWxnaXM1QVU2b0VnPT06d1ZEcVhvU25iS0UwY3dnQWYvRW82QT09Ns8g",
#   "label":"480p","type":"mp4"},{
#   "file":"https:\/\/fvs.io\/redirector?token=bGY3aGRUUGg2K3I3YmtnSXJrZDAzK2xQTUFoV0ZvemNBTmpxLytkSlNMM0NjRXNJUWZzNnRQbFltSXVGR3BLQkJHL1dxTlNWaWZpWnN5cG1VN2lMTFRCd3laOHE3ekZaa3Z2MzlmVTBwdE4wamYrbVpTemVJWVliU3FhZDVXblBGU3d1bUtJZHJ3Z2RBWTl4OENDWGFrWGluWTlxZFkyQ2ZGaz06ZS9FZWk1Q0hEQnlWNFNjem1jVForUT09ugCh",
#   "label":"720p","type":"mp4"}],
# "captions":[],
# "is_vr":false
# }

def fembed(url,headers,movie_id):
    resolution = xbmcplugin.getSetting(int(sys.argv[1]),"quality_default")
    try:
        # consultar el API
        form_data = {'r':headers["Referer"],'d':'vanfem.com'}
        response = requests.post(url, timeout=30, data=form_data,headers=headers)

        if response.status_code == 200:
            #obtener la respuesta en json
            response_json = response.json()        
            debug("response code: "+ str(response.status_code))
            debug("Respuesta Obtenida: " +str(response_json['data']))

            if isinstance(response_json['data'],list):
                for stream in response_json['data']:
                    if stream['label'] ==  resolution:
                        file = stream['file']
                        break
                    else:
                        file = response_json['data'][0]['file']

                #ahora extraemos el url final del video
                try:
                    new_response = requests.get(file, timeout=30, allow_redirects=False,headers=headers)
                    
                    debug("nuevo response code: "+ str(new_response.status_code))
                    debug("Nueva URL Obtenida: " +str(new_response.headers['Location']))

                    url_final = new_response.headers['Location']                
                    
                    return url_final
                
                except requests.exceptions.Timeout:
                    debug("Tiempo exedido para acceder al Servidor fembed")
                    return False
                except requests.exceptions.RequestException as e:    
                    debug("Servidor fembed Excepcion: " +str(e))
                    return False   
            else:
                return False

        else:
            debug("response code: "+ str(response.status_code))
            return False

    except requests.exceptions.Timeout:
        debug("Tiempo exedido para acceder al Servidor fembed")
        return False
    except requests.exceptions.RequestException as e:    
        debug("Servidor fembed Excepcion: " +str(e))
        return False

def create_list(url,headers,movie_id):
    file = fembed(url,headers,movie_id)

    if file:

        #extraer del url final el timestamp
        timestamp = file.split("/")[4]
        #grabamos en la base de datos la ultima url usada                
        set_last_url_movie(movie_id,file,timestamp,"fembed")

        #creamos el list item vacio
        debug("creating list item for url {}".format(file))
        post = "|user-agent="+headers["User-Agent"]+"&referer=https://vanfem.com/"#+headers["Referer"]
        list_item = xbmcgui.ListItem("", path=file+post)          
        #list_item.setInfo(type='Video', infoLabels={'Title': "", 'plot': ""})
        list_item.setMimeType("video/mp4")

        return list_item
    else:
        return False
