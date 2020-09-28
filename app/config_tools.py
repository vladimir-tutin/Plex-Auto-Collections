# -*- coding: UTF-8 -*-
import os
import yaml
from plexapi.server import PlexServer
from plexapi.video import Movie
from plexapi.video import Show
from plexapi.library import MovieSection
from plexapi.library import ShowSection
from trakt import Trakt
import trakt_helpers

class Config:
    def __init__(self, config_path):
        #self.config_path = os.path.join(os.getcwd(), 'config.yml')
        self.config_path = config_path
        with open(self.config_path, 'rt', encoding='utf-8') as yml:
            self.data = yaml.load(yml, Loader=yaml.FullLoader)
        self.collections = self.data['collections']
        self.plex = self.data['plex']
        # Make 'tmdb' key optional
        if 'tmdb' in self.data:
            self.tmdb = self.data['tmdb']
        else:
            self.tmdb = {}
        # Make 'trakt' key optional
        if 'trakt' in self.data:
            self.trakt = self.data['trakt']
        else:
            self.trakt = {}
        # Make 'radarr' key optional
        if 'radarr' in self.data:
            self.radarr = self.data['radarr']
        else:
            self.radarr = {}
        # Make 'image-server' key optional
        if 'image-server' in self.data:
            self.image_server = self.data['image-server']
        else:
            self.image_server = {}


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
            raise RuntimeError("Unsupported library type in Plex config")
        self.Movie = Movie
        self.Show = Show


class Radarr:
    def __init__(self, config_path):
        config = Config(config_path).radarr
        self.url = config['url']
        # Set 'version' to v2 if not set
        if 'version' in config:
            self.version = config['version']
        else:
            self.version = "v2"
        self.token = config['token']
        self.quality_profile_id = config['quality_profile_id']
        self.root_folder_path = config['root_folder_path']
        # Set 'add_movie' to None if not set
        if 'add_movie' in config: 
            self.add_movie = config['add_movie']
        else:
            self.add_movie = None
        # Support synonyms 'search_movie' and 'search'; add logical default to False
        if 'search_movie' in config:
            self.search_movie = config['search_movie']
        elif 'search' in config:
            self.search_movie = config['search']
        else:
            self.search_movie = False

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
        
        print("Attempting to find posters directory")
        
        if 'poster-directory' in config:
            self.posterdirectory = config['poster-directory']
        else:
            app_dir = os.path.dirname(os.path.realpath(__file__))

            # Test separate config directory with nested 'posters' directory
            if os.path.exists(os.path.join(app_dir, "..", "config", "posters")):
                self.posterdirectory = os.path.abspath(os.path.join(app_dir, "..", "config", "posters"))
            # Test separate config folder with nested 'images' directory
            elif os.path.exists(os.path.join(app_dir, "..", "config", "images")):
                self.posterdirectory = os.path.abspath(os.path.join(app_dir, "..", "config", "images"))
            # Test nested posters directory
            elif os.path.exists(os.path.join(app_dir, "posters")):
                self.posterdirectory = os.path.abspath(os.path.join(app_dir, "posters"))
            # Test nested images directory
            elif os.path.exists(os.path.join(app_dir, "images")):
                self.posterdirectory = os.path.abspath(os.path.join(app_dir, "images"))
            else:
                print("Invalid poster-directory setting")
            
        if self.posterdirectory: 
            print("Using {} as poster directory".format(self.posterdirectory))
        
        print("Attempting to find backgrounds directory")
        
        if 'background-directory' in config:
            self.backgrounddirectory = config['background-directory']
        else:
            app_dir = os.path.dirname(os.path.realpath(__file__))

            # Test separate config directory with nested 'posters' directory
            if os.path.exists(os.path.join(app_dir, "..", "config", "backgrounds")):
                self.backgrounddirectory = os.path.abspath(os.path.join(app_dir, "..", "config", "backgrounds"))
            # Test nested posters directory
            elif os.path.exists(os.path.join(app_dir, "backgrounds")):
                self.backgrounddirectory = os.path.abspath(os.path.join(app_dir, "backgrounds"))
            else:
                print("Invalid background-directory setting")
            
        if self.backgrounddirectory: 
            print("Using {} as background directory".format(self.backgrounddirectory))


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
