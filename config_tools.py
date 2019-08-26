# -*- coding: UTF-8 -*-
import os
import yaml
from plex_tools import get_actor_rkey
from plex_tools import add_to_collection
from plexapi.server import PlexServer
from plexapi.video import Movie
from radarr_tools import add_to_radarr

class Config:
    def __init__(self):
        self.config_path = os.path.join(os.getcwd(), 'config.yml')
        with open(self.config_path, 'rt', encoding='utf-8') as yml:
            self.data = yaml.load(yml, Loader=yaml.FullLoader)
        self.plex = self.data['server']
        self.tmdb = self.data['tmdb']
        self.radarr = self.data['radarr']
        self.collections = self.data['collections']

class Plex:
    def __init__(self):
        config = Config().plex
        url = config['url']
        token = config['token']
        library = config['library']
        self.Server = PlexServer(url, token)
        self.MovieLibrary = self.Server.library.section(library)
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

def update_from_config(plex, skip_radarr=False):
    collections = Config().collections
    for c in collections:
        print("Updating collection: {}...".format(c))
        methods = [m for m in collections[c] if "subfilters" not in m]
        if "subfilters" in collections[c]:
            subfilters = []
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
                except UnboundLocalError:
                    missing = add_to_collection(plex, m, v, c)
                if missing:
                    print("{} missing movies from IMDB List: {}".format(len(missing), v))
                    if not skip_radarr:
                        if input("Add missing movies to Radarr? (y/n)").upper() == "Y":
                            add_to_radarr(missing)
    print("\n")

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

