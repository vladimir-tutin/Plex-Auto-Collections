# -*- coding: UTF-8 -*-
import os
import yaml
import requests
import socket
from plexapi.server import PlexServer
from plexapi.video import Movie
from plexapi.video import Show
from plexapi.library import MovieSection
from plexapi.library import ShowSection
from plexapi.library import Collections
from plex_tools import get_actor_rkey
from plex_tools import add_to_collection
from plex_tools import get_collection
from radarr_tools import add_to_radarr
from imdb_tools import tmdb_get_summary
from trakt import Trakt
import trakt_helpers

class Config:
    def __init__(self, config_path):
        #self.config_path = os.path.join(os.getcwd(), 'config.yml')
        self.config_path = config_path
        with open(self.config_path, 'rt', encoding='utf-8') as yml:
            self.data = yaml.load(yml, Loader=yaml.FullLoader)
        self.plex = self.data['plex']
        self.tmdb = self.data['tmdb']
        self.trakt = self.data['trakt']
        self.radarr = self.data['radarr']
        self.collections = self.data['collections']
        self.image_server = self.data['image-server']


class Plex:
    def __init__(self, config_path):
        config = Config(config_path).plex
        self.url = config['url']
        self.token = config['token']
        self.timeout = 60
        self.library = config['library']
        self.library_type = config['library_type']
        self.Server = PlexServer(self.url, self.token, timeout=self.timeout)
        self.Sections = self.Server.library.sections()
        if self.library_type == "movie":
            self.Library = next((s for s in self.Sections if (s.title == self.library) and (isinstance(s, MovieSection))), None)
        elif self.library_type == "show":
            self.Library = next((s for s in self.Sections if (s.title == self.library) and (isinstance(s, ShowSection))), None)
        else:
            print("Unsupported library type!")
        self.Movie = Movie
        self.Show = Show


class Radarr:
    def __init__(self, config_path):
        config = Config(config_path).radarr
        self.url = config['url']
        self.token = config['token']
        self.quality = config['quality_profile_id']


class TMDB:
    def __init__(self, config_path):
        config = Config(config_path).tmdb
        self.apikey = config['apikey']
        self.language = config['language']


class TraktClient:
    def __init__(self, config_path):
        config = Config(config_path).trakt
        self.client_id = config['client_id']
        self.client_secret = config['client_secret']
        self.authorization = config['authorization']
        Trakt.configuration.defaults.client(self.client_id, self.client_secret)
        # Try the token from the config
        self.updated_authorization = trakt_helpers.authenticate(self.authorization)
        Trakt.configuration.defaults.oauth.from_response(self.updated_authorization)
        if self.updated_authorization != self.authorization:
            trakt_helpers.save_authorization(Config(config_path).config_path, self.updated_authorization)


class ImageServer:
    def __init__(self, config_path):
        config = Config(config_path).image_server
        try:
            self.host = config['host']
        except:
            a = 1
        try:
            self.port = config['port']
        except:
            a = 1

def update_from_config(config_path, plex, skip_radarr=False):
    config = Config(config_path)
    collections = config.collections
    if isinstance(plex.Library, MovieSection):
        libtype = "movie"
    elif isinstance(plex.Library, ShowSection):
        libtype = "show"
    for c in collections:
        print("Updating collection: {}...".format(c))
        methods = [m for m in collections[c] if m not in ("details", "subfilters")]
        subfilters = []
        if "subfilters" in collections[c]:
            for sf in collections[c]["subfilters"]:
                sf_string = sf, collections[c]["subfilters"][sf]
                subfilters.append(sf_string)
        for m in methods:
            if isinstance(collections[c][m], list):
                # Support multiple imdb/tmdb/trakt lists
                values = collections[c][m]
            else:
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
                    missing = add_to_collection(config_path, plex, m, v, c, subfilters)
                except UnboundLocalError:  # No sub-filters
                    missing = add_to_collection(config_path, plex, m, v, c)
                except (KeyError, ValueError) as e:
                    print(e)
                    missing = False
                if missing:
                    if libtype == "movie":
                        if "imdb" in m:
                            method_name = "IMDb"
                        elif "trakt" in m":
                            method_name = "Trakt"
                        else:
                            method_name = "TMDb"
                        print("{} missing movies from {} List: {}".format(len(missing), method_name, v))
                        if not skip_radarr:
                            if input("Add missing movies to Radarr? (y/n): ").upper() == "Y":
                                add_to_radarr(config_path, missing)
                    elif libtype == "show":
                        if "trakt" in m:
                            method_name = "Trakt"
                        else:
                            method_name = "TMDb"
                        print("{} missing shows from {} List: {}".format(len(missing), method_name, v))
                        # if not skip_sonarr:
                        #     if input("Add missing shows to Sonarr? (y/n): ").upper() == "Y":
                        #         add_to_radarr(missing_shows)
        # Multiple collections of the same name
        if "details" in collections[c]:
            # # Check if there are multiple collections with the same name
            # movie_collections = plex.MovieLibrary.search(title=c, libtype="collection")
            # show_collections = plex.ShowLibrary.search(title=c, libtype="collection")
            # if len(movie_collections + show_collections) > 1:
            #     print("Multiple collections named {}.\nUpdate of \"details\" is currently unsupported.".format(c))
            #     continue
            plex_collection = get_collection(plex, c)
            if not isinstance(plex_collection, Collections):
                # No collections created with requested criteria
                continue
            for dt_m in collections[c]["details"]:
                rkey = plex_collection.ratingKey
                # subtype = plex_collection.subtype
                dt_v = collections[c]["details"][dt_m]
                if "summary" in dt_m:
                    if "tmdb" in dt_m:
                        try:
                            dt_v = tmdb_get_summary(config_path, dt_v, "overview")
                        except AttributeError:
                            dt_v = tmdb_get_summary(config_path, dt_v, "biography")

                    library_name = plex.Library

                    #section = plex.Server.library.section(library_name).key
                    section = library_name.key
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
                        if not r.status_code == 404:
                            # Create url for request to Plex
                            url = plex.url + "/library/metadata/" + str(rkey) + "/posters"
                            querystring = {"url": poster,
                                               "X-Plex-Token": config.plex['token']}
                            response = requests.request("POST", url, params=querystring)
                    except:
                        False

def modify_config(config_path, c_name, m, value):
    config = Config(config_path)
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
