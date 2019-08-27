from plexapi.video import Movie
from plexapi import exceptions as PlexExceptions
import imdb_tools


def get_movie(plex, data):
    # If an int is passed as data, assume it is a movie's rating key
    if isinstance(data, int):
        try:
            return plex.Server.fetchItem(data)
        except PlexExceptions.BadRequest:
            return "Nothing found"
    elif isinstance(data, Movie):
        return data
    else:
        print(data)
        movie_list = plex.MovieLibrary.search(title=data)
        if movie_list:
            return movie_list
        else:
            return "Movie: " + data + " not found"

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

def get_all_movies(plex):
    return plex.MovieLibrary.all()

def get_collection(plex, data):
    collection_list = plex.MovieLibrary.search(title=data, libtype="collection")
    if len(collection_list) > 1:
        c_names = [(str(i+1) + ") " + collection.title) for i, collection in enumerate(collection_list)]
        print("\n".join(c_names))
        while True:
            try:
                selection = int(input("Choose collection number: ")) - 1
                if selection >= 0:
                    return collection_list[selection]
                elif selection == "q":
                    return
                else:
                    print("Invalid entry")
            except (IndexError, ValueError) as E:
                print("Invalid entry")
    elif len(collection_list) == 1:
        return collection_list[0]
    else:
        return "No collection found"

def add_to_collection(plex, method, value, c, subfilters=None):
    if method in Movie.__doc__ or hasattr(Movie, method):
        try:
            movies = plex.MovieLibrary.search(**{method: value})
        except PlexExceptions.BadRequest:
            # If last character is "s" remove it and try again
            if method[-1:] == "s":
                movies = plex.MovieLibrary.search(**{method[:-1]: value})
                movies = [m.ratingKey for m in movies if movies]
    else:
        if method == "imdb-list":
            movies, missing = imdb_tools.imdb_get_movies(plex, value)
        elif method == "tmdb-list":
            movies, missing = imdb_tools.tmdb_get_movies(plex, value)
    if movies:
        # Check if already in collection
        cols = plex.MovieLibrary.search(title=c, libtype="collection")
        try:
            fs = cols[0].children
        except IndexError:
            fs = []
        for rk in movies:
            current_m = get_movie(plex, rk)
            current_m.reload()
            if current_m in fs:
                print("{} is already in collection: {}".format(current_m.title, c))
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
                            if method == "video-resolution":
                                mv_attrs = [media.videoResolution]
                            for part in media.parts:
                                if method == "audio-language":
                                    mv_attrs = ([audio_stream.language for audio_stream in part.audioStreams()])
                                if method == "subtitle-language":
                                    mv_attrs = ([subtitle_stream.language for subtitle_stream in part.subtitleStreams()])

                    # Get the intersection of the user's terms and movie's terms
                    # If it's empty, it's not a match
                    if not list(set(terms) & set(mv_attrs)):
                        match = False
                        break
                if match:
                    print("+++ Adding {} to collection {}".format(current_m.title, c))
                    current_m.addCollection(c)
            elif not subfilters:
                print("+++ Adding {} to collection: {}".format(current_m.title, c))
                current_m.addCollection(c)
    try:
        missing
    except UnboundLocalError:
        return
    else:
        return missing

def delete_collection(data):
    confirm = input("{} selected. Confirm deletion (y/n):".format(data.title))
    if confirm == "y":
        data.delete()
        print("Collection deleted")
