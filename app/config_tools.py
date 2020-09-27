# -*- coding: UTF-8 -*-
import os
import yaml
import requests
import socket
import urllib
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
    def __init__(self, config_path, mode="server"):
        config = Config(config_path).image_server
        # Best defaults for "host" are 0.0.0.0 for server and 127.0.0.1 for client
        # Set respective defaults in server and client
        if 'host' in config:
            self.host = config['host']
        else:
            if mode == "server":
                self.host = "0.0.0.0"
            else:
                self.host = "127.0.0.1"
        # Set default port
        if 'port' in config:
            self.port = config['port']
        else:
            self.port = 5000
        # Test and set default folder path
        if mode == "server":
            print("Attempting to find posters directory")
            
            if 'poster-directory' in config:
                self.posterdirectory = config['poster-directory']
            else:
                app_dir = os.path.dirname(os.path.realpath(__file__))

                # Test separate config directory with nested 'posters' directory
                if os.path.exists(os.path.join(app_dir, "..", "config", "posters")):
                    self.posterdirectory = os.path.join("..", "config", "posters")
                # Test separate config folder with nested 'images' directory
                elif os.path.exists(os.path.join(app_dir, "..", "config", "images")):
                    self.posterdirectory = os.path.join("..", "config", "images")            
                # Test nested posters directory
                elif os.path.exists(os.path.join(app_dir, "posters")):
                    self.posterdirectory = "posters"
                # Test nested images directory
                elif os.path.exists(os.path.join(app_dir, "images")):
                    self.posterdirectory = "images"
                else:
                    raise RuntimeError("Invalid poster-directory setting")
            
            print("Using {} as poster directory".format(self.posterdirectory))


def update_from_config(config_path, plex, headless=False):
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
                        elif "trakt" in m:
                            method_name = "Trakt"
                        else:
                            method_name = "TMDb"
                        print("{} missing movies from {} List: {}".format(len(missing), method_name, v))
                        if 'add_movie' in config.radarr:
                            if config.radarr['add_movie'] is True:
                                print("Adding missing movies to Radarr")
                                add_to_radarr(config_path, missing)
                        else:
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
            if headless is True: 
                plex_collection = get_collection(plex, c, True)
            elif headless is False:
                plex_collection = get_collection(plex, c, False)
            if not isinstance(plex_collection, Collections):
                # No collections created with requested criteria
                continue

            item = plex.Server.fetchItem(plex_collection.ratingKey)

            # Handle collection titleSort
            if "sort_title" in collections[c]["details"]:
                edits = {'titleSort.value': collections[c]["details"]["sort_title"], 'titleSort.locked': 1}
                item.edit(**edits)
                item.reload()

            # Handle collection contentRating
            if "content_rating" in collections[c]["details"]:
                edits = {'contentRating.value': collections[c]["details"]["content_rating"], 'contentRating.locked': 1}
                item.edit(**edits)
                item.reload()

            # Handle collection summary
            summary = None
            if "summary" in collections[c]["details"]:
                summary = collections[c]["details"]["summary"]
            elif "tmdb-summary" in collections[c]["details"]:
                # Seems clunky ...
                try:
                    summary = tmdb_get_summary(config_path, collections[c]["details"]["tmdb-summary"], "overview")
                except AttributeError:
                    summary = tmdb_get_summary(config_path, collections[c]["details"]["tmdb-summary"], "biography")
            if summary:
                edits = {'summary.value': summary, 'summary.locked': 1}
                item.edit(**edits)
                item.reload()

            # Handle collection posters
            poster = None
            if "poster" in collections[c]["details"]:
                poster = collections[c]["details"]["poster"]
            elif "tmdb-poster" in collections[c]["details"]:
                # Seems clunky ...
                try:
                    slug = tmdb_get_summary(config_path, collections[c]["details"]["tmdb-poster"], "poster_path")
                except AttributeError:
                    slug = tmdb_get_summary(config_path, collections[c]["details"]["tmdb-poster"], "profile_path")
                
                poster = "https://image.tmdb.org/t/p/original/" + slug
            else:
                # Try to pull image from image_server.
                # To do: this should skip if it's run without the image server
                # To do: this only runs if 'details' key is set - might make sense to run regardless
                # Setup connection to image_server
                config_client = ImageServer(config_path, "client")

                # Url encode collection name
                c_name = urllib.parse.quote(c, safe='')
                
                # Create local url to where image would be if exists
                local_poster_url = "http://" + config_client.host + ":" + str(config_client.port) + "/images/" + c_name
                
                # Test local url
                response = requests.head(local_poster_url)
                if response.status_code < 400:
                    poster = local_poster_url

            if poster:               
                item.uploadPoster(url=poster)

            # Handle collection backgrounds
            background = None
            if "background" in collections[c]["details"]:
                background = collections[c]["details"]["background"]
            else:
                # Try to pull image from image_server.
                # To do: this should skip if it's run without the image server
                # To do: this only runs if 'details' key is set - might make sense to run regardless
                # Setup connection to image_server
                config_client = ImageServer(config_path, "client")

                # Url encode collection name
                c_name = urllib.parse.quote(c, safe='')

                # Create local url to where image would be if exists
                local_background_url = "http://" + config_client.host + ":" + str(config_client.port) + "/images/" + c_name + "-background"

                # Test local url
                response = requests.head(local_background_url)
                if response.status_code < 400:
                    background = local_background_url

            if background:
                item.uploadArt(url=background)

            # Handle collection collectionMode
            if "collection_mode" in collections[c]["details"]:
                collectionMode = collections[c]["details"]["collection_mode"]
                if collectionMode in ('default', 'hide', 'hide_items', 'show_items'):
                    item.modeUpdate(mode=collectionMode)
                else:
                    print("collectionMode Invalid\ndefault (Library default)\nhide (Hide Collection)\nhideItems (Hide Items in this Collection)\nshowItems (Show this Collection and its Items)\n")

            # Handle collection collectionSort
            if "collection_sort" in collections[c]["details"]:
                collectionSort = collections[c]["details"]["collection_sort"]
                if collectionSort in ('release_date', 'alphabetical'):
                    item.sortUpdate(sort=collectionSort)
                else:
                    print("collectionSort Invalid\nrelease (Order Collection by release dates)\nalpha (Order Collection Alphabetically)\n")


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
