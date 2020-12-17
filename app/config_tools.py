# -*- coding: UTF-8 -*-
import os
import sys
import yaml
import ruamel.yaml
import requests
from yaml.scanner import ScannerError
from urllib.parse import urlparse
from tmdbv3api import Collection
from plexapi.exceptions import Unauthorized
from plexapi.server import PlexServer
from plexapi.video import Movie
from plexapi.video import Show
from plexapi.library import MovieSection
from plexapi.library import ShowSection
from trakt import Trakt
import trakt_helpers


def check_for_attribute(config, attribute, parent=None, test_list=None, options="", default=None, do_print=True, default_is_none=False, var_type="str", throw=False, save=True):
    message = ""
    endline = ""
    text = "{} attribute".format(attribute) if parent is None else "{} sub-attribute {}".format(parent, attribute)
    if config is None or attribute not in config:
        message = "| Config Error: {} not found".format(text)
        if parent and save == True:
            ruamel.yaml.YAML().allow_duplicate_keys = True
            from ruamel.yaml.util import load_yaml_guess_indent
            new_config, ind, bsi = load_yaml_guess_indent(open(Config.config_path))
            endline = "\n| {} sub-attribute {} added to config".format(parent, attribute)
            if parent not in new_config:
                new_config = {parent: {attribute: default}}
            elif not new_config[parent]:
                new_config[parent] = {attribute: default}
            elif attribute not in new_config[parent]:
                new_config[parent][attribute] = default
            else:
                endLine = ""
            ruamel.yaml.round_trip_dump(new_config, open(Config.config_path, 'w'), indent=ind, block_seq_indent=bsi)
    elif not config[attribute] and config[attribute] != False:
        message = "| Config Error: {} is blank".format(text)
    elif var_type == "bool":
        if isinstance(config[attribute], bool):
            return config[attribute]
        else:
            message = "| Config Error: {} must be either true or false".format(text)
    elif var_type == "int":
        if isinstance(config[attribute], int) and config[attribute] > 0:
            return config[attribute]
        else:
            message = "| Config Error: {} must an integer > 0".format(text)
    elif test_list is None or config[attribute] in test_list:
        return config[attribute]
    else:
        message = "| Config Error: {}: {} is an invalid input".format(text, config[attribute])
    if default is not None or default_is_none:
        message = message + " using {} as default".format(default)
    message = message + endline
    if (default is None and not default_is_none) or throw:
        if len(options) > 0:
            message = message + "\n" + options
        sys.exit(message)
    if do_print:
        print(message)
        if attribute in config and config[attribute] and test_list is not None and config[attribute] not in test_list:
            print(options)
    return default


class Config:
    valid = None
    headless = None
    config_path = None
    def __init__(self, config_path, headless=False):
        if Config.headless is None:
            Config.headless = headless
        Config.config_path = config_path
        self.config_path = config_path
        try:
            with open(self.config_path, 'rt', encoding='utf-8') as yml:
                self.data = yaml.load(yml, Loader=yaml.FullLoader)
        except ScannerError as e:
            sys.exit("| Scan Error: {}".format(str(e).replace('\n', '\n|\t      ')))
        if Config.valid == True:
            self.collections = check_for_attribute(self.data, "collections", default={}, do_print=False)
            self.plex = self.data['plex']
            self.tmdb = check_for_attribute(self.data, "tmdb", default={}, do_print=False)
            self.tautulli = check_for_attribute(self.data, "tautulli", default={}, do_print=False)
            self.trakt = check_for_attribute(self.data, "trakt", default={}, do_print=False)
            self.radarr = check_for_attribute(self.data, "radarr", default={}, do_print=False)
            self.image_server = check_for_attribute(self.data, "image_server", default={}, do_print=False)
        elif Config.valid is None:
            Config.valid = True
            print("|===================================================================================================|")
            print("| Connecting to Plex...")
            Plex(config_path)
            self.collections = check_for_attribute(self.data, "collections", default={})
            print("| Plex Connection Successful")
            print("|===================================================================================================|")
            if "tmdb" in self.data:
                TMDB(config_path)
            else:
                TMDB.valid = False
                print("| tmdb attribute not found")
            print("|===================================================================================================|")
            if "tautulli" in self.data:
                Tautulli(config_path)
            else:
                Tautulli.valid = False
                print("| tautulli attribute not found")
            print("|===================================================================================================|")
            if "trakt" in self.data:
                TraktClient(config_path)
            else:
                TraktClient.valid = False
                print("| trakt attribute not found")
            print("|===================================================================================================|")
            if "radarr" in self.data:
                Radarr(config_path)
            else:
                Radarr.valid = False
                print("| radarr attribute not found")
            print("|===================================================================================================|")
            if "image-server" in self.data:
                print("| Config Error: Please change the image-server attribute to image_server")
            if "image_server" in self.data:
                ImageServer(config_path)
            else:
                ImageServer.valid = False
                print("| image_server attribute not found")
            print("|===================================================================================================|")


class Plex:
    valid = None
    def __init__(self, config_path):
        config = Config(config_path).plex
        fatal_message = ""
        message = ""
        try:
            self.library = check_for_attribute(config, "library", parent="plex", throw=True)
        except SystemExit as e:
            fatal_message = fatal_message + "\n" + str(e) if len(fatal_message) > 0 else str(e)
        try:
            self.library_type = check_for_attribute(config, "library_type", parent="plex", test_list=["movie", "show"], options="| \tmovie (Movie Library)\n| \tshow (Show Library)", throw=True)
        except SystemExit as e:
            fatal_message = fatal_message + "\n" + str(e) if len(fatal_message) > 0 else str(e)
        try:
            self.token = check_for_attribute(config, "token", parent="plex", throw=True)
        except SystemExit as e:
            fatal_message = fatal_message + "\n" + str(e) if len(fatal_message) > 0 else str(e)
        try:
            self.url = check_for_attribute(config, "url", parent="plex", throw=True)
        except SystemExit as e:
            fatal_message = fatal_message + "\n" + str(e) if len(fatal_message) > 0 else str(e)
        try:
            self.sync_mode = check_for_attribute(config, "sync_mode", parent="plex", default="append", test_list=["append", "sync"], options="| \tappend (Only Add Items to the Collection)\n| \tsync (Add & Remove Items from the Collection)", throw=True)
        except SystemExit as e:
            self.sync_mode = check_for_attribute(config, "sync_mode", parent="plex", default="append", test_list=["append", "sync"], do_print=False)
            message = message + "\n" + str(e) if len(message) > 0 else str(e)
        self.timeout = 60
        if len(fatal_message) > 0:
            sys.exit(fatal_message + "\n" + message)
        if Plex.valid is None and len(message) > 0:
            print(message)
        try:
            self.Server = PlexServer(self.url, self.token, timeout=self.timeout)
        except Unauthorized:
            sys.exit("| Config Error: Plex token is invalid")
        except:
            sys.exit("| Config Error: Plex url is invalid")
        self.Sections = self.Server.library.sections()
        if self.library_type == "movie":
            self.Library = next((s for s in self.Sections if (s.title == self.library) and (isinstance(s, MovieSection))), None)
        elif self.library_type == "show":
            self.Library = next((s for s in self.Sections if (s.title == self.library) and (isinstance(s, ShowSection))), None)
        self.Movie = Movie
        self.Show = Show
        if not self.Library:
            sys.exit("| Config Error: Plex Library {} not found".format(self.library))
        Plex.valid = True


class Radarr:
    valid = None
    def __init__(self, config_path):
        config = Config(config_path).radarr
        if Radarr.valid:
            self.url = check_for_attribute(config, "url", parent="radarr")
            self.version = check_for_attribute(config, "version", parent="radarr", test_list=["v2", "v3"], default="v2", do_print=False)
            self.token = check_for_attribute(config, "token", parent="radarr")
            self.quality_profile_id = check_for_attribute(config, "quality_profile_id", parent="radarr", var_type="int")
            self.root_folder_path = check_for_attribute(config, "root_folder_path", parent="radarr")
            self.add_to_radarr = check_for_attribute(config, "add_to_radarr", parent="radarr", var_type="bool", default_is_none=True, do_print=False)
            self.search_movie = check_for_attribute(config, "search_movie", parent="radarr", var_type="bool", default=False, do_print=False)
        elif Radarr.valid is None:
            if TMDB.valid:
                print("| Connecting to Radarr...")
                fatal_message = ""
                message = ""
                try:
                    self.url = check_for_attribute(config, "url", parent="radarr", throw=True)
                except SystemExit as e:
                    fatal_message = fatal_message + "\n" + str(e) if len(fatal_message) > 0 else str(e)
                try:
                    self.version = check_for_attribute(config, "version", parent="radarr", test_list=["v2", "v3"], options="| \tv2 (For Radarr 0.2)\n| \tv3 (For Radarr 3.0)", default="v2", throw=True)
                except SystemExit as e:
                    message = message + "\n" + str(e) if len(message) > 0 else str(e)
                try:
                    self.token = check_for_attribute(config, "token", parent="radarr", throw=True)
                except SystemExit as e:
                    fatal_message = fatal_message + "\n" + str(e) if len(fatal_message) > 0 else str(e)
                try:
                    self.quality_profile_id = check_for_attribute(config, "quality_profile_id", parent="radarr", var_type="int", throw=True)
                except SystemExit as e:
                    fatal_message = fatal_message + "\n" + str(e) if len(fatal_message) > 0 else str(e)
                try:
                    self.root_folder_path = check_for_attribute(config, "root_folder_path", parent="radarr", throw=True)
                except SystemExit as e:
                    fatal_message = fatal_message + "\n" + str(e) if len(fatal_message) > 0 else str(e)
                try:
                    self.add_to_radarr = check_for_attribute(config, "add_to_radarr", parent="radarr", options="| \ttrue (Add missing movies to Radarr)\n| \tfalse (Do not add missing movies to Radarr)", var_type="bool", default_is_none=True, throw=True)
                except SystemExit as e:
                    message = message + "\n" + str(e) if len(message) > 0 else str(e)
                if "add_movie" in config:
                    try:
                        self.add_to_radarr = check_for_attribute(config, "add_movie", parent="radarr", var_type="bool", throw=True, save=False)
                        print("| Config Warning: replace add_movie with add_to_radarr")
                    except SystemExit as e:
                        pass
                try:
                    self.search_movie = check_for_attribute(config, "search_movie", parent="radarr", options="| \ttrue (Have Radarr seach the added movies)\n| \tfalse (Do not have Radarr seach the added movies)", var_type="bool", default=False, throw=True)
                except SystemExit as e:
                    message = message + "\n" + str(e) if len(message) > 0 else str(e)
                if len(fatal_message) > 0:
                    print(fatal_message + "\n" + message)
                    Radarr.valid = False
                else:
                    if len(message) > 0:
                        print(message)
                    try:
                        payload = {"qualityProfileId": self.quality_profile_id}
                        response = requests.post(self.url + ("/api/v3/movie" if self.version == "v3" else "/api/movie"), json=payload, params={"apikey": "{}".format(self.token)})
                        if response.json()[0]['errorMessage'] == "Profile does not exist":
                            sys.exit("| Config Error: radarr sub-attribute quality_profile_id: {} does not exist in radarr".format(self.quality_profile_id))
                        Radarr.valid = True
                    except SystemExit:
                        raise
                    except:
                        sys.exit("| Could not connect to Radarr at {}".format(self.url))
                print("| Radarr Connection {}".format("Successful" if Radarr.valid else "Failed"))
            else:
                print("| TMDb must be connected to use Radarr")
                Radarr.valid = False


class TMDB:
    valid = None
    def __init__(self, config_path):
        config = Config(config_path).tmdb
        if TMDB.valid:
            self.apikey = check_for_attribute(config, "apikey", parent="tmdb")
            self.language = check_for_attribute(config, "language", parent="tmdb", default="en", do_print=False)
        elif TMDB.valid is None:
            print("| Connecting to TMDb...")
            fatal_message = ""
            message = ""
            tmdb = Collection()
            try:
                self.apikey = check_for_attribute(config, "apikey", parent="tmdb", throw=True)
            except SystemExit as e:
                fatal_message = fatal_message + "\n" + str(e) if len(fatal_message) > 0 else str(e)
            try:
                self.language = check_for_attribute(config, "language", parent="tmdb", default="en", throw=True)
            except SystemExit as e:
                message = message + "\n" + str(e) if len(message) > 0 else str(e)
            if len(fatal_message) > 0:
                print(fatal_message + "\n" + message)
                TMDB.valid = False
            else:
                if len(message) > 0:
                    print(message)
                try:
                    tmdb.api_key = self.apikey
                    tmdb.details("100693").parts
                    TMDB.valid = True
                except AttributeError:
                    print("| Config Error: Invalid apikey")
                    TMDB.valid = False
            print("| TMDb Connection {}".format("Successful" if TMDB.valid else "Failed"))


class Tautulli:
    valid = None
    def __init__(self, config_path):
        config = Config(config_path).tautulli
        if Tautulli.valid:
            self.url = check_for_attribute(config, "url", parent="tautulli")
            self.apikey = check_for_attribute(config, "apikey", parent="tautulli")
        elif Tautulli.valid is None:
            print("| Connecting to tautulli...")
            message = ""
            try:
                self.url = check_for_attribute(config, "url", parent="tautulli", throw=True)
            except SystemExit as e:
                message = message + "\n" + str(e) if len(message) > 0 else str(e)
            try:
                self.apikey = check_for_attribute(config, "apikey", parent="tautulli", throw=True)
            except SystemExit as e:
                message = message + "\n" + str(e) if len(message) > 0 else str(e)
            if len(message) > 0:
                print(message)
                Tautulli.valid = False
            else:
                try:
                    stats = requests.get('{}/api/v2?apikey={}&cmd=get_home_stats&time_range=7'.format(self.url, self.apikey))
                    response = stats.json()
                    if response['response']['result'] == "success":
                        Tautulli.valid = True
                    else:
                        print("| Config Error: {}".format(response['response']['message']))
                        Tautulli.valid = False
                except:
                    print("| Config Error: Invalid url")
                    Tautulli.valid = False
            print("| tautulli Connection {}".format("Successful" if Tautulli.valid else "failed"))


class TraktClient:
    valid = None
    def __init__(self, config_path):
        config = Config(config_path).trakt
        if TraktClient.valid:
            self.client_id = check_for_attribute(config, "client_id", parent="trakt")
            self.client_secret = check_for_attribute(config, "client_secret", parent="trakt")
            self.auto_refresh_token = check_for_attribute(config, "auto_refresh_token", parent="trakt")
            self.authorization = config['authorization']
            Trakt.configuration.defaults.client(self.client_id, self.client_secret)
            Trakt.configuration.defaults.oauth.from_response(self.authorization)
        elif TraktClient.valid is None:
            print("| Connecting to Trakt...")
            fatal_message = ""
            try:
                self.client_id = check_for_attribute(config, "client_id", parent="trakt", throw=True)
            except SystemExit as e:
                fatal_message = fatal_message + "\n" + str(e) if len(fatal_message) > 0 else str(e)
            try:
                self.client_secret = check_for_attribute(config, "client_secret", parent="trakt", throw=True)
            except SystemExit as e:
                fatal_message = fatal_message + "\n" + str(e) if len(fatal_message) > 0 else str(e)
            try:
                self.auto_refresh_token = check_for_attribute(config, "auto_refresh_token", parent="trakt", var_type="bool", default=False)
            except SystemExit as e:
                fatal_message = fatal_message + "\n" + str(e) if len(fatal_message) > 0 else str(e)
            if len(fatal_message) > 0:
                print(fatal_message)
                TraktClient.valid = False
            else:
                Trakt.configuration.defaults.client(self.client_id, self.client_secret)
                if 'authorization' in config and config['authorization']:
                    self.authorization = config['authorization']
                else:
                    self.authorization = trakt_helpers.clear_authorization()
                if trakt_helpers.check_trakt(self.authorization):
                    # Initial authorization attempt
                    TraktClient.valid = True
                else:
                    # Try getting a new access_token from the refresh_token
                    if self.auto_refresh_token and self.authorization['refresh_token']:
                        self.refreshed_authorization = trakt_helpers.get_refreshed_authorization(self.authorization)
                    else:
                        self.refreshed_authorization = None
                    if trakt_helpers.check_trakt(self.refreshed_authorization):
                        # Save the refreshed authorization
                        trakt_helpers.save_authorization(Config(config_path).config_path, self.refreshed_authorization)
                        TraktClient.valid = True
                    else:
                        # Clear everything and re-auth
                        trakt_helpers.clear_authorization()
                        if Config.headless:
                            print("| Run without --update/-u to configure Trakt")
                            TraktClient.valid = False
                        else:
                            try:
                                self.updated_authorization = trakt_helpers.authenticate(self.authorization)
                                if trakt_helpers.check_trakt(self.updated_authorization):
                                    Trakt.configuration.defaults.oauth.from_response(self.updated_authorization)
                                    if self.updated_authorization != self.authorization:
                                        trakt_helpers.save_authorization(Config(config_path).config_path, self.updated_authorization)
                                    TraktClient.valid = True
                                else:
                                    TraktClient.valid = False
                                    print("| New Authorization Failed")
                            except SystemExit as e:
                                print(e)
                                TraktClient.valid = False
            print("| Trakt Connection {}".format("Successful" if TraktClient.valid else "Failed"))


class ImageServer:
    valid = None
    def __init__(self, config_path):
        config = Config(config_path).image_server
        app_dir = os.path.dirname(os.path.abspath(__file__))

        if config:
            input_poster = config['poster_directory'] if 'poster_directory' in config else None
            input_background = config['background_directory'] if 'background_directory' in config else None
            input_image = config['image_directory'] if 'image_directory' in config else None
            self.poster = input_poster if input_poster and os.path.exists(os.path.abspath(input_poster)) else None
            self.background = input_background if input_background and os.path.exists(os.path.abspath(input_background)) else None
            self.image = input_image if input_image and os.path.exists(os.path.abspath(input_image)) else None
        else:
            input_poster = None
            input_background = None
            input_image = None
            self.poster = "posters" if os.path.exists(os.path.join(app_dir, "posters")) else "..\\config\\posters" if os.path.exists(os.path.join(app_dir, "..", "config", "posters")) else None
            self.background = "backgrounds" if os.path.exists(os.path.join(app_dir, "backgrounds")) else "..\\config\\backgrounds" if os.path.exists(os.path.join(app_dir, "..", "config", "backgrounds")) else None
            self.image = "images" if os.path.exists(os.path.join(app_dir, "images")) else "..\\config\\images" if os.path.exists(os.path.join(app_dir, "..", "config", "images")) else None

        if ImageServer.valid is None:
            print("| Locating Image Server...")
            if "poster-directory" in config:
                print("| Config Error: Please change the poster-directory attribute to poster_directory")
            if config:
                def checkPath(attribute, path, type, input_directory, extra=None):
                    if path is None:
                        if input_directory is None:
                            print("| {} Directory was blank and defaults were not found".format(type))
                        else:
                            print("| {} Directory: {} not found".format(type, input_directory))
                    else:
                        abspath = os.path.abspath(path)
                        if attribute in config:
                            print("| Using {} for {} Directory".format(abspath, type) if os.path.exists(abspath) else "{} Directory not found: {}".format(type, abspath) if value else "{} attribute is empty".format(attribute))
                        elif extra and extra not in config:
                            print("| {} & {} attributes not found".format(attribute, extra))
                checkPath("poster_directory", self.poster, "Posters", input_poster, "image_directory")
                checkPath("background_directory", self.background, "Backgrounds", input_background, "image_directory")
                checkPath("image_directory", self.image, "Images", input_image)
            else:
                if self.poster:
                    print("| Using {} for posters directory".format(os.path.abspath(self.poster)))
                if self.background:
                    print("| Using {} for backgrounds directory".format(os.path.abspath(self.background)))
                if self.image:
                    print("| Using {} for images directory".format(os.path.abspath(self.image)))
                if not self.poster and not self.background and not self.image:
                    print("| Posters Directory not found: {} or {}".format(os.path.join(app_dir, "posters"), os.path.join(app_dir, "..", "config", "posters")))
                    print("| Backgrounds Directory not found: {} or {}".format(os.path.join(app_dir, "backgrounds"), os.path.join(app_dir, "..", "config", "backgrounds")))
                    print("| Images Directory not found: {} or {}".format(os.path.join(app_dir, "images"), os.path.join(app_dir, "..", "config", "images")))
            ImageServer.valid = True if self.poster or self.background or self.image else False


def modify_config(config_path, c_name, m, value):
    config = Config(config_path)
    if m == "movie":
        print("| Movies in config not supported yet")
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
