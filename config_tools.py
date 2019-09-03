# -*- coding: UTF-8 -*-
import os
import yaml
import requests
import socket
from plexapi.server import PlexServer
from plexapi.video import Movie
from plex_tools import get_actor_rkey
from plex_tools import add_to_collection
from plex_tools import get_collection
from radarr_tools import add_to_radarr
from imdb_tools import tmdb_get_summary

class Config:
    def __init__(self):
        self.config_path = os.path.join(os.getcwd(), 'config.yml')
        with open(self.config_path, 'rt', encoding='utf-8') as yml:
            self.data = yaml.load(yml, Loader=yaml.FullLoader)
        self.plex = self.data['plex']
        self.tmdb = self.data['tmdb']
        self.radarr = self.data['radarr']
        self.collections = self.data['collections']
        self.image_server = self.data['image-server']


class Plex:
    def __init__(self):
        config = Config().plex
        self.url = config['url']
        self.token = config['token']
        self.library = config['library']
        self.Server = PlexServer(self.url, self.token)
        self.MovieLibrary = self.Server.library.section(self.library)
        self.Movie = Movie


class Radarr:
    def __init__(self):
        config = Config().radarr
        self.url = config['url']
        self.token = config['token']
        self.quality = config['quality_profile_id']


class TMDB:
    def __init__(self):
        config = Config().tmdb
        self.apikey = config['apikey']
        self.language = config['language']

class ImageServer:
    def __init__(self):
        config = Config().image_server
        try:
            self.host = config['host']
        except:
            a = 1
        try:
            self.port = config['port']
        except:
            a = 1

def update_from_config(plex, skip_radarr=False):
    config = Config()
    collections = config.collections
    for c in collections:
        print("Updating collection: {}...".format(c))
        methods = [m for m in collections[c] if m not in ("details", "subfilters")]
        subfilters = []
        if "subfilters" in collections[c]:
            for sf in collections[c]["subfilters"]:
                sf_string = sf, collections[c]["subfilters"][sf]
                subfilters.append(sf_string)
        for m in methods:
            values = collections[c][m].split(", ")
            for v in values:
                if m[-1:] == "s":
                    m_print = m[:-1]
                else:
                    m_print = m
                print("Processing {}: {}".format(m_print, v))
                if m == "actors" or m == "actor":
                    v = get_actor_rkey(plex, v)
                try:
                    missing = add_to_collection(plex, m, v, c, subfilters)
                except UnboundLocalError:  # No sub-filters
                    missing = add_to_collection(plex, m, v, c)
                except KeyError as e:
                    print(e)
                    missing = False
                if missing:
                    if "imdb" in m:
                        m = "IMDB"
                    else:
                        m = "TMDb"
                    print("{} missing movies from {} List: {}".format(len(missing), m, v))
                    if not skip_radarr:
                        if input("Add missing movies to Radarr? (y/n): ").upper() == "Y":
                            add_to_radarr(missing)
        if "details" in collections[c]:
            for dt_m in collections[c]["details"]:
                rkey = get_collection(plex, c).ratingKey
                dt_v = collections[c]["details"][dt_m]
                if "summary" in dt_m:
                    if "tmdb" in dt_m:
                        try:
                            dt_v = tmdb_get_summary(dt_v, "overview")
                        except AttributeError:
                            dt_v = tmdb_get_summary(dt_v, "biography")

                    library_name = plex.library
                    section = plex.Server.library.section(library_name).key
                    url = plex.url + "/library/sections/" + str(section) + "/all"

                    querystring = {"type":"18",
                                   "id": str(rkey),
                                   "summary.value": dt_v,
                                   "X-Plex-Token": config.plex['token']}
                    response = requests.request("PUT", url, params=querystring)
                poster = None
                if "poster" in dt_m:
                    if "tmdb" in dt_m:
                        poster = "https://image.tmdb.org/t/p/original/"
                        poster = poster + tmdb_get_summary(dt_v).poster_path
                    else:
                        poster = dt_v
                if not poster:
                    # try to pull image from image_server. File is Collection name.png
                    # Setup connection to image_server
                    try:
                        host = config.image_server["host"]
                    except AttributeError:
                        host = "127.0.0.1"
                    try:
                        port = config.image_server["port"]
                    except AttributeError:
                        port = "5000"

                    # Replace spaces in collection name with %20
                    c_name = c.replace(" ", "%20")
                    # Create url to where image would be if exists
                    poster = "http://" + host + ":" + str(port) + "/images/" + c_name
                    try:
                        r = requests.request("GET", poster)
                    except:
                        False
                if not r.status_code == 404:
                    # Create url for request to Plex
                    url = plex.url + "/library/metadata/" + str(rkey) + "/posters"
                    querystring = {"url": poster,
                                       "X-Plex-Token": config.plex['token']}
                    response = requests.request("POST", url, params=querystring)

def modify_config(c_name, m, value):
    config = Config()
    if m == "movie":
        print("Movie's in config not supported yet")
    else:
        try:
            if value not in str(config.data['collections'][c_name][m]):
                try:
                    config.data['collections'][c_name][m] = \
                        config.data['collections'][c_name][m] + ", {}".format(value)
                except TypeError:
                    config.data['collections'][c_name][m] = value
            else:
                print("Value already in collection config")
                return
        except KeyError:
            config.data['collections'][c_name][m] = value
        print("Updated config file")
        with open(config.config_path, "w") as f:
            yaml.dump(config.data, f)
