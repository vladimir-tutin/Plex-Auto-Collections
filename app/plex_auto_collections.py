import os
import argparse
import sys
import threading
import glob
from plexapi.server import PlexServer
from plexapi.video import Movie
from plexapi.video import Show
from plexapi.library import MovieSection
from plexapi.library import ShowSection
from plexapi.library import Collections
from plex_tools import add_to_collection
from plex_tools import delete_collection
from plex_tools import get_actor_rkey
from plex_tools import get_collection
from plex_tools import get_movie
from imdb_tools import tmdb_get_summary
from config_tools import Config
from config_tools import Plex
from config_tools import ImageServer
from config_tools import modify_config
from radarr_tools import add_to_radarr

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
            if "poster" in collections[c]["details"]:
                item.uploadPoster(url=collections[c]["details"]["poster"])
            elif "tmdb-poster" in collections[c]["details"]:
                # Seems clunky ...
                try:
                    slug = tmdb_get_summary(config_path, collections[c]["details"]["tmdb-poster"], "poster_path")
                except AttributeError:
                    slug = tmdb_get_summary(config_path, collections[c]["details"]["tmdb-poster"], "profile_path")
                
                item.uploadPoster(url="https://image.tmdb.org/t/p/original/{}".format(slug))
            else:
                search = os.path.join(ImageServer(config_path).posterdirectory, "{}.*".format(c))
                matches = glob.glob(search)

                if len(matches) == 1:
                    item.uploadPoster(filepath=matches[0])

            # Handle collection backgrounds
            if "background" in collections[c]["details"]:
                item.uploadArt(url=collections[c]["details"]["background"])
            else:
                search = os.path.join(ImageServer(config_path).backgrounddirectory, "{}.*".format(c))
                matches = glob.glob(search)

                if len(matches) == 1:
                    item.uploadArt(filepath=matches[0])

            # Handle collection collectionMode
            if "collection_mode" in collections[c]["details"]:
                collectionMode = collections[c]["details"]["collection_mode"]
                if collectionMode in ('default', 'hide', 'hideItems', 'showItems'):
                    item.modeUpdate(mode=collectionMode)
                else:
                    print("collectionMode Invalid\ndefault (Library default)\nhide (Hide Collection)\nhideItems (Hide Items in this Collection)\nshowItems (Show this Collection and its Items)\n")

            # Handle collection collectionSort
            if "collection_sort" in collections[c]["details"]:
                collectionSort = collections[c]["details"]["collection_sort"]
                if collectionSort in ('release', 'alpha'):
                    item.sortUpdate(sort=collectionSort)
                else:
                    print("collectionSort Invalid\nrelease (Order Collection by release dates)\nalpha (Order Collection Alphabetically)\n")


def append_collection(config_path, config_update=None):
    while True:
        if config_update:
            collection_name = config_update
            selected_collection = get_collection(plex, collection_name, True)
        else:
            collection_name = input("Enter collection to add to: ")
            selected_collection = get_collection(plex, collection_name)
        try:
            if not isinstance(selected_collection, str):
                print("\"{}\" Selected.".format(selected_collection.title))
                finished = False
                while not finished:
                    try:
                        collection_type = selected_collection.subtype
                        if collection_type == 'movie':
                            method = input("Add Movie(m), Actor(a), IMDb/TMDb/Trakt List(l), Custom(c)?: ")
                        else:
                            method = input("Add Show(s), Actor(a), IMDb/TMDb/Trakt List(l), Custom(c)?: ")
                        if method == "m":
                            if not config_update:
                                method = "movie"
                                value = input("Enter Movie (Name or Rating Key): ")
                                if value is int:
                                    plex_movie = get_movie(plex, int(value))
                                    print('+++ Adding %s to collection %s' % (
                                        plex_movie.title, selected_collection.title))
                                    plex_movie.addCollection(selected_collection.title)
                                else:
                                    results = get_movie(plex, value)
                                    if len(results) > 1:
                                        while True:
                                            i = 1
                                            for result in results:
                                                print("{POS}) {TITLE} - {RATINGKEY}".format(POS=i, TITLE=result.title,
                                                                                            RATINGKEY=result.ratingKey))
                                                i += 1
                                            s = input("Select movie (N for None): ")
                                            if int(s):
                                                s = int(s)
                                                if len(results) >= s > 0:
                                                    result = results[s - 1]
                                                    print('+++ Adding %s to collection %s' % (
                                                        result.title, selected_collection.title))
                                                    result.addCollection(selected_collection.title)
                                                    break
                                            else:
                                                break
                            else:
                                print("Movies in configuration file not yet supported")

                        # elif method == "s":
                        #     if not config_update:
                        #         method = "show"
                        #         value = input("Enter Show (Name or Rating Key): ")
                        #         if value is int:
                        #             plex_show = get_show(int(value))
                        #             print('+++ Adding %s to collection %s' % (
                        #                 plex_show.title, selected_collection.title))
                        #             plex_show.addCollection(selected_collection.title)
                        #         else:
                        #             results = get_show(plex, value)
                        #             if len(results) > 1:
                        #                 while True:
                        #                     i = 1
                        #                     for result in results:
                        #                         print("{POS}) {TITLE} - {RATINGKEY}".format(POS=i, TITLE=result.title,
                        #                                                                     RATINGKEY=result.ratingKey))
                        #                         i += 1
                        #                     s = input("Select show (N for None): ")
                        #                     if int(s):
                        #                         s = int(s)
                        #                         if len(results) >= s > 0:
                        #                             result = results[s - 1]
                        #                             print('+++ Adding %s to collection %s' % (
                        #                                 result.title, selected_collection.title))
                        #                             result.addCollection(selected_collection.title)
                        #                             break
                        #                     else:
                        #                         break
                        #     else:
                        #         print("Shows in configuration file not yet supported")

                        elif method == "a":
                            method = "actors"
                            value = input("Enter Actor Name: ")
                            a_rkey = get_actor_rkey(plex, value)
                            if config_update:
                                modify_config(config_path, collection_name, method, value)
                            else:
                                add_to_collection(config_path, plex, method, a_rkey, selected_collection.title)

                        elif method == "l":
                            l_type = input("Enter list type IMDb(i) TMDb(t) Trakt(k): ")
                            if l_type == "i":
                                l_type = "IMDb"
                                method = "imdb-list"
                            elif l_type == "t":
                                l_type = "TMDb"
                                method = "tmdb-list"
                            elif l_type == "k":
                                l_type = "Trakt"
                                method = "trakt-list"
                            else:
                                return
                            url = input("Enter {} List URL: ".format(l_type)).strip()
                            print("Processing {} List: {}".format(l_type, url))
                            if config_update:
                                modify_config(config_path, collection_name, method, url)
                            else:
                                missing = add_to_collection(config_path, plex, method, url, selected_collection.title)
                                if missing:
                                    if collection_type == 'movie':
                                        print("{} missing movies from {} List: {}".format(len(missing), l_type, url))
                                        if input("Add missing movies to Radarr? (y/n)").upper() == "Y":
                                            add_to_radarr(config_path, missing)
                                    # elif collection_type == 'show':
                                    #     print("{} missing shows from {} List: {}".format(len(missing_shows), l_type, url))
                                    #     if input("Add missing shows to Sonarr? (y/n)").upper() == "Y":
                                    #         add_to_sonarr(missing_shows)
                                print("Bad {} List URL".format(l_type))

                        elif method == "c":
                            print("Please read the below link to see valid filter types. "
                                  "Please note not all have been tested")
                            print(
                                "https://python-plexapi.readthedocs.io/en/latest/modules/video.html?highlight=plexapi.video.Movie#plexapi.video.Movie")
                            while True:
                                method = input("Enter filter method (q to quit): ")
                                if method in "quit":
                                    break
                                m_search = "  " + method + " "
                                if m_search in Movie.__doc__ or hasattr(Movie, m_search):
                                    if method[-1:] == "s":
                                        method_p = method[:-1]
                                    else:
                                        method_p = method
                                    value = input("Enter {}: ".format(method_p))
                                    if config_update:
                                        modify_config(config_path, collection_name, method, value)
                                    else:
                                        add_to_collection(config_path, plex, method, value, selected_collection.title)
                                    break
                                else:
                                    print("Filter method did not match an attribute for plexapi.video.Movie")
                    except TypeError:
                        print("Bad {} URL".format(l_type))
                    except KeyError as e:
                        print(e)
                    if input("Add more to collection? (y/n): ") == "n":
                        finished = True
                        print("\n")
                break
            else:
                print(selected_collection)
                break
        except AttributeError:
            print("No collection found")


if hasattr(__builtins__, 'raw_input'):
    input = raw_input

parser = argparse.ArgumentParser()
parser.add_argument("-c", "--config-path", "--config_path",
                    dest="config_path",
                    help="Run with desired config.yml file",
                    nargs='?',
                    const=1,
                    type=str)
parser.add_argument("-u", "--update",
                    help="Update collections using config without user interaction",
                    action="store_true")

args = parser.parse_args()

print("==================================================================")
print(" Plex Auto Collections                                            ")
print("==================================================================")

print("Attempting to find config")
config_path = None
app_dir = os.path.dirname(os.path.realpath(__file__))

# Set config_path from command line switch
if args.config_path and os.path.exists(args.config_path):
    config_path = args.config_path
# Set config_path from app_dir
elif os.path.exists(os.path.join(app_dir, "config.yml")):
    config_path = os.path.abspath(os.path.join(app_dir, "config.yml"))
# Set config_path from config_dir
elif os.path.exists(os.path.join(app_dir, "..", "config", "config.yml")):
    config_path = os.path.abspath(os.path.join(app_dir, "..", "config", "config.yml"))
else:
    print("No config found, exiting")
    sys.exit(1)

print("Using {} as config".format(config_path))

plex = Plex(config_path)

if args.update:
    # sys.stdout = open("pac.log", "w")
    update_from_config(config_path, plex, True)
    sys.exit(0)

if input("Update Collections from Config? (y/n): ").upper() == "Y":
    update_from_config(config_path, plex, False)

print("\n")
mode = None
while not mode == "q":
    try:
        print("Modes: Rescan(r), Actor(a), IMDb/TMDb/Trakt List(l), "
              "Add to Existing Collection(+), Delete(-), "
              "Search(s), Quit(q)\n")
        mode = input("Select Mode: ")

        if mode == "r":
            update_from_config(config_path, plex)

        elif mode == "a":
            actor = input("Enter actor name: ")
            a_rkey = get_actor_rkey(plex, actor)
            if isinstance(a_rkey, int):
                c_name = input("Enter collection name: ")
                add_to_collection(config_path, plex, "actors", a_rkey, c_name)
            else:
                print("Invalid actor")
            print("\n")

        elif mode == "l":
            l_type = input("Enter list type IMDb(i) TMDb(t) Trakt(k): ")
            method_map = {"i": ("IMDb", "imdb-list"), "t": ("TMDb", "tmdb-list"), "k": ("Trakt", "trakt-list")}
            if l_type in ("i", "t", "k"):
                l_type, method = method_map[l_type]
                url = input("Enter {} List URL: ".format(l_type)).strip()
                c_name = input("Enter collection name: ")
                print("Processing {} List: {}".format(l_type, url))
                try:
                    missing = add_to_collection(config_path, plex, method, url, c_name)
                    if missing:
                        if isinstance(plex.Library, MovieSection):
                            print("{} missing items from {} List: {}".format(len(missing), l_type, url))
                            if input("Add missing movies to Radarr? (y/n)").upper() == "Y":
                                add_to_radarr(config_path, missing)
                        elif isinstance(plex.Library, ShowSection):
                            print("{} missing shows from {} List: {}".format(len(missing), l_type, url))
                            # if input("Add missing shows to Sonarr? (y/n)").upper() == "Y":
                            #     add_to_sonarr(missing)
                except (NameError, TypeError) as f:
                    print("Bad {} list URL".format(l_type))
                except KeyError as e:
                    print(e)
            print("\n")

        elif mode == "+":
            if input("Add to collection in config file? (y/n): ") == "y":
                collections = Config(config_path).collections
                for i, collection in enumerate(collections):
                    print("{}) {}".format(i + 1, collection))
                selection = None
                while selection not in list(collections):
                    selection = input("Enter Collection Number: ")
                    try:
                        if int(selection) > 0:
                            selection = list(collections)[int(selection) - 1]
                        else:
                            print("Invalid selection")
                    except (IndexError, ValueError) as e:
                        print("Invalid selection")
                append_collection(config_path, selection)
            else:
                append_collection(config_path)

        elif mode == "-":
            data = input("Enter collection name to search for (blank for all): ")
            collection = get_collection(plex, data)
            if not isinstance(collection, str):
                delete_collection(collection)
            else:
                print(collection)
            print("\n")

        elif mode == "s":
            data = input("Enter collection name to search for (blank for all): ")
            collection = get_collection(plex, data)
            if not isinstance(collection, str):
                print("Found {} collection {}".format(collection.subtype, collection.title))
                items = collection.children
                print("{}s in collection: ".format(collection.subtype).capitalize())
                for i, m in enumerate(items):
                    print("{}) {}".format(i + 1, m.title))
            else:
                print(collection)
            print("\n")
    except KeyboardInterrupt:
        print("\n"),
        pass
