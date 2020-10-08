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


def checkForAttribute(config, attribute, text="{} attribute", testList=None, options="", default=None, doPrint=True, type="str"):
    message = ""
    if attribute not in config:                                 message = "| Config Error: " + text.format(attribute) + " not found"
    elif not config[attribute] and config[attribute] != False:  message = "| Config Error: " + text.format(attribute) + " is blank"
    elif type == "bool":
        if isinstance(config[attribute], bool):                     return config[attribute]
        else:                                                       message = "| Config Error: " + text.format(attribute) + " must be either true or false"
    elif type == "int":
        if isinstance(config[attribute], int):                      return config[attribute]
        else:                                                       message = "| Config Error: " + text.format(attribute) + " must an integer"
    elif testList == None:                                      return config[attribute]
    elif config[attribute] in testList:                         return config[attribute]
    else:                                                       message = "| Config Error: " + text.format(attribute) + ": {} is an invalid input".format(config[attribute])

    if default == None:                                         sys.exit(message + ("\n" if len(options) > 0 else "") + options)
    if doPrint:
        print(message + " using {} as default".format(default))
        if attribute in config and config[attribute] and testList != None and config[attribute] not in testList:
            print(options)
    return default


class Config:
    valid = None
    def __init__(self, config_path):
        self.config_path = config_path
        with open(self.config_path, 'rt', encoding='utf-8') as yml:
            self.data = yaml.load(yml, Loader=yaml.FullLoader)
        self.collections = self.data['collections']
        if "plex" not in self.data: sys.exit("| Config Error: plex attribute not found")
        self.plex = self.data['plex']
        self.tmdb = self.data['tmdb'] if 'tmdb' in self.data else {}
        self.trakt = self.data['trakt'] if 'trakt' in self.data else {}
        self.radarr = self.data['radarr'] if 'radarr' in self.data else {}
        self.image_server = self.data['image-server'] if 'image-server' in self.data else {}
        if Config.valid == None:
            Config.valid = True
            print("|===================================================================================================|")
            print("| Connecting to plex...")
            Plex(config_path)
            print("| plex connection scuccessful")
            print("|===================================================================================================|")
            if "tmdb" not in self.data:             print("| tmdb attribute not found")
            else:                                   TMDB(config_path)
            print("|===================================================================================================|")
            if "trakt" not in self.data:            print("| trakt attribute not found")
            else:                                   TraktClient(config_path)
            print("|===================================================================================================|")
            if "radarr" not in self.data:           print("| radarr attribute not found")
            else:                                   Radarr(config_path)
            print("|===================================================================================================|")
            if "image-server" not in self.data:     print("| image-server attribute not found")
            else:                                   ImageServer(config_path)
            print("|===================================================================================================|")

class Plex:
    def __init__(self, config_path):
        config = Config(config_path).plex
        if not config:
            sys.exit("| Config Error: plex attribute has no sub-attributes")
        self.url = checkForAttribute(config, "url", text="plex sub-attribute {}")
        self.token = checkForAttribute(config, "token", text="plex sub-attribute {}")
        self.timeout = 60
        self.library = checkForAttribute(config, "library", text="plex sub-attribute {}")
        self.library_type = checkForAttribute(config, "library_type", text="plex sub-attribute {}", testList=["movie", "show"], options="| movie (Movie Library)\n| show (Show Library)")
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
            self.url = checkForAttribute(config, "url", text="radarr sub-attribute {}")
            self.version = checkForAttribute(config, "version", text="radarr sub-attribute {}", testList=["v2", "v3"], default="v2", doPrint=False)
            self.token = checkForAttribute(config, "token", text="radarr sub-attribute {}")
            self.quality_profile_id = checkForAttribute(config, "quality_profile_id", text="radarr sub-attribute {}")
            self.root_folder_path = checkForAttribute(config, "root_folder_path", text="radarr sub-attribute {}")
            self.add_movie = checkForAttribute(config, "add_movie", text="radarr sub-attribute {}", type="bool", default=False, doPrint=False)
            self.search_movie = checkForAttribute(config, "search_movie", text="radarr sub-attribute {}", type="bool", default=False, doPrint=False)
        elif Radarr.valid == None:
            if TMDB.valid:
                print("| Connecting to radarr...")
                try:
                    self.url = checkForAttribute(config, "url", text="radarr sub-attribute {}")
                    self.version = checkForAttribute(config, "version", text="radarr sub-attribute {}", testList=["v2", "v3"], options="| v2 (For Radarr 0.2)\n| v3 (For Radarr 3.0)", default="v2")
                    self.token = checkForAttribute(config, "token", text="radarr sub-attribute {}")
                    self.quality_profile_id = checkForAttribute(config, "quality_profile_id", text="radarr sub-attribute {}")
                    self.root_folder_path = checkForAttribute(config, "root_folder_path", text="radarr sub-attribute {}")
                    self.add_movie = checkForAttribute(config, "add_movie", text="radarr sub-attribute {}", options="| true (Add missing movies to Radarr)\n| false (Do not add missing movies to Radarr)", type="bool", default=False)
                    self.search_movie = checkForAttribute(config, "search_movie", text="radarr sub-attribute {}", options="| true (Have Radarr seach the added movies)\n| false (Do not have Radarr seach the added movies)", type="bool", default=False)
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
            self.apikey = checkForAttribute(config, "apikey", text="tmdb sub-attribute {}")
            self.language = checkForAttribute(config, "language", text="tmdb sub-attribute {}", default="en", doPrint=False)
        elif TMDB.valid == None:
            print("| Connecting to tmdb...")
            tmdb = Collection()
            try:
                self.apikey = checkForAttribute(config, "apikey", text="tmdb sub-attribute {}")
                self.language = checkForAttribute(config, "language", text="tmdb sub-attribute {}", default="en")
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
            self.client_id = checkForAttribute(config, "client_id", text="trakt sub-attribute {}")
            self.client_secret = checkForAttribute(config, "client_secret", text="trakt sub-attribute {}")
            self.authorization = config['authorization']
            Trakt.configuration.defaults.client(self.client_id, self.client_secret)
            Trakt.configuration.defaults.oauth.from_response(self.authorization)
        elif TraktClient.valid == None:
            print("| Connecting to trakt...")
            try:
                self.client_id = checkForAttribute(config, "client_id", text="trakt sub-attribute {}")
                self.client_secret = checkForAttribute(config, "client_secret", text="trakt sub-attribute {}")
                self.authorization = config['authorization']

                def checkTrakt ():
                    try:
                        trakt_url = "https://trakt.tv/users/movistapp/lists/christmas-movies"
                        if trakt_url[-1:] == " ":
                            trakt_url = trakt_url[:-1]
                        imdb_map = {}
                        trakt_list_path = urlparse(trakt_url).path
                        trakt_list_items = trakt.Trakt[trakt_list_path].items()
                        title_ids = [m.pk[1] for m in trakt_list_items if isinstance(m, trakt.objects.movie.Movie)]
                        return True
                    except:
                        return False

                if not checkTrakt():
                    self.authorization = {'access_token': None, 'token_type': None, 'expires_in': None, 'refresh_token': None, 'scope': None, 'created_at': None}
                    print("| Stored Authorization Failed")
                Trakt.configuration.defaults.client(self.client_id, self.client_secret)
                self.updated_authorization = trakt_helpers.authenticate(self.authorization)

                if checkTrakt():
                    Trakt.configuration.defaults.oauth.from_response(self.updated_authorization)
                    if self.updated_authorization != self.authorization:
                        trakt_helpers.save_authorization(Config(config_path).config_path, self.updated_authorization)
                    TraktClient.valid = True
                else:
                    TraktClient.valid = False
            except SystemExit as e:
                print(e)
                TraktClient.valid = False
            print("| trakt connection {}".format("scuccessful" if TMDB.valid else "failed"))

class ImageServer:
    valid = None
    def __init__(self, config_path):
        config = Config(config_path).image_server

        if config:
            self.poster = config['poster-directory'] if 'poster-directory' in config and config['poster-directory'] and os.path.exists(os.path.abspath(config['poster-directory'])) else None
            self.background = config['background-directory'] if 'background-directory' in config and config['background-directory'] and os.path.exists(os.path.abspath(config['background-directory'])) else None
            self.image = config['image-directory'] if 'image-directory' in config and config['image-directory'] and os.path.exists(os.path.abspath(config['image-directory'])) else None
        else:
            self.poster = "posters" if os.path.exists(os.path.abspath("posters")) else "..\\config\\posters" if os.path.exists(os.path.abspath("..\\config\\posters")) else None
            self.background = "backgrounds" if os.path.exists(os.path.abspath("backgrounds")) else "..\\config\\backgrounds" if os.path.exists(os.path.abspath("..\\config\\backgrounds")) else None
            self.image = "images" if os.path.exists(os.path.abspath("images")) else "..\\config\\images" if os.path.exists(os.path.abspath("..\\config\\images")) else None

        if ImageServer.valid == None:
            print("| Locating image-server...")
            if config:
                def checkPath(attribute, value, extra=None):
                    v = os.path.abspath(value)
                    if attribute in config:               print("| Using {} for {}".format(v, attribute) if os.path.exists(v) else "{} not found: {}".format(attribute, v) if value else "{} attribute is empty".format(attribute))
                    elif extra and extra not in config:   print("| {} & {} attributes not found".format(attribute, extra))
                checkPath("poster-directory", self.poster, "image-directory")
                checkPath("background-directory", self.background, "image-directory")
                checkPath("image-directory", self.image)
            else:
                if self.poster:            print("| Using {} for posters directory".format(os.path.abspath(self.poster)))
                if self.background:        print("| Using {} for backgrounds directory".format(os.path.abspath(self.background)))
                if self.image:             print("| Using {} for images directory".format(os.path.abspath(self.image)))
                if not self.poster and not self.background and not self.image:
                    print("| posters directory not found: {} or {}".format(os.path.abspath("posters"), os.path.abspath("..\\config\\posters")))
                    print("| backgrounds directory not found: {} or {}".format(os.path.abspath("backgrounds"), os.path.abspath("..\\config\\backgrounds")))
                    print("| images directory not found: {} or {}".format(os.path.abspath("images"), os.path.abspath("..\\config\\images")))
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
