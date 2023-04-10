import sys
import xbmc
import xbmcplugin
from inputstreamhelper import Helper
from resources.lib.youtube_dl import YoutubeDL
from resources.lib.loggers import *
from resources.lib.database import *
import urllib.parse


# python embedded (as used in kodi) has a known bug for second calls of strptime. 
# The python bug is docmumented here https://bugs.python.org/issue27400 
# The following workaround patch is borrowed from https://forum.kodi.tv/showthread.php?tid=112916&pid=2914578#pid2914578
def patch_strptime():
    import datetime

    #fix for datatetime.strptime returns None
    class proxydt(datetime.datetime):
        @staticmethod
        def strptime(date_string, format):
            import time
            return datetime.datetime(*(time.strptime(date_string, format)[0:6]))

    datetime.datetime = proxydt

# patch broken strptime (see above)
patch_strptime()

ydl_opts = {
    'format': 'best',
    'extract_flat': 'in_playlist'
}

def okru(url):
    ydl = YoutubeDL(ydl_opts)
    ydl.add_default_info_extractors()

    with ydl:
        try:
            result = ydl.extract_info(url, download=False, ie_key="Odnoklassniki")
            return result

        except:
            showErrorNotification("Could not resolve the url, check the log for more info")            
            return False

def create_list(url,headers,movie_id,handle):
    result = okru(url)    
    #debug("ok.ru result: "+str(result))
    if result:
        adaptive_type = False
        url = extract_manifest_url(result)
        if url is not None:
            log("found original manifest: " + url)
            adaptive_type, supported = check_if_kodi_supports_manifest(url)
            if not supported:
                url = None 
        if url is None:
            for entry in result['formats']:
                #si detectamos que dentro de los formatos hay uno con manifest_url lo devolvemos inmediatamente
                if 'manifest_url' in entry and get_adaptive_type_from_url(entry['manifest_url']):
                    url = entry['manifest_url']
                    break
            if url is None:
                log("could not find an original manifest or manifest is not supported falling back to best all-in-one stream")
                url = extract_best_all_in_one_stream(result)
        if url is None:
            err_msg = "Error: was not able to extract manifest or all-in-one stream. Implement https://github.com/firsttris/plugin.video.sendtokodi/issues/34"
            log(err_msg)
            showInfoNotification(err_msg)
            raise Exception(err_msg)

        #extraer del url final el timestamp        
        data= urllib.parse.parse_qs(url.replace("?","&"))
        debug("ok.ru url final: "+str(url))
        timestamp = data["expires"][0]
        #grabamos en la base de datos la ultima url usada                
        set_last_url_movie(movie_id,url,timestamp,"ok")
        
        log("creating list item for url {}".format(url))
        post = "|user-agent="+headers["User-Agent"]+"&referer="+headers["Referer"]
        list_item = xbmcgui.ListItem(result['title'], path=url+post)
        list_item.setInfo(type='Video', infoLabels={'Title': result['title'], 'plot': result.get('description', None)})
        if result.get('thumbnail', None) is not None:
            list_item.setArt({'thumb': result['thumbnail']})
        subtitles = result.get('subtitles', {})
        if subtitles:
            list_item.setSubtitles([
                subtitleListEntry['url']
                for lang in subtitles
                for subtitleListEntry in subtitles[lang]
            ])
        if adaptive_type:
            list_item.setProperty('inputstream', 'inputstream.adaptive')
            list_item.setProperty('inputstream.adaptive.stream_selection_type', 'adaptive')
            list_item.setProperty('inputstream.adaptive.manifest_type', adaptive_type)

        xbmcplugin.setResolvedUrl(handle, True, listitem=list_item)

    else:
        log("Fallo url no encontrada okru: " + url)


# def createListItemFromVideo(result):
#     #debug(result)
#     adaptive_type = False
#     #if xbmcplugin.getSetting(int(sys.argv[1]),"usemanifest") == 'true':
#     url = extract_manifest_url(result)
#     if url is not None:
#         log("found original manifest: " + url)
#         adaptive_type, supported = check_if_kodi_supports_manifest(url)
#         if not supported:
#             url = None 
#     if url is None:
#         log("could not find an original manifest or manifest is not supported falling back to best all-in-one stream")
#         url = extract_best_all_in_one_stream(result)
#     if url is None:
#         err_msg = "Error: was not able to extract manifest or all-in-one stream. Implement https://github.com/firsttris/plugin.video.sendtokodi/issues/34"
#         log(err_msg)
#         showInfoNotification(err_msg)
#         raise Exception(err_msg)
#     # else:
#     #     url = result['url']
#     log("creating list item for url {}".format(url))
#     list_item = xbmcgui.ListItem(result['title'], path=url)
#     list_item.setInfo(type='Video', infoLabels={'Title': result['title'], 'plot': result.get('description', None)})
#     if result.get('thumbnail', None) is not None:
#         list_item.setArt({'thumb': result['thumbnail']})
#     subtitles = result.get('subtitles', {})
#     if subtitles:
#         list_item.setSubtitles([
#             subtitleListEntry['url']
#             for lang in subtitles
#             for subtitleListEntry in subtitles[lang]
#         ])
#     if adaptive_type:
#         list_item.setProperty('inputstream', 'inputstream.adaptive')
#         list_item.setProperty('inputstream.adaptive.stream_selection_type', 'adaptive')
#         list_item.setProperty('inputstream.adaptive.manifest_type', adaptive_type)


#     return list_item

def extract_manifest_url(result):
    # sometimes there is an url directly 
    # but for some extractors this is only one quality and sometimes not even a real manifest
    if 'manifest_url' in result and get_adaptive_type_from_url(result['manifest_url']):
        return result['manifest_url']
    # otherwise we must relay that the requested formats have been found and 
    # extract the manifest url from them
    if 'requested_formats' not in result:
        return None
    for entry in result['requested_formats']:
        # the resolver marks not all entries with video AND audio 
        # but usually adaptive video streams also have audio
        if 'manifest_url' in entry and 'vcodec' in entry and get_adaptive_type_from_url(entry['manifest_url']):
            return entry['manifest_url']
    return None


def extract_best_all_in_one_stream(result):
    # if there is nothing to choose from simply take the shot it is correct
    if len(result['formats']) == 1:
        return result['formats'][0]['url'] 
    audio_video_streams = [] 
    filter_format = (lambda f: f.get('vcodec', 'none') != 'none' and f.get('acodec', 'none') != 'none')
    # assume it is a video containg audio. Get the one with the highest resolution
    for entry in result['formats']:
        # #si detectamos que dentro de los formatos hay uno con manifest_url lo devolvemos inmediatamente
        # if 'manifest_url' in entry and get_adaptive_type_from_url(entry['manifest_url']):
        #     return entry['manifest_url']
        if filter_format(entry):
            audio_video_streams.append(entry)
    if audio_video_streams:
            return max(audio_video_streams, key=lambda f: f['width'])['url'] 
    # test if it is an audio only stream
    if result.get('vcodec', 'none') == 'none': 
        # in case of multiple audio streams get the best
        audio_streams = []
        filter_format = (lambda f: f.get('abr', 'none') != 'none')
        for entry in result['formats']:
            if filter_format(entry):
                audio_streams.append(entry)
        if audio_streams:
            return max(audio_streams, key=lambda f: f['abr'])['url'] 
        # not all extractors provide an abr (and other fields are also not guaranteed), try to get any audio 
        if (entry.get('acodec', 'none') != 'none') or entry.get('ext', False) in ['mp3', 'wav', 'opus']:
            return entry['url']      
    # was not able to resolve
    return None

def get_adaptive_type_from_url(url):
    supported_endings = [".m3u8", ".hls", ".mpd", ".rtmp", ".ism"]
    if url is None:
        return False
    file = url.split('/')[-1]
    for ending in supported_endings:
        if ending in file:
            # adaptive input stream plugin needs the type which is not the same as the file ending
            if ending  == ".m3u8":  
                return "hls"
            else:
                return ending.lstrip('.')
    log("Manifest type could not be identified for {}".format(file))
    return False

def check_if_kodi_supports_manifest(url):    
    adaptive_type = get_adaptive_type_from_url(url)
    is_helper = Helper(adaptive_type) 
    supported = is_helper.check_inputstream()
    if not supported:
        msg = "your kodi instance does not support the adaptive stream manifest of " + url + ", might need to install the adpative stream plugin"
        showInfoNotification("msg")
        log(msg=msg, level=xbmc.LOGWARNING)
    return adaptive_type, supported