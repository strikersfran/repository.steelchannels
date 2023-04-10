import os
import sqlite3
from datetime import datetime
import xbmcaddon

ADDON = xbmcaddon.Addon()
#PATH_DATA = os.path.join(".kodi/userdata/addon_data/", ADDON.getAddonInfo("id"))
PATH_DATA = os.path.join(ADDON.getAddonInfo("path").replace("/addons/"+ADDON.getAddonInfo("id"),""),"userdata/addon_data/"+ADDON.getAddonInfo("id"))

connection = sqlite3.connect(PATH_DATA+"/steelchannels.db")

#esta funcion crea las tabla si no existes
def create():
    cursor = connection.cursor()
    movie_table(cursor)
    cursor.close()

#para crear la tabla de peliculas
def movie_table(cursor):

    cursor.execute("CREATE TABLE IF NOT EXISTS movie (id INTEGER NOT NULL PRIMARY KEY, server TEXT)")

    cursor.execute("CREATE TABLE IF NOT EXISTS movie_stream (movie_id INTEGER, type TEXT, temp_id INTEGER, permanet_url TEXT, last_url TEXT, last_time INTEGER, estatus INTEGER)")

#obtener una pelicula por su id
def get_movie(id):
    cursor = connection.cursor()

    rows = cursor.execute("SELECT * FROM movie LEFT JOIN movie_stream ON movie.id = movie_stream.movie_id WHERE movie.id = ?",(id, )).fetchall()

    cursor.close()
    return rows

#obtener una pelicula por su id y verificar si tiene last_url disponible
def get_movie_last_url(id,type):
    cursor = connection.cursor()

    row = cursor.execute("SELECT * FROM movie_stream WHERE movie_id=? and type=? AND last_url !=''",(id, type )).fetchone()

    cursor.close()
    return row

#obtener la url final de la pelicula dependiendo del tipo de stream
def get_movie_for_stream(id, type):
    cursor = connection.cursor()

    row = cursor.execute("SELECT * FROM movie_stream WHERE movie_id = ? AND type =?",(id,type )).fetchone()

    cursor.close()
    return row

#insertar una pelicula
def insert_movie(movie,streams):
    cursor = connection.cursor()
    cursor.execute("INSERT INTO movie (id,server) VALUES (?,?)",(movie["id"],movie["server"]))

    for stream in streams:
        cursor.execute("INSERT INTO movie_stream (movie_id , type , temp_id , permanet_url , last_url , last_time, estatus ) VALUES (?,?,?,?,?,?,?)",(movie["id"],stream["type"],stream["temp_id"],stream["permanet_url"],"","",stream["estatus"]))
    
    connection.commit()
    cursor.close()
    return True

#agregar una pelicula si no existe
def add_movie(movie,streams):
    #buscamos primero para aber si existe
    rows = get_movie(movie["id"])

    if len(rows) == 0:
        insert_movie(movie,streams)

#actualizar información de una pelicula
def set_last_url_movie(id,last_url,timestamp,type):

    cursor = connection.cursor()
    cursor.execute("UPDATE movie_stream SET last_url = ?,last_time =? WHERE movie_id=? and type=?",(last_url,timestamp,id,type))

    connection.commit()
    cursor.close()

#actualizar el permanente url del stream
def set_permanete_url_movie_stream(id,type,permanet_url):
    cursor = connection.cursor()
    cursor.execute("UPDATE movie_stream SET permanet_url = ? WHERE movie_id=? AND type=?",(permanet_url,id,type))

    connection.commit()
    cursor.close()

#actualizar status del stream
def set_status_movie_stream(id,type,estatus):
    cursor = connection.cursor()
    cursor.execute("UPDATE movie_stream SET estatus = ? WHERE movie_id=? WHERE type=?",(estatus,id,type))

    connection.commit()
    cursor.close()