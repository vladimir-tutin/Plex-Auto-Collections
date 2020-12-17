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
from tmdbv3api import TMDb
from tmdbv3api import Movie as TMDb_Movie
import os
import sqlite3
import tempfile
import glob
import shutil
from contextlib import closing


def adjust_space(old_length, display_title):
    display_title = str(display_title)
    space_length = old_length - len(display_title)
    if space_length > 0:
        display_title += " " * space_length
    return display_title

def get_item(plex, data):
    if isinstance(data, int) or isinstance(data, Movie) or isinstance(data, Show):
        try:
            return plex.Server.fetchItem(data.ratingKey if isinstance(data, Movie) or isinstance(data, Show) else data)
        except PlexExceptions.BadRequest:
            return "Nothing found"
    else:
        item_list = plex.Library.search(title=data)
        if item_list:
            return item_list
        else:
            return "Item: {} not found".format(data)

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

def get_map(config_path, plex):
    plex_map = {}
    current_length = 0
    current_count = 0
    if TMDB.valid:
        tmdb = TMDb()
        tmdb.api_key = TMDB(config_path).apikey
        tmovie = TMDb_Movie()
    print("|")
    if plex.library_type == "movie":
        config_dir = os.path.dirname(config_path)
        db_dir = os.path.join(config_dir, 'db')
        guid_map = os.path.join(db_dir, "{}_guid.db".format(os.path.splitext(os.path.basename(config_path))[0]))    
        if not os.path.isfile(guid_map):
            create_guid_map(config_path)
            update_guid_map_from_db(config_path, plex)
    print("| Mapping Plex {}".format("Movies" if plex.library_type == "movie" else "Shows"))
    plex_items = plex.Library.all()
    try:
        for item in plex_items:
            current_count += 1
            print_display = "| Processing: {}/{} {}".format(current_count, len(plex_items), item.title)
            print(adjust_space(current_length, print_display), end="\r")
            current_length = len(print_display)
            update = None
            key_id = None
            error_message = "Unable to map {} ID".format("TMDb/IMDb" if plex.library_type == "movie" else "TVDb")

            guid = urlparse(item.guid)
            item_type = guid.scheme.split('.')[-1]
            check_id = guid.netloc
            if item_type == 'plex' and plex.library_type == "movie":
                # Check GUID map for TMDb ID
                key_id = query_guid_map(config_path, item.guid, 'tmdb_id')
                # Check GUID map for for IMDb ID
                if not key_id:
                    key_id = query_guid_map(config_path, item.guid, 'imdb_id')
                if not key_id:
                    imdb_id, tmdb_id = alt_id_lookup(plex, item)
                    if tmdb_id:
                        key_id = tmdb_id
                        print(adjust_space(current_length, "| Cache | {} | {:<46} | {:<6} | {}".format("^" if update == True else "+", item.guid, key_id, item.title)))
                        update_guid_map(config_path, item.guid, tmdb_id=key_id)
                    elif imdb_id:
                        key_id = imdb_id
                        print(adjust_space(current_length, "| Cache | {} | {:<46} | {:<6} | {}".format("^" if update == True else "+", item.guid, key_id, item.title)))
                        update_guid_map(config_path, item.guid, imdb_id=key_id)
            elif item_type == 'imdb' and plex.library_type == "movie":
                key_id = None
                if TMDB.valid and key_id is None:
                    key_id = imdb_tools.imdb_get_tmdb(config_path, check_id)
                if TraktClient.valid and key_id is None:
                    key_id = trakt_tools.trakt_imdb_to_tmdb(config_path, check_id)
                if key_id is None:
                    if TMDB.valid and TraktClient.valid:
                        error_message = "Unable to convert IMDb ID: {} to TMDb ID using TMDb or Trakt".format(check_id)
                    elif TMDB.valid:
                        error_message = "Unable to convert IMDb ID: {} to TMDb ID using TMDb".format(check_id)
                    elif TraktClient.valid:
                        error_message = "Unable to convert IMDb ID: {} to TMDb ID using Trakt".format(check_id)
                    else:
                        error_message = "Configure TMDb or Trakt to covert IMDb ID: {} to TMDb ID".format(check_id)
            elif item_type == 'themoviedb' and plex.library_type == "movie":
                tmdbapi = tmovie.details(check_id)
                if hasattr(tmdbapi, 'id'):
                    key_id = tmdbapi.id
                else:
                    key_id = None
                    error_message = "TMDb ID: {} Invalid".format(check_id)
            elif item_type == 'thetvdb' and plex.library_type == "show":
                key_id = check_id
            elif item_type == 'themoviedb' and plex.library_type == "show":
                key_id = None
                if TMDB.valid and key_id is None:
                    key_id = imdb_tools.tmdb_get_tvdb(config_path, check_id)
                if TraktClient.valid and key_id is None:
                    key_id = trakt_tools.trakt_tmdb_to_tvdb(config_path, check_id)
                if key_id is None:
                    if TMDB.valid and TraktClient.valid:
                        error_message = "Unable to convert TMDb ID: {} to TVDb ID using TMDb or Trakt".format(check_id)
                    elif TMDB.valid:
                        error_message = "Unable to convert TMDb ID: {} to TVDb ID using TMDb".format(check_id)
                    elif TraktClient.valid:
                        error_message = "Unable to convert TMDb ID: {} to TVDb ID using Trakt".format(check_id)
                    else:
                        error_message = "Configure TMDb or Trakt to covert TMDb ID: {} to TVDb ID".format(check_id)
            elif item_type == "local":
                key_id = None
                error_message = "No match in Plex"
            else:
                key_id = None
                error_message = "Agent {} not supported".format(item_type)
            if key_id:
                plex_map[key_id] = item.ratingKey
            else:
                print(adjust_space(current_length, "| {} {:<46} | {} for {}".format("Cache | ! |", item.guid, error_message, item.title)))
        print(adjust_space(current_length, "| Processed {} {}".format(len(plex_items), "Movies" if plex.library_type == "movie" else "Shows")))
    except:
        print()
        raise
    return plex_map

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
                        raise ValueError("No collection selected")
                    else:
                        print("| Invalid entry")
                except (IndexError, ValueError) as E:
                    print("| Invalid entry")
    elif len(collection_list) == 1 and (exact is None or collection_list[0].title == data):
        return collection_list[0]
    else:
        raise ValueError("Collection {} Not Found".format(data))

def add_to_collection(config_path, plex, method, value, c, plex_map=None, map=None, filters=None):
    if plex_map is None and ("imdb" in method or "tvdb" in method or "tmdb" in method or "trakt" in method):
        plex_map = get_map(config_path, plex)
    if map is None:
        map = {}
    items = []
    missing = []

    if method == "all":
        items = plex.Library.all()
    elif method == "plex_collection":
        items = value.children
    elif method == "plex_search":
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
        items = plex.Library.search(**search_terms)
    elif method == "tvdb_show" and plex.library_type == "show":
        items, missing = imdb_tools.tvdb_get_shows(config_path, plex, plex_map, value)
    elif "imdb" in method or "tmdb" in method:
        if not TMDB.valid:
            raise KeyError("| tmdb connection required for {}",format(method))
        elif method == "imdb_list" and plex.library_type == "movie":
            items, missing = imdb_tools.imdb_get_movies(config_path, plex, plex_map, value)
        elif "tmdb" in method and plex.library_type == "movie":
            items, missing = imdb_tools.tmdb_get_movies(config_path, plex, plex_map, value, method)
        elif "tmdb" in method and plex.library_type == "show":
            items, missing = imdb_tools.tmdb_get_shows(config_path, plex, plex_map, value, method)
    elif "trakt" in method:
        if not TraktClient.valid:
            raise KeyError("| trakt connection required for {}",format(method))
        elif plex.library_type == "movie":
            items, missing = trakt_tools.trakt_get_movies(config_path, plex, plex_map, value, method)
        elif plex.library_type == "show":
            items, missing = trakt_tools.trakt_get_shows(config_path, plex, plex_map, value, method)
    elif method == "tautulli":
        if not Tautulli.valid:
            raise KeyError("| tautulli connection required for {}",format(method))
        else:
            items, missing = imdb_tools.get_tautulli(config_path, plex, value)
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
        "plex_collection": "collections",
    }

    if items:
        # Check if already in collection
        cols = plex.Library.search(title=c, libtype="collection")
        try:
            fs = cols[0].children
        except IndexError:
            fs = []
        item_count = 0
        item_max = len(items)
        max_str_len = len(str(item_max))
        current_length = 0
        for rk in items:
            current_item = get_item(plex, rk)
            item_count += 1
            match = True
            if filters:
                display_count = (" " * (max_str_len - len(str(item_count)))) + str(item_count)
                print_display = "| Filtering {}/{} {}".format(display_count, item_max, current_item.title)
                print(adjust_space(current_length, print_display), end = "\r")
                current_length = len(print_display)
                for f in filters:
                    modifier = f[0][-4:]
                    method = filter_alias[f[0][:-4]] if modifier in [".not", ".lte", ".gte"] else filter_alias[f[0]]
                    if method == "max_age":
                        threshold_date = datetime.now() - timedelta(days=f[1])
                        attr = getattr(current_item, "originallyAvailableAt")
                        if attr is None or attr < threshold_date:
                            match = False
                            break
                    elif modifier in [".gte", ".lte"]:
                        if method == "originallyAvailableAt":
                            threshold_date = datetime.strptime(f[1], "%m/%d/%y")
                            attr = getattr(current_item, "originallyAvailableAt")
                            if (modifier == ".lte" and attr > threshold_date) or (modifier == ".gte" and attr < threshold_date):
                                match = False
                                break
                        elif method in ["year", "rating"]:
                            attr = getattr(current_item, method)
                            if (modifier == ".lte" and attr > f[1]) or (modifier == ".gte" and attr < f[1]):
                                match = False
                                break
                    else:
                        terms = f[1] if isinstance(f[1], list) else str(f[1]).split(", ")
                        if method in ["video_resolution", "audio_language", "subtitle_language"]:
                            for media in current_item.media:
                                if method == "video_resolution":
                                    attrs = [media.videoResolution]
                                for part in media.parts:
                                    if method == "audio_language":
                                        attrs = ([audio_stream.language for audio_stream in part.audioStreams()])
                                    if method == "subtitle_language":
                                        attrs = ([subtitle_stream.language for subtitle_stream in part.subtitleStreams()])
                        elif method in ["contentRating", "studio", "year", "rating", "originallyAvailableAt"]:                    # Otherwise, it's a string. Make it a list.
                            attrs = [str(getattr(current_item, method))]
                        elif method in ["actors", "countries", "directors", "genres", "writers", "collections"]:
                            attrs = [getattr(x, 'tag') for x in getattr(current_item, method)]

                        # Get the intersection of the user's terms and item's terms
                        # If it's empty and modifier is not .not, it's not a match
                        # If it's not empty and modifier is .not, it's not a match
                        if (not list(set(terms) & set(attrs)) and modifier != ".not") or (list(set(terms) & set(attrs)) and modifier == ".not"):
                            match = False
                            break
            if match:
                if current_item in fs:
                    map[current_item.ratingKey] = None
                else:
                    current_item.addCollection(c)
                print(adjust_space(current_length, "| {} Collection | {} | {}".format(c, "=" if current_item in fs else "+", current_item.title)))
        print(adjust_space(current_length, "| Processed {} {}".format(item_max, "Movies" if plex.library_type == "movie" else "Shows")))
    else:
        print("| No {} Found".format("Movies" if plex.library_type == "movie" else "Shows"))

    return missing, map

def delete_collection(data):
    confirm = input("| {} selected. Confirm deletion (y/n):".format(data.title))
    if confirm == "y":
        data.delete()
        print("| Collection deleted")

def alt_id_lookup(plex, movie):
    req = Request('{}{}'.format(plex.url, movie.key))
    req.add_header('X-Plex-Token', plex.token)
    req.add_header('User-Agent', 'Mozilla/5.0')
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

def create_guid_map(config_path):
    config_dir = os.path.dirname(config_path)
    db_dir = os.path.join(config_dir, 'db')
    os.makedirs(db_dir, exist_ok=True)
    guid_map = os.path.join(db_dir, "{}_guid.db".format(os.path.splitext(os.path.basename(config_path))[0]))
    with closing(sqlite3.connect(guid_map)) as connection:
        connection.row_factory = sqlite3.Row
        with closing(connection.cursor()) as cursor:
            cursor.execute(''' SELECT count(name) FROM sqlite_master WHERE type='table' AND name='guids' ''')
            if cursor.fetchone()[0] != 1:
                print("| Initializing GUID map database at {}".format(guid_map))
                cursor.execute('CREATE TABLE IF NOT EXISTS guids (plex_guid TEXT PRIMARY KEY, imdb_id TEXT, tmdb_id TEXT, updated TEXT)')
            else:
                print("| Using GUID map database at {}".format(guid_map))

def update_guid_map_from_db(config_path, plex):
    config_dir = os.path.dirname(config_path)
    temp_dir = tempfile.mkdtemp(dir=config_dir)
    print("| Downloading temporary database to {}".format(temp_dir))
    plex.Server.downloadDatabases(savepath=temp_dir, unpack=True)
    os.remove(glob.glob(os.path.join(temp_dir, '*.zip'))[0])
    plex_temp_db = glob.glob(os.path.join(temp_dir, '*'))[0]
    print("| Updating GUID map from database")
    with closing(sqlite3.connect(plex_temp_db)) as connection:
        connection.row_factory = sqlite3.Row
        with closing(connection.cursor()) as cursor:
            for row in cursor.execute(
                    '''SELECT t.tag, mdi.guid, mdi.title, mdi.year
                    FROM metadata_items mdi
                    JOIN taggings tg
                    ON tg.metadata_item_id = mdi.id
                    JOIN tags t
                    ON t.id = tg.tag_id
                    AND t.tag_type = 314
                    WHERE mdi.metadata_type = 1
                    AND mdi.library_section_id = ?
                    AND (t.tag LIKE 'tmdb://%'
                    OR t.tag LIKE 'imdb://%')
                    GROUP BY mdi.id, t.tag''', (plex.Library.key, )):
                if 'imdb' in row['tag']:
                    update_guid_map(config_path, row['guid'], imdb_id=urlparse(row['tag']).netloc)
                elif 'tmdb' in row['tag']:
                    update_guid_map(config_path, row['guid'], tmdb_id=urlparse(row['tag']).netloc)
                print("| GUID map | + | {:38} | {:<9} | {} ({})".format(row['guid'], urlparse(row['tag']).netloc, row['title'], row['year']))
    shutil.rmtree(temp_dir)


def query_guid_map(config_path, key, column):
    config_dir = os.path.dirname(config_path)
    db_dir = os.path.join(config_dir, 'db')
    guid_map = os.path.join(db_dir, "{}_guid.db".format(os.path.splitext(os.path.basename(config_path))[0]))
    with closing(sqlite3.connect(guid_map)) as connection:
        connection.row_factory = sqlite3.Row
        with closing(connection.cursor()) as cursor:
            cursor.execute("SELECT * FROM guids WHERE plex_guid = ?", (key, ))
            row = cursor.fetchone()
            if row:
                return row[column]

def update_guid_map(config_path, plex_guid, **kwargs):
    config_dir = os.path.dirname(config_path)
    db_dir = os.path.join(config_dir, 'db')
    guid_map = os.path.join(db_dir, "{}_guid.db".format(os.path.splitext(os.path.basename(config_path))[0]))
    with closing(sqlite3.connect(guid_map)) as connection:
        connection.row_factory = sqlite3.Row
        with closing(connection.cursor()) as cursor:
            cursor.execute('INSERT OR IGNORE INTO guids(plex_guid) VALUES(?)', (plex_guid, ))
            if 'imdb_id' in kwargs:
                imdb_id = kwargs['imdb_id']
                cursor.execute('INSERT OR IGNORE INTO guids(plex_guid, imdb_id, updated) VALUES(?, ?, ?)', (plex_guid, imdb_id, datetime.now()))
                cursor.execute('UPDATE guids SET imdb_id = ?, updated = ? WHERE plex_guid = ?', (imdb_id, datetime.now(), plex_guid))
            if 'tmdb_id' in kwargs:
                tmdb_id = kwargs['tmdb_id']
                cursor.execute('INSERT OR IGNORE INTO guids(plex_guid, tmdb_id, updated) VALUES(?, ?, ?)', (plex_guid, tmdb_id, datetime.now()))
                cursor.execute('UPDATE guids SET tmdb_id = ?, updated = ? WHERE plex_guid = ?', (tmdb_id, datetime.now(), plex_guid))
        connection.commit()