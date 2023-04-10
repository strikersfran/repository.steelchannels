import sys
import base64
import requests
import re
from bs4 import BeautifulSoup
from resources.lib.loggers import *
from resources.lib.addon import *
import resources.lib.folder as folder
import urllib.parse
import resources.lib.streamlare as streamlare
import resources.lib.fembed as fembed
import resources.lib.okru as okru
from resources.lib.database import *
from datetime import datetime, timedelta
#import pytz

import xbmc
import xbmcgui
import xbmcplugin

base_url = "https://cinecalidad.ms/"
fembed_api_url = "https://vanfem.com/api/source/"
streamlare_api_url = "https://sltube.org/api/video/stream/get?id="
okru_url = "https://ok.ru/videoembed/"

PATH_MOVIES = os.path.join(FOLDER, 'cinecalidad/movies')
PATH_SERIES = os.path.join(FOLDER, 'cinecalidad/series')
CREATED = 0
REMOVED = 0

headers = {
    'User-Agent': USERAGENT,
    "Referer": base_url
}

def cinecalidad(action,callback):
    
    try:
        main_page = requests.get(base_url, timeout=30)
        soup_main = BeautifulSoup(main_page.content, "html.parser")

        results_pages = soup_main.find_all('a',class_="page-numbers")

        #obtenemos el valor de la ultima pagina
        last_page_num = results_pages[-2].text.strip()
        if len(results_pages[-2]["href"].split("?"))>1:
            params = results_pages[-2]["href"].split("?")[1]
        else:
            params=""

        log("Action: "+str(action))
        log("Ultima pagina: "+str(last_page_num))
        CINECALIDAD_NUM_PAGE = ADDON.getSetting('num_page')
        total_page=int(CINECALIDAD_NUM_PAGE)
        #verificamos si es update o download todas
        if action == 30201:#download
            next = 0
            #ultima pagina visitada
            if CINECALIDAD_MOVIE_PAGE != '0':
                last_page_num = int(CINECALIDAD_MOVIE_PAGE)-1#la ultima pagina descargada menos una o sea la siguiente
                if CINECALIDAD_MOVIE_PAGE == '1':
                    last_page_num = int(CINECALIDAD_MOVIE_PAGE)+2
                    total_page = 2
            #realizamos el el escaneo desde la ultima pagina hacia la 1 cada 10 paginas
            for i in range(total_page):
                callback(15 + int(i * 15 / total_page))
                next = int(last_page_num)-int(i)
                if next > 0:
                    log("Url page: "+base_url+"page/"+str(next)+"/?"+params)
                    page = requests.get(base_url+"page/"+str(next)+"/?"+params, timeout=30, headers=headers)
                    soup = BeautifulSoup(page.content, "html.parser")
                    items = soup.find_all('a', class_="absolute")
                    log("Entro en descargar pagina: "+str(next))                    

                    for item in items:
                        if "pelicula" in item["href"]:
                            log(item["href"])
                            get_movie(item["href"])
                    #para grabar que ya fue descargada la pagina
                    set_setting('movie_page',str(next))
                else:
                    next = 1
                        
            #set_setting('movie_page',str(next))
        else:#para el caso de update 
            items = soup_main.find_all('a', class_="absolute")
            log("Entro en update")
            for item in items:
                if "pelicula" in item["href"]:
                    log(item["href"])
                    get_movie(item["href"])                    
        
        log(results_pages[-2])
        
        callback(100)

        clean_update_library()

    except requests.exceptions.Timeout:
        debug("Tiempo exedido para acceder al Servidor cinecalidad")
        return False
    except requests.exceptions.RequestException as e:    
        debug("Cinecalidad Excepcion: " +str(e))
        return False
    # except Exception as e:
    #     debug("Error Fatal cinecalidad")
    #     debug(e)

def get_movie(url):
    try:
        page = requests.get(url, timeout=30)
        soup = BeautifulSoup(page.content, "html.parser")

        tmdb = soup.find(id="tmdb-s")
        if tmdb:
            tmdb = tmdb["href"]
        uls = soup.find("ul", class_="options")
        if uls:
            servers = uls.find_all("a",href="#!")
        else:
            return False
        id = url.split("/")[-2]#url.replace(base_url+"pelicula/","").replace("/","")
        movie_url = ""
        trid="0"#id de la pelicula
        trtype="0"#tipo de contenido
        fembed_id="0"#servidor fembed
        streamlare_id="0"#servidor streamlare
        ok_id="0"#servidor ok.ru
        #streams = []

        #vamos a buscar los url de los servidores ok, streamlare y fembed y extreaerle sus id
        #para tener las 3 opciones en la url de plugin player
        for serv in servers:
            if serv.get("data-src") !='':
                url_temp = base64.b64decode(serv.get("data-src")).decode('utf-8')
                #remplazamos el url base del url_temp
                url_temp = url_temp.replace(base_url+"?","")
                #ahora hacemos un split por el simbolo &
                split_url = url_temp.split("&")
                #la posicio 1 y 2 corresponde al id de la pelicula y el tipo
                trid=split_url[1]
                trtype=split_url[2]
                #movie_id = int(trid.split("=")[1])
                #LOS 3 MEJORES SERVIDORES
                if "FEMBED" in serv.get_text().upper():
                    fembed_id=split_url[0].split("=")[1]
                    #movie_url = get_url_fembed(url_temp)
                    #streams.append({"movie_id":movie_id,"type":"fembed","temp_id":int(fembed_id),"permanet_id":"","estatus":1})
                if "STREAMLARE" in serv.get_text().upper():
                    streamlare_id=split_url[0].split("=")[1]
                    #streams.append({"movie_id":movie_id,"type":"streamlare","temp_id":int(streamlare_id),"permanet_id":"","estatus":1})
                if "OK" in serv.get_text().upper():
                    ok_id=split_url[0].split("=")[1]
                    #streams.append({"movie_id":movie_id,"type":"ok","temp_id":int(ok_id),"permanet_id":"","estatus":1})
        
        #si no existe ningunos de los servidores activo entonces no contruimos el url
        if ok_id =="0" and streamlare_id == "0" and fembed_id == "0":
            log("Pelicula no tiene servidores online")
            return False
        #contruimos el url final
        movie_url = "server=cinecalidad&ok="+ok_id+"&streamlare="+streamlare_id+"&fembed="+fembed_id+"&"+trid+"&"+trtype

        log("Pelicula encontrada: tmdb: " +str(tmdb))
        log("Pelicula Url: " +movie_url)
        log("Pelicula ID: "+id)

        if id and movie_url and tmdb:
            #verificamos si existe el directorio
            folder.init_dir(PATH_MOVIES+"/"+id)
            #creamos el archivo strm y nfo
            create_strm(PATH_MOVIES+"/"+id, "movie", str(movie_url))
            create_nfo(PATH_MOVIES+"/"+id, tmdb, "movie")  

            # #creamos el registro en la base de datos
            add_movie_db(movie_url)
            # movie = {"id":movie_id,"server":"cinecalidad","last_url":"","last_time":0}
            # add_movie(movie,streams) 
                         

    except requests.exceptions.Timeout:
        debug("Tiempo exedido cinecalidad get_movie")
        return False
    except requests.exceptions.RequestException as e:    
        debug("Cinecalidad get_movie Excepcion: " +str(e))
        return False

#para obtener el id finales de los servidores embed
def get_id_embed(url):
    try:
        if base_url not in url:
            url = base_url+"?"+url
        page = requests.get(url, timeout=30)
        soup = BeautifulSoup(page.content, "html.parser")

        iframe = soup.find("iframe")
        id = iframe["src"].split("/")[-1]       

        return id

    except requests.exceptions.Timeout:
        debug("Tiempo exedido en Cinecalidad get_embed")
        return False
    except requests.exceptions.RequestException as e:    
        debug("Cinecalidad get_embed Excepcion: " +str(e))
        return False

#para obtener el url final de fembed segun cinecalidad
def get_url_fembed(url):
    
    id = get_id_embed(url)

    if id:
        log("Fembed ID:" +id)

        url_final = fembed_api_url+id

        return url_final
    else:
        return False

#para obtener el url final de streamlare segun cinecalidad
def get_url_streamlare(url):
   
    id = get_id_embed(url)
    if id:
        log("Streamlare ID:" +id)

        url_final = streamlare_api_url+id+"&streamlare=true"

        return url_final    
    else:
        return False

#para obtener el url final de ok.ru segun cinecalidad
def get_url_okru(url):
   
    id = get_id_embed(url)
    if id:
        log("Ok.ru ID:" +id)

        url_final = okru_url+id

        return url_final    
    else:
        return False

def create_strm(folder, name, url):
    global CREATED
    f = open(os.path.join(folder, '%s.strm' % name), 'w')
    f.write('plugin://plugin.video.steelchannels.studio/?%s\n' % url )
    f.close()
    CREATED += 1

def create_nfo(folder, tmdb, type):
    f = open(os.path.join(folder, '%s.nfo' % type), 'w')
    f.write('%s\n' % tmdb)    
    f.close()

def clean_update_library():
    debug('REMOVED: %d' % REMOVED)
    if REMOVED > 0:
        xbmc.executebuiltin('CleanLibrary(video)')
    debug('CREATED: %d' % CREATED)
    if CREATED > 0:
        xbmc.executebuiltin('UpdateLibrary(video)')

#funcion para reproducir una video
def play(handle,url):
    #convertimos los parametros en array
    data= urllib.parse.parse_qs(url)
    debug("data url: "+str(data))

    #por si el archivo .strm existe y no existe en la base de datos
    add_movie_db(url)

    #verificamos si hay un url en db disponible y no vencido para ofrecerlo directo
    # last_url = get_movie_last_url(data["trid"][0])
    # if last_url:
    #     now = datetime.now()#pytz.timezone("Europe/Madrid"))
    #     timestamp = datetime.timestamp(now+timedelta(hours=4))
    #     debug("fecha actual: "+str(now))
    #     debug("timestamp actual: "+str(timestamp))
    #     if int(last_url[3]) > int(timestamp):#significa que aun es valido el url
    #         debug("existe un url valido, timestamp: "+str(last_url[3]))
    #         xbmcplugin.setResolvedUrl(handle, True, listitem=create_list(last_url[2]))
    #         return
    #     else:
    #         debug("existe un url pero esta vencido, timestamp: "+str(last_url[3]))

    #verificamos si tenemos mas de un servidor disponible
    server_num = 0
    list = []
    index = 0 #seleccion por defecto
    if data["ok"][0] != "0":
        server_num+=1
        list.append("Servidor Ok.ru")
    if data["streamlare"][0] != "0":
        server_num+=1
        list.append("Servidor Streamlare")
    if data["fembed"][0] != "0":
        server_num+=1
        list.append("Servidor Fembed (Preferido)")
    
    #abrimos una ventana de seleecion
    if server_num > 1:        
        index = xbmcgui.Dialog().contextmenu(list)                        
    
    if index >= 0:
        if "Ok" in list[index]:
            url_db = True
            debug("Seleccionado el servidor OK.ru")
            #verificamos si ya existe el url final en la base de datos
            row = get_movie_for_stream(data["trid"][0], "ok")
            debug("Row: "+str(row))
            if not (row is None):
                if row[4] != "" and row[4] != None and row[5] != "" and row[5] != None:
                    now = datetime.now()
                    timestamp = datetime.timestamp(now+timedelta(hours=4))
                    debug("fecha actual: "+str(now))
                    debug("timestamp actual: "+str(timestamp))
                    if int(row[5]) > int(timestamp):#significa que aun es valido el url
                        debug("existe un url valido, timestamp: "+str(row[5]))
                        xbmcplugin.setResolvedUrl(handle, True, listitem=create_list(row[4]))
                        return                
                if row[3] != "":
                    url = row[3]  
                    debug("Url de la base de datos") 
                else:
                    url_db = None
            if row is None or url_db is None:
                url = get_url_okru("trembed="+data["ok"][0]+"&trid="+data["trid"][0]+"&trtype="+data["trtype"][0])
                set_permanete_url_movie_stream(data["trid"][0], "ok",url)
            #xbmcplugin.setResolvedUrl(handle, True, listitem=okru.create_list(url,headers,data["trid"][0]))
            okru.create_list(url,headers,data["trid"][0],handle)

        elif "Streamlare" in list[index]:
            url_db = True
            debug("Seleccionado el servidor Streamlare")
            #verificamos si ya existe el url final en la base de datos
            row = get_movie_for_stream(data["trid"][0], "streamlare")
            debug("Row: "+str(row))
            if not (row is None):
                if row[4] != "" and row[4] != None and row[5] != "" and row[5] != None:
                    now = datetime.now()
                    timestamp = datetime.timestamp(now+timedelta(hours=4))
                    debug("fecha actual: "+str(now))
                    debug("timestamp actual: "+str(timestamp))
                    if int(row[5]) > int(timestamp):#significa que aun es valido el url
                        debug("existe un url valido, timestamp: "+str(row[5]))
                        xbmcplugin.setResolvedUrl(handle, True, listitem=create_list(row[4]))
                        return
                if row[3] != "":
                    url = row[3]  
                    debug("Url de la base de datos")             
                else:
                    url_db = None
            if row is None or url_db is None:
                url = get_url_streamlare("trembed="+data["streamlare"][0]+"&trid="+data["trid"][0]+"&trtype="+data["trtype"][0])
                set_permanete_url_movie_stream(data["trid"][0], "streamlare",url)
                
            xbmcplugin.setResolvedUrl(handle, True, listitem=streamlare.create_list(url,headers,data["trid"][0]))
        elif "Fembed" in list[index]:
            url_db = True
            debug("Seleccionado el servidor Fembed")
            row = get_movie_for_stream(data["trid"][0], "fembed")
            debug("Row: "+str(row))
            if not (row is None):
                if row[4] != "" and row[4] != None and row[5] != "" and row[5] != None:
                    now = datetime.now()
                    timestamp = datetime.timestamp(now+timedelta(hours=4))
                    debug("fecha actual: "+str(now))
                    debug("timestamp actual: "+str(timestamp))
                    if int(row[5]) > int(timestamp):#significa que aun es valido el url
                        debug("existe un url valido, timestamp: "+str(row[5]))
                        xbmcplugin.setResolvedUrl(handle, True, listitem=create_list(row[4]))
                        return
                if row[3] != "":
                    url = row[3]    
                    debug("Url de la base de datos")           
                else:
                    url_db = None
            if row is None or url_db is None:
                url = get_url_fembed("trembed="+data["fembed"][0]+"&trid="+data["trid"][0]+"&trtype="+data["trtype"][0])
                set_permanete_url_movie_stream(data["trid"][0], "fembed",url)
            xbmcplugin.setResolvedUrl(handle, True, listitem=fembed.create_list(url,headers,data["trid"][0]))

    else:
        showErrorNotification("No se pudo reproducir el contenido")


def create_list(file):    
    
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

#para agregar a la base de datos en caso de que no este registrado
def add_movie_db(movie_url):
    #movie_url = "server=cinecalidad&ok="+ok_id+"&streamlare="+streamlare_id+"&fembed="+fembed_id+"&"+trid+"&"+trtype
    #convertimos los parametros en array
    data= urllib.parse.parse_qs(movie_url)
    streams = []

    movie_id = data["trid"][0]

    if data["ok"][0] != "0":
        streams.append({"movie_id":movie_id,"type":"ok","temp_id":int(data["ok"][0]),"permanet_url":"","estatus":1})
    if data["streamlare"][0] != "0":
        streams.append({"movie_id":movie_id,"type":"streamlare","temp_id":int(data["streamlare"][0]),"permanet_url":"","estatus":1})
    if data["fembed"][0] != "0":
        streams.append({"movie_id":movie_id,"type":"fembed","temp_id":int(data["fembed"][0]),"permanet_url":"","estatus":1})
    #creamos el registro en la base de datos
    movie = {"id":movie_id,"server":"cinecalidad","last_url":"","last_time":0}

    add_movie(movie,streams)

