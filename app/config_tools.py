# -*- coding: UTF-8 -*-
import os
import sys
import yaml
import requests
from tmdbv3api import Collection
from plexapi.server import PlexServer
from plexapi.video import Movie
from plexapi.video import Show
from plexapi.library import MovieSection
from plexapi.library import ShowSection
from trakt import Trakt
import trakt_helpers
import trakt


def check_for_attribute(config, attribute, text="{} attribute", test_list=None, options="", default=None, do_print=True, default_is_none=False, type="str"):
    message = ""
    if attribute not in config:                                 message = "| Config Error: " + text.format(attribute) + " not found"
    elif not config[attribute] and config[attribute] != False:  message = "| Config Error: " + text.format(attribute) + " is blank"
    elif type == "bool":
        if isinstance(config[attribute], bool):                     return config[attribute]
        else:                                                       message = "| Config Error: " + text.format(attribute) + " must be either true or false"
    elif type == "int":
        if isinstance(config[attribute], int):                      return config[attribute]
        else:                                                       message = "| Config Error: " + text.format(attribute) + " must an integer"
    elif test_list == None:                                      return config[attribute]
    elif config[attribute] in test_list:                         return config[attribute]
    else:                                                       message = "| Config Error: " + text.format(attribute) + ": {} is an invalid input".format(config[attribute])

    if default == None and not default_is_none:                 sys.exit(message + ("\n" if len(options) > 0 else "") + options)
    if do_print:
        print(message + " using {} as default".format(default))
        if attribute in config and config[attribute] and test_list != None and config[attribute] not in test_list:
            print(options)
    return default


class Config:
    valid = None
    headless = None
    def __init__(self, config_path, headless=False):
        if Config.headless == None:
            Config.headless = headless
        self.config_path = config_path
        with open(self.config_path, 'rt', encoding='utf-8') as yml:
            self.data = yaml.load(yml, Loader=yaml.FullLoader)
        if "collections" not in self.data: sys.exit("| Config Error: collections attribute not found")
        self.collections = self.data['collections']
        if "plex" not in self.data: sys.exit("| Config Error: plex attribute not found")
        self.plex = self.data['plex']
        self.tmdb = self.data['tmdb'] if 'tmdb' in self.data else {}
        self.trakt = self.data['trakt'] if 'trakt' in self.data else {}
        self.radarr = self.data['radarr'] if 'radarr' in self.data else {}
        self.image_server = self.data['image_server'] if 'image_server' in self.data else {}
        if Config.valid == None:
            Config.valid = True
            print("|===================================================================================================|")
            print("| Connecting to plex...")
            Plex(config_path)
            print("| plex connection scuccessful")
            print("|===================================================================================================|")
            if "tmdb" not in self.data:
                TMDB.valid = False
                print("| tmdb attribute not found")
            else:
                TMDB(config_path)
            print("|===================================================================================================|")
            if "trakt" not in self.data:
                TraktClient.valid = False
                print("| trakt attribute not found")
            else:
                TraktClient(config_path)
            print("|===================================================================================================|")
            if "radarr" not in self.data:
                Radarr.valid = False
                print("| radarr attribute not found")
            else:
                Radarr(config_path)
            print("|===================================================================================================|")
            if "image_server" not in self.data:
                ImageServer.valid = False
                print("| image_server attribute not found")
            else:
                ImageServer(config_path)
            print("|===================================================================================================|")

class Plex:
    def __init__(self, config_path):
        config = Config(config_path).plex
        if not config:
            sys.exit("| Config Error: plex attribute has no sub-attributes")
        self.url = check_for_attribute(config, "url", text="plex sub-attribute {}")
        self.token = check_for_attribute(config, "token", text="plex sub-attribute {}")
        self.timeout = 60
        self.library = check_for_attribute(config, "library", text="plex sub-attribute {}")
        self.library_type = check_for_attribute(config, "library_type", text="plex sub-attribute {}", test_list=["movie", "show"], options="| movie (Movie Library)\n| show (Show Library)")
        self.Server = PlexServer(self.url, self.token, timeout=self.timeout)
        self.Sections = self.Server.library.sections()
        if self.library_type == "movie":
            self.Library = next((s for s in self.Sections if (s.title == self.library) and (isinstance(s, MovieSection))), None)
        elif self.library_type == "show":
            self.Library = next((s for s in self.Sections if (s.title == self.library) and (isinstance(s, ShowSection))), None)
        self.Movie = Movie
        self.Show = Show
        if not self.Library:
            sys.exit("| Config Error: Plex Library {} not found".format(self.library))

class Radarr:
    valid = None
    def __init__(self, config_path):
        config = Config(config_path).radarr
        if Radarr.valid:
            self.url = check_for_attribute(config, "url", text="radarr sub-attribute {}")
            self.version = check_for_attribute(config, "version", text="radarr sub-attribute {}", test_list=["v2", "v3"], default="v2", do_print=False)
            self.token = check_for_attribute(config, "token", text="radarr sub-attribute {}")
            self.quality_profile_id = check_for_attribute(config, "quality_profile_id", text="radarr sub-attribute {}")
            self.root_folder_path = check_for_attribute(config, "root_folder_path", text="radarr sub-attribute {}")
            self.add_movie = check_for_attribute(config, "add_movie", text="radarr sub-attribute {}", type="bool", default_is_none=True, do_print=False)
            self.search_movie = check_for_attribute(config, "search_movie", text="radarr sub-attribute {}", type="bool", default=False, do_print=False)
        elif Radarr.valid == None:
            if TMDB.valid:
                print("| Connecting to radarr...")
                try:
                    self.url = check_for_attribute(config, "url", text="radarr sub-attribute {}")
                    self.version = check_for_attribute(config, "version", text="radarr sub-attribute {}", test_list=["v2", "v3"], options="| v2 (For Radarr 0.2)\n| v3 (For Radarr 3.0)", default="v2")
                    self.token = check_for_attribute(config, "token", text="radarr sub-attribute {}")
                    self.quality_profile_id = check_for_attribute(config, "quality_profile_id", text="radarr sub-attribute {}")
                    self.root_folder_path = check_for_attribute(config, "root_folder_path", text="radarr sub-attribute {}")
                    self.add_movie = check_for_attribute(config, "add_movie", text="radarr sub-attribute {}", options="| true (Add missing movies to Radarr)\n| false (Do not add missing movies to Radarr)", type="bool", default_is_none=True)
                    self.search_movie = check_for_attribute(config, "search_movie", text="radarr sub-attribute {}", options="| true (Have Radarr seach the added movies)\n| false (Do not have Radarr seach the added movies)", type="bool", default=False)
                    try:
                        payload = {"qualityProfileId": self.quality_profile_id}
                        response = requests.post(self.url + ("/api/v3/movie" if self.version == "v3" else "/api/movie"), json=payload, params={"apikey": "{}".format(self.token)})
                        if response.json()[0]['errorMessage'] == "Profile does not exist":
                            sys.exit("| Config Error: radarr sub-attribute quality_profile_id: {} does not exist in radarr".format(self.quality_profile_id))
                        Radarr.valid = True
                    except SystemExit:
                        raise
                    except:
                        sys.exit("| Could not connect to radarr ar {}".format(self.url))
                except SystemExit as e:
                    print(e)
                    Radarr.valid = False
                print("| radarr connection {}".format("scuccessful" if Radarr.valid else "failed"))
            else:
                print("| tmdb must be connected to use radarr")
                Radarr.valid = False

class TMDB:
    valid = None
    def __init__(self, config_path):
        config = Config(config_path).tmdb
        if TMDB.valid:
            self.apikey = check_for_attribute(config, "apikey", text="tmdb sub-attribute {}")
            self.language = check_for_attribute(config, "language", text="tmdb sub-attribute {}", default="en", do_print=False)
        elif TMDB.valid == None:
            print("| Connecting to tmdb...")
            tmdb = Collection()
            try:
                self.apikey = check_for_attribute(config, "apikey", text="tmdb sub-attribute {}")
                self.language = check_for_attribute(config, "language", text="tmdb sub-attribute {}", default="en")
                try:
                    tmdb.api_key = self.apikey
                    tmdb.details("100693").parts
                    TMDB.valid = True
                except AttributeError:
                    print("| Config Error: Invalid apikey")
                    TMDB.valid = False
            except SystemExit as e:
                print(e)
                TMDB.valid = False
            print("| tmdb connection {}".format("scuccessful" if TMDB.valid else "failed"))

class TraktClient:
    valid = None
    def __init__(self, config_path):
        config = Config(config_path).trakt
        if TraktClient.valid:
            self.client_id = check_for_attribute(config, "client_id", text="trakt sub-attribute {}")
            self.client_secret = check_for_attribute(config, "client_secret", text="trakt sub-attribute {}")
            self.authorization = config['authorization']
            Trakt.configuration.defaults.client(self.client_id, self.client_secret)
            Trakt.configuration.defaults.oauth.from_response(self.authorization)
        elif TraktClient.valid == None:
            print("| Connecting to trakt...")
            try:
                self.client_id = check_for_attribute(config, "client_id", text="trakt sub-attribute {}")
                self.client_secret = check_for_attribute(config, "client_secret", text="trakt sub-attribute {}")
                self.authorization = config['authorization']

                def check_trakt (auth):
                    try:
                        #TODO: Validate Trakt Connection
                        return True
                    except:
                        return False

                if not check_trakt(self.authorization):
                    self.authorization = {'access_token': None, 'token_type': None, 'expires_in': None, 'refresh_token': None, 'scope': None, 'created_at': None}
                    print("| Stored Authorization Failed")
                Trakt.configuration.defaults.client(self.client_id, self.client_secret)
                self.updated_authorization = trakt_helpers.authenticate(self.authorization, headless=Config.headless)

                if check_trakt(self.updated_authorization):
                    try:
                        Trakt.configuration.defaults.oauth.from_response(self.updated_authorization)
                        if self.updated_authorization != self.authorization:
                            trakt_helpers.save_authorization(Config(config_path).config_path, self.updated_authorization)
                        TraktClient.valid = True
                    except:
                        TraktClient.valid = False
                else:
                    TraktClient.valid = False
            except SystemExit as e:
                print(e)
                TraktClient.valid = False
            print("| trakt connection {}".format("scuccessful" if TraktClient.valid else "failed"))

class ImageServer:
    valid = None
    def __init__(self, config_path):
        config = Config(config_path).image_server
        app_dir = os.path.dirname(os.path.abspath(__file__))

        if config:
            self.poster = config['poster_directory'] if 'poster_directory' in config and config['poster_directory'] and os.path.exists(os.path.abspath(config['poster_directory'])) else None
            self.background = config['background_directory'] if 'background_directory' in config and config['background_directory'] and os.path.exists(os.path.abspath(config['background_directory'])) else None
            self.image = config['image_directory'] if 'image_directory' in config and config['image_directory'] and os.path.exists(os.path.abspath(config['image_directory'])) else None
        else:
            self.poster = "posters" if os.path.exists(os.path.join(app_dir, "posters")) else "..\\config\\posters" if os.path.exists(os.path.join(app_dir, "..", "config", "posters")) else None
            self.background = "backgrounds" if os.path.exists(os.path.join(app_dir, "backgrounds")) else "..\\config\\backgrounds" if os.path.exists(os.path.join(app_dir, "..", "config", "backgrounds")) else None
            self.image = "images" if os.path.exists(os.path.join(app_dir, "images")) else "..\\config\\images" if os.path.exists(os.path.join(app_dir, "..", "config", "images")) else None

        if ImageServer.valid == None:
            print("| Locating image_server...")
            if config:
                def checkPath(attribute, value, extra=None):
                    v = os.path.abspath(value)
                    if attribute in config:               print("| Using {} for {}".format(v, attribute) if os.path.exists(v) else "{} not found: {}".format(attribute, v) if value else "{} attribute is empty".format(attribute))
                    elif extra and extra not in config:   print("| {} & {} attributes not found".format(attribute, extra))
                checkPath("poster_directory", self.poster, "image_directory")
                checkPath("background_directory", self.background, "image_directory")
                checkPath("image_directory", self.image)
            else:
                if self.poster:            print("| Using {} for posters directory".format(os.path.abspath(self.poster)))
                if self.background:        print("| Using {} for backgrounds directory".format(os.path.abspath(self.background)))
                if self.image:             print("| Using {} for images directory".format(os.path.abspath(self.image)))
                if not self.poster and not self.background and not self.image:
                    print("| posters directory not found: {} or {}".format(os.path.join(app_dir, "posters"), os.path.join(app_dir, "..", "config", "posters")))
                    print("| backgrounds directory not found: {} or {}".format(os.path.join(app_dir, "backgrounds"), os.path.join(app_dir, "..", "config", "backgrounds")))
                    print("| images directory not found: {} or {}".format(os.path.join(app_dir, "images"), os.path.join(app_dir, "..", "config", "images")))
            ImageServer.valid = True if self.poster or self.background or self.image else False


def modify_config(config_path, c_name, m, value):
    config = Config(config_path)
    if m == "movie":
        print("| Movie's in config not supported yet")
    else:
        try:
            if value not in str(config.data['collections'][c_name][m]):
                try:
                    config.data['collections'][c_name][m] = \
                        config.data['collections'][c_name][m] + ", {}".format(value)
                except TypeError:
                    config.data['collections'][c_name][m] = value
            else:
                print("| Value already in collection config")
                return
        except KeyError:
            config.data['collections'][c_name][m] = value
        print("| Updated config file")
        with open(config.config_path, "w") as f:
            yaml.dump(config.data, f)
