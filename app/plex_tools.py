from plexapi.video import Movie
from plexapi.video import Show
from plexapi import exceptions as PlexExceptions
from plexapi.library import MovieSection
from plexapi.library import ShowSection
from datetime import datetime, timedelta
import imdb_tools
import trakt_tools
from config_tools import Config
from config_tools import TMDB
from config_tools import TraktClient
from config_tools import Tautulli
from bs4 import BeautifulSoup
from urllib.request import Request
from urllib.request import urlopen
from urllib.parse import urlparse
import os
import sqlite3


def get_movie(plex, data):
    # If an int is passed as data, assume it is a movie's rating key
    if isinstance(data, int):
        try:
            return plex.Server.fetchItem(data)
        except PlexExceptions.BadRequest:
            print("| Nothing found")
            return None
    elif isinstance(data, Movie):
        return data
    else:
        movie_list = plex.Library.search(title=data)
        if movie_list:
            return movie_list
        else:
            print("| Movie: {} not found".format(data))
            return None

def get_item(plex, data):
    # If an int is passed as data, assume it is a movie's rating key
    if isinstance(data, int):
        try:
            return plex.Server.fetchItem(data)
        except PlexExceptions.BadRequest:
            return "Nothing found"
    elif isinstance(data, Movie):
        return data
    elif isinstance(data, Show):
        return data
    else:
        print(data)
        item_list = plex.Library.search(title=data)
        if item_list:
            return item_list
        else:
            return "Item: " + data + " not found"

def get_actor_rkey(plex, data):
    """Takes in actors name as str and returns as Plex's corresponding rating key ID"""
    search = data

    # We must first perform standard search against the Plex Server
    # Searching in the Library via Actor only works if the ratingKey is already known
    results = plex.Server.search(search)

    for entry in results:
        entry = str(entry)
        entry = entry.split(":")
        entry[0] = entry[0][1:]
        if entry[0] == "Movie":
            movie_id = int(entry[1])
            break
    try:
        # We need to pull details from a movie to correspond the actor's name to their Plex Rating Key
        movie_roles = plex.Server.fetchItem(movie_id).roles
        for role in movie_roles:
            role = str(role).split(":")
            movie_actor_id = role[1]
            movie_actor_name = role[2][:-1].upper()
            if search.upper().replace(" ", "-") == movie_actor_name:
                actor_id = movie_actor_id
        return int(actor_id)
    except UnboundLocalError:
        raise ValueError("| Config Error: Actor: {} not found".format(search))

# subtype can be 'movie', 'show', or None (movie/tv combined)
def get_collection(plex, data, exact=None, subtype=None):
    collection_list = plex.Library.search(title=data, libtype="collection")
    if len(collection_list) > 1:
        for collection in collection_list:
            if collection.title == data:
                return collection
        if not exact:
            c_names = ["| " + (str(i + 1) + ") " + collection.title + " (" + collection.subtype + ")") for i, collection in enumerate(collection_list)]
            print("| 0) Do Nothing")
            print("\n".join(c_names))
            while True:
                try:
                    selection = int(input("| Choose collection number: ")) - 1
                    if selection >= 0:
                        return collection_list[selection]
                    elif selection == -1:
                        return "No collection selected"
                    else:
                        print("| Invalid entry")
                except (IndexError, ValueError) as E:
                    print("| Invalid entry")
    elif len(collection_list) == 1:
        if exact:
            # if collection_list[0] == data:
            if collection_list[0].title == data:
                return collection_list[0]
            else:
                return "Collection not in Plex, please update from config first"
        else:
            return collection_list[0]
    else:
        return "No collection found"

def add_to_collection(config_path, plex, method, value, c, map, filters=None):
    movies = []
    shows = []
    items = []
    missing = []
    def search_plex():
        search_terms = {}
        output = ""
        for attr_pair in value:
            if attr_pair[0] == "actor":
                search_list = []
                for actor in attr_pair[1]:
                    search_list.append(get_actor_rkey(plex, actor))
            else:
                search_list = attr_pair[1]
            final_method = attr_pair[0][:-4] + "!" if attr_pair[0][-4:] == ".not" else attr_pair[0]
            if plex.library_type == "show":
                final_method = "show." + final_method
            search_terms[final_method] = search_list
            ors = ""
            for param in attr_pair[1]:
                ors = ors + (" OR " if len(ors) > 0 else attr_pair[0] + "(") + str(param)
            output = output + ("\n|\t\t      AND " if len(output) > 0 else "| Processing Plex Search: ") + ors + ")"
        print(output)
        return plex.Library.search(**search_terms)

    if ("trakt" in method or (("tmdb" in method or "tvdb" in method) and plex.library_type == "show")) and not TraktClient.valid:
        raise KeyError("| trakt connection required for {}",format(method))
    elif ("imdb" in method or "tmdb" in method) and not TMDB.valid:
        raise KeyError("| tmdb connection required for {}",format(method))
    elif method == "tautulli" and not Tautulli.valid:
        raise KeyError("| tautulli connection required for {}",format(method))
    elif plex.library_type == "movie":
        if method == "imdb_list":
            movies, missing = imdb_tools.imdb_get_movies(config_path, plex, value)
        elif method in ["tmdb_list", "tmdb_id", "tmdb_movie", "tmdb_collection", "tmdb_company"]:
            movies, missing = imdb_tools.tmdb_get_movies(config_path, plex, value, method)
        elif method == "trakt_list":
            movies, missing = trakt_tools.trakt_get_movies(config_path, plex, value)
        elif method == "trakt_trending":
            movies, missing = trakt_tools.trakt_get_movies(config_path, plex, value, is_userlist=False)
        elif method == "tautulli":
            movies, missing = imdb_tools.get_tautulli(config_path, plex, value)
        elif method == "all":
            movies = plex.Library.all()
        elif method == "plex_search":
            movies = search_plex()
        else:
            print("| Config Error: {} method not supported".format(method))
    elif plex.library_type == "show":
        if method == "tmdb_list":
            shows, missing = imdb_tools.tmdb_get_shows(config_path, plex, value, is_list=True)
        elif method in ["tmdb_id", "tmdb_show"]:
            shows, missing = imdb_tools.tmdb_get_shows(config_path, plex, value)
        elif method == "tvdb_show":
            shows, missing = imdb_tools.tvdb_get_shows(config_path, plex, value)
        elif method == "trakt_list":
            shows, missing = trakt_tools.trakt_get_shows(config_path, plex, value)
        elif method == "trakt_trending":
            shows, missing = trakt_tools.trakt_get_shows(config_path, plex, value, is_userlist=False)
        elif method == "tautulli":
            shows, missing = imdb_tools.get_tautulli(config_path, plex, value)
        elif method == "all":
            shows = plex.Library.all()
        elif method == "plex_search":
            shows = search_plex()
        else:
            print("| Config Error: {} method not supported".format(method))

    filter_alias = {
        "actor": "actors",
        "content_rating": "contentRating",
        "country": "countries",
        "director": "directors",
        "genre": "genres",
        "studio": "studio",
        "year": "year",
        "writer": "writers",
        "rating": "rating",
        "max_age": "max_age",
        "originally_available": "originallyAvailableAt",
        "video_resolution": "video_resolution",
        "audio_language": "audio_language",
        "subtitle_language": "subtitle_language",
    }

    if movies:
        # Check if already in collection
        cols = plex.Library.search(title=c, libtype="collection")
        try:
            fs = cols[0].children
        except IndexError:
            fs = []
        for rk in movies:
            current_m = get_movie(plex, rk)
            current_m.reload()
            match = True
            print(f'\r| Filtering {current_m.title}                                                                ', end = "\r")
            if filters:
                for f in filters:
                    modifier = f[0][-4:]
                    method = filter_alias[f[0][:-4]] if modifier in [".not", ".lte", ".gte"] else filter_alias[f[0]]
                    if method == "max_age":
                        threshold_date = datetime.now() - timedelta(days=f[1])
                        attr = getattr(current_m, "originallyAvailableAt")
                        if attr is None or attr < threshold_date:
                            match = False
                            break
                    elif modifier in [".gte", ".lte"]:
                        if method == "originallyAvailableAt":
                            threshold_date = datetime.strptime(f[1], "%m/%d/%y")
                            attr = getattr(current_m, "originallyAvailableAt")
                            if (modifier == ".lte" and attr > threshold_date) or (modifier == ".gte" and attr < threshold_date):
                                match = False
                                break
                        elif method in ["year", "rating"]:
                            attr = getattr(current_m, method)
                            if (modifier == ".lte" and attr > f[1]) or (modifier == ".gte" and attr < f[1]):
                                match = False
                                break
                    else:
                        terms = f[1] if isinstance(f[1], list) else str(f[1]).split(", ")
                        if method in ["video_resolution", "audio_language", "subtitle_language"]:
                            for media in current_m.media:
                                if method == "video_resolution":
                                    mv_attrs = [media.videoResolution]
                                for part in media.parts:
                                    if method == "audio_language":
                                        mv_attrs = ([audio_stream.language for audio_stream in part.audioStreams()])
                                    if method == "subtitle_language":
                                        mv_attrs = ([subtitle_stream.language for subtitle_stream in part.subtitleStreams()])
                        elif method in ["contentRating", "studio", "year", "rating", "originallyAvailableAt"]:                    # Otherwise, it's a string. Make it a list.
                            mv_attrs = [str(getattr(current_m, method))]
                        elif method in ["actors", "countries", "directors", "genres", "writers"]:
                            mv_attrs = [getattr(x, 'tag') for x in getattr(current_m, method)]

                        # Get the intersection of the user's terms and movie's terms
                        # If it's empty and modifier is not .not, it's not a match
                        # If it's not empty and modifier is .not, it's not a match
                        if (not list(set(terms) & set(mv_attrs)) and modifier != ".not") or (list(set(terms) & set(mv_attrs)) and modifier == ".not"):
                            match = False
                            break
            if match:
                if current_m in fs:
                    print(f'\r| {c} Collection | = | {current_m.title}                                                                ', end = "\r")
                    map[current_m.ratingKey] = None
                else:
                    print(f'\r| {c} Collection | + | {current_m.title}                                                                ', end = "\r")
                    current_m.addCollection(c)
                print()
    elif plex.library_type == "movie":
        print("| No movies found")

    if shows:
        # Check if already in collection
        cols = plex.Library.search(title=c, libtype="collection")
        try:
            fs = cols[0].children
        except IndexError:
            fs = []
        for rk in shows:
            current_s = get_item(plex, rk)
            current_s.reload()
            match = True
            print(f'\r| Filtering {current_s.title}                                                                ', end = "\r")
            if filters:
                for f in filters:
                    modifier = f[0][-4:]
                    method = filter_alias[f[0][:-4]] if modifier in [".not", ".lte", ".gte"] else filter_alias[f[0]]
                    if method == "max_age":
                        threshold_date = datetime.now() - timedelta(days=f[1])
                        attr = getattr(current_s, "originallyAvailableAt")
                        if attr is None or attr < threshold_date:
                            match = False
                            break
                    elif modifier in [".gte", ".lte"]:
                        if method == "originallyAvailableAt":
                            threshold_date = datetime.strptime(f[1], "%m/%d/%y")
                            attr = getattr(current_s, "originallyAvailableAt")
                            if (modifier == ".lte" and attr > threshold_date) or (modifier == ".gte" and attr < threshold_date):
                                match = False
                                break
                        elif method in ["year", "rating"]:
                            attr = getattr(current_s, method)
                            if (modifier == ".lte" and attr > f[1]) or (modifier == ".gte" and attr < f[1]):
                                match = False
                                break
                    else:
                        terms = f[1] if isinstance(f[1], list) else str(f[1]).split(", ")
                        # if method in ["video_resolution", "audio_language", "subtitle_language"]:
                        #     for media in current_s.media:
                        #         if method == "video_resolution":
                        #             show_attrs = [media.videoResolution]
                        #         for part in media.parts:
                        #             if method == "audio_language":
                        #                 show_attrs = ([audio_stream.language for audio_stream in part.audioStreams()])
                        #             if method == "subtitle_language":
                        #                 show_attrs = ([subtitle_stream.language for subtitle_stream in part.subtitleStreams()])
                        if method in ["contentRating", "studio", "year", "rating", "originallyAvailableAt"]:
                            mv_attrs = [str(getattr(current_s, method))]
                        elif method in ["actors", "genres"]:
                            mv_attrs = [getattr(x, 'tag') for x in getattr(current_s, method)]

                        # Get the intersection of the user's terms and movie's terms
                        # If it's empty and modifier is not .not, it's not a match
                        # If it's not empty and modifier is .not, it's not a match
                        if (not list(set(terms) & set(show_attrs)) and modifier != ".not") or (list(set(terms) & set(show_attrs)) and modifier == ".not"):
                            match = False
                            break
            if match:
                if current_s in fs:
                    print(f'\r| {c} Collection | = | {current_s.title}                                                                ', end = "\r")
                    map[current_s.ratingKey] = None
                else:
                    print(f'\r| {c} Collection | + | {current_s.title}                                                                ', end = "\r")
                    current_s.addCollection(c)
                print()
    elif plex.library_type == "show":
        print("| No shows found")

    try:
        missing
    except UnboundLocalError:
        return
    else:
        return missing, map

def delete_collection(data):
    confirm = input("| {} selected. Confirm deletion (y/n):".format(data.title))
    if confirm == "y":
        data.delete()
        print("| Collection deleted")

def alt_id_lookup(plex, value):
    req = Request('{}{}'.format(plex.url, value.key))
    req.add_header('X-Plex-Token', plex.token)
    with urlopen(req) as response:
        contents = response.read()
    bs = BeautifulSoup(contents, 'lxml')
    imdb_id = None
    tmdb_id = None
    for guid_tag in bs.find_all('guid'):
        agent = urlparse(guid_tag['id']).scheme
        guid = urlparse(guid_tag['id']).netloc
        if agent == 'imdb':
            imdb_id = guid
        elif agent == 'tmdb':
            tmdb_id = guid
    return imdb_id, tmdb_id

def create_cache(config_path):
    cache = os.path.join(os.path.dirname(config_path), 'cache.db')
    connection = sqlite3.connect(cache)
    with sqlite3.connect(cache) as connection:
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()
        cursor.execute(''' SELECT count(name) FROM sqlite_master WHERE type='table' AND name='guids' ''')
        if cursor.fetchone()[0] != 1:
            print("| Initializing cache database.".format(cache))
            cursor.execute('CREATE TABLE IF NOT EXISTS guids (plex_guid TEXT PRIMARY KEY, imdb_id TEXT, tmdb_id TEXT)')

def query_cache(config_path, key, column):
    cache = os.path.join(os.path.dirname(config_path), 'cache.db')
    with sqlite3.connect(cache) as connection:
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM guids WHERE plex_guid = ?", (key, ))
        row = cursor.fetchone()
        if row:
            return row[column]

def update_cache(config_path, plex_guid, **kwargs):
    cache = os.path.join(os.path.dirname(config_path), 'cache.db')
    with sqlite3.connect(cache) as connection:
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()
        if 'imdb_id' in kwargs:
            imdb_id = kwargs['imdb_id']
            cursor.execute('INSERT OR IGNORE INTO guids(plex_guid, imdb_id) VALUES(?, ?)', (plex_guid, imdb_id, ))
            cursor.execute('UPDATE guids SET imdb_id = ? WHERE plex_guid = ?', (imdb_id, plex_guid))
        if 'tmdb_id' in kwargs:
            tmdb_id = kwargs['tmdb_id']
            cursor.execute('INSERT OR IGNORE INTO guids(plex_guid, tmdb_id) VALUES(?, ?)', (plex_guid, tmdb_id, ))
            cursor.execute('UPDATE guids SET tmdb_id = ? WHERE plex_guid = ?', (tmdb_id, plex_guid))
