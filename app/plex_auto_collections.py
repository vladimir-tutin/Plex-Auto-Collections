import argparse
import sys
import threading

from plexapi.video import Movie
from plexapi.video import Show

import image_server
import plex_tools
from config_tools import Config
from config_tools import Plex
from config_tools import modify_config
from config_tools import update_from_config
from radarr_tools import add_to_radarr


def append_collection(config_path, config_update=None):
    while True:
        if config_update:
            collection_name = config_update
            selected_collection = plex_tools.get_collection(plex, collection_name, True)
        else:
            collection_name = input("Enter collection to add to: ")
            selected_collection = plex_tools.get_collection(plex, collection_name)
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
                                    plex_movie = plex_tools.get_movie(int(value))
                                    print('+++ Adding %s to collection %s' % (
                                        plex_movie.title, selected_collection.title))
                                    plex_movie.addCollection(selected_collection.title)
                                else:
                                    results = plex_tools.get_movie(plex, value)
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

                        elif method == "s":
                            if not config_update:
                                method = "show"
                                value = input("Enter Show (Name or Rating Key): ")
                                if value is int:
                                    plex_show = plex_tools.get_show(int(value))
                                    print('+++ Adding %s to collection %s' % (
                                        plex_show.title, selected_collection.title))
                                    plex_show.addCollection(selected_collection.title)
                                else:
                                    results = plex_tools.get_show(plex, value)
                                    if len(results) > 1:
                                        while True:
                                            i = 1
                                            for result in results:
                                                print("{POS}) {TITLE} - {RATINGKEY}".format(POS=i, TITLE=result.title,
                                                                                            RATINGKEY=result.ratingKey))
                                                i += 1
                                            s = input("Select show (N for None): ")
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
                                print("Shows in configuration file not yet supported")

                        elif method == "a":
                            method = "actors"
                            value = input("Enter Actor Name: ")
                            a_rkey = plex_tools.get_actor_rkey(plex, value)
                            if config_update:
                                modify_config(config_path, collection_name, method, value)
                            else:
                                plex_tools.add_to_collection(config_path, plex, method, a_rkey, selected_collection.title)

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
                                missing = plex_tools.add_to_collection(config_path, plex, method, url, selected_collection.title)
                                if missing:
                                    if collection_type == 'movie':
                                        print("{} missing movies from {} List: {}".format(len(missing), l_type, url))
                                        if input("Add missing movies to Radarr? (y/n)").upper() == "Y":
                                            add_to_radarr(config_path, missing)
                                    elif collection_type == 'show':
                                        print("{} missing shows from {} List: {}".format(len(missing_shows), l_type, url))
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
                                        plex_tools.add_to_collection(config_path, plex, method, value, selected_collection.title)
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
parser.add_argument("-c", "--config_path",
                    help="Configuration file",
                    nargs='?',
                    const=1,
                    type=str,
                    default="config.yml")
parser.add_argument("-u", "--update",
                    help="Automatically update collections off config and quits",
                    action="store_true")
parser.add_argument("-ns", "--noserver",
                    help="Don't start the image server",
                    action="store_true")

args = parser.parse_args()


print("==================================================================")
print(" Plex Auto Collections by /u/iRawrz  ")
print("==================================================================")

config_path = args.config_path
plex = Plex(config_path)

if not args.noserver:
    print("Attempting to start image server")
    pid = threading.Thread(target=image_server.start_srv, args=(config_path,))
    pid.daemon = True
    pid.start()
    print(image_server.check_running(config_path))

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
            a_rkey = plex_tools.get_actor_rkey(plex, actor)
            if isinstance(a_rkey, int):
                c_name = input("Enter collection name: ")
                plex_tools.add_to_collection(config_path, plex, "actors", a_rkey, c_name)
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
                    missing = plex_tools.add_to_collection(config_path, plex, method, url, c_name)
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
            collection = plex_tools.get_collection(plex, data)
            if not isinstance(collection, str):
                plex_tools.delete_collection(collection)
            else:
                print(collection)
            print("\n")

        elif mode == "s":
            data = input("Enter collection name to search for (blank for all): ")
            collection = plex_tools.get_collection(plex, data)
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
