from plexapi.video import Movie
from plexapi.video import Show
from plexapi import exceptions as PlexExceptions
from plexapi.library import MovieSection
from plexapi.library import ShowSection
import imdb_tools
import trakt_tools
from config_tools import Config
from config_tools import TMDB
from config_tools import TraktClient


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
            print("| Movie: " + data + " not found")
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
        return "Actor: " + search + " not found"

def get_all_items(plex):
    return plex.Library.all()

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

def add_to_collection(config_path, plex, method, value, c, subfilters=None):
    movies = []
    shows = []
    items = []
    if method in Movie.__doc__ or hasattr(Movie, method):
        try:
            movies = plex.Library.search(**{method: value})
        except PlexExceptions.BadRequest:
            # If last character is "s" remove it and try again
            if method[-1:] == "s":
                movies = plex.Library.search(**{method[:-1]: value})
                movies = [m.ratingKey for m in movies if movies]
    elif method in Show.__doc__ or hasattr(Show, method):
        try:
            shows = plex.Library.search(**{method: value})
        except PlexExceptions.BadRequest as e:
            print(e)
    else:
        if isinstance(plex.Library, MovieSection):
            config = Config(config_path)
            if method == "imdb_list":
                if TMDB.valid:                  movies, missing = imdb_tools.imdb_get_movies(config_path, plex, value)
                else:                           print("| tmdb connection required")
            elif method == "tmdb_list":
                if TMDB.valid:                  movies, missing = imdb_tools.tmdb_get_movies(config_path, plex, value)
                else:                           print("| tmdb connection required")
            elif method == "trakt_list":
                if TraktClient.valid:           movies, missing = trakt_tools.trakt_get_movies(config_path, plex, value)
                else:                           print("| trakt connection required")
        elif isinstance(plex.Library, ShowSection):
            if method == "trakt_list":
                if TraktClient.valid:           shows, missing = trakt_tools.trakt_get_shows(config_path, plex, value)
                else:                           print("| trakt connection required")

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
            if current_m in fs:
                print("| {} Collection already contains: {}".format(c, current_m.title))
            elif subfilters:
                match = True
                for sf in subfilters:
                    method = sf[0]
                    terms = str(sf[1]).split(", ")
                    try:
                        mv_attrs = getattr(current_m, method)
                        # If it returns a list, get the 'tag' attribute
                        # Otherwise, it's a string. Make it a list.
                        if isinstance(mv_attrs, list) and "-" not in method:
                            mv_attrs = [getattr(x, 'tag') for x in mv_attrs]
                        else:
                            mv_attrs = [str(mv_attrs)]
                    except AttributeError:
                        for media in current_m.media:
                            if method == "video_resolution":
                                mv_attrs = [media.videoResolution]
                            for part in media.parts:
                                if method == "audio_language":
                                    mv_attrs = ([audio_stream.language for audio_stream in part.audioStreams()])
                                if method == "subtitle_language":
                                    mv_attrs = ([subtitle_stream.language for subtitle_stream in part.subtitleStreams()])

                    # Get the intersection of the user's terms and movie's terms
                    # If it's empty, it's not a match
                    if not list(set(terms) & set(mv_attrs)):
                        match = False
                        break
                if match:
                    print("| +++ {} Collection: {}".format(c, current_m.title))
                    current_m.addCollection(c)
            elif not subfilters:
                print("| +++ {} Collection: {}".format(c, current_m.title))
                current_m.addCollection(c)
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
            if current_s in fs:
                print("| {} is already in collection: {}".format(current_s.title, c))
            elif subfilters:
                match = True
                for sf in subfilters:
                    method = sf[0]
                    terms = str(sf[1]).split(", ")
                    try:
                        show_attrs = getattr(current_s, method)
                        # If it returns a list, get the 'tag' attribute
                        # Otherwise, it's a string. Make it a list.
                        if isinstance(show_attrs, list) and "-" not in method:
                            show_attrs = [getattr(x, 'tag') for x in show_attrs]
                        else:
                            show_attrs = [str(show_attrs)]
                    except AttributeError as e:
                        print(e)
                        # for media in current_s.media:
                        #     if method == "video_resolution":
                        #         show_attrs = [media.videoResolution]
                        #     for part in media.parts:
                        #         if method == "audio_language":
                        #             show_attrs = ([audio_stream.language for audio_stream in part.audioStreams()])
                        #         if method == "subtitle_language":
                        #             show_attrs = ([subtitle_stream.language for subtitle_stream in part.subtitleStreams()])

                    # Get the intersection of the user's terms and movie's terms
                    # If it's empty, it's not a match
                    if not list(set(terms) & set(show_attrs)):
                        match = False
                        break
                if match:
                    print("| +++ Adding {} to collection {}".format(current_s.title, c))
                    current_s.addCollection(c)
            elif not subfilters:
                print("| +++ Adding {} to collection: {}".format(current_s.title, c))
                current_s.addCollection(c)
    try:
        missing
    except UnboundLocalError:
        return
    else:
        return missing

def delete_collection(data):
    confirm = input("| {} selected. Confirm deletion (y/n):".format(data.title))
    if confirm == "y":
        data.delete()
        print("| Collection deleted")
