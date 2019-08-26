from config_tools import Plex
from config_tools import update_from_config
from config_tools import modify_config
from config_tools import Config
from plexapi.video import Movie
import plex_tools
from radarr_tools import add_to_radarr
import argparse
import sys

plex = Plex()

parser = argparse.ArgumentParser()
parser.add_argument("-u", "--update", help="Automatically update collections off config and quit",
                    action="store_true")
args = parser.parse_args()

if args.update:
    update_from_config(plex, True)
    sys.exit(0)

print("==================================================================")
print(" Plex Auto Collections by /u/iRawrz  ")
print("==================================================================")
print("\n")

if hasattr(__builtins__, 'raw_input'):
    input = raw_input

if input("Update Collections from Config? (y/n): ").upper() == "Y":
    update_from_config(plex)

def append_collection(config_update=None):
    while True:
        if config_update:
            collection_name = config_update
        else:
            collection_name = input("Enter collection to add to: ")
        try:
            selected_collection = plex_tools.get_collection(plex, collection_name)
            if not isinstance(selected_collection, str):
                print("\"{}\" Selected.".format(selected_collection.title))
                finished = False
                while not finished:
                    method = input("Add Movie(m), Actor(a), IMDB List(l), Custom (c)?: ")
                    if method == "m":
                        if not config_update:
                            method = "movie"
                            value = input("Enter Movie (Name or Rating Key): ")
                            if value is int:
                                plex_movie = plex_tools.get_movie(int(value))
                                print('+++ Adding %s to collection %s' % (plex_movie.title, selected_collection.title))
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

                    elif method == "a":
                        method = "actors"
                        value = input("Enter Actor Name: ")
                        a_rkey = plex_tools.get_actor_rkey(plex, value)
                        if config_update:
                            modify_config(collection_name, method, value)
                        else:
                            plex_tools.add_to_collection(plex, method, a_rkey, selected_collection.title)

                    elif method == "l":
                        method = "imdb-list"
                        url = input("Enter IMDB List URL: ").strip()
                        print("Processing IMDB List: {}".format(url))
                        try:
                            missing = plex_tools.add_to_collection(plex, "imdb-list", url, selected_collection.title)
                            if missing:
                                print("{} missing movies from IMDB List: {}".format(len(missing), url))
                                if input("Add missing movies to Radarr? (y/n)").upper() == "Y":
                                    add_to_radarr(missing)
                        except:
                            print("Bad IMDB List URL")
                        if config_update:
                            modify_config(collection_name, method, url)

                    elif method == "c":
                        print("Please read the below link to see valid filter types. "
                              "Please note not all have been tested")
                        print("https://python-plexapi.readthedocs.io/en/latest/modules/video.html?highlight=plexapi.video.Movie#plexapi.video.Movie")
                        while True:
                            method = input("Enter filter method: ")
                            m_search = "  " + method + " "
                            if m_search in Movie.__doc__ or hasattr(Movie, m_search):
                                if method[-1:] == "s":
                                    method_p = method[:-1]
                                else:
                                    method_p = method
                                value = input("Enter {}: ".format(method_p))
                                if config_update:
                                    modify_config(collection_name, method, value)
                                else:
                                    plex_tools.add_to_collection(plex, method, value, selected_collection.title)
                                break
                            else:
                                print("Filter method did not match an attribute for plexapi.video.Movie")
                    if input("Add more to collection? (y/n):") == "n":
                        print("\n")
                        finished = True
                break
            else:
                print(selected_collection)
                break
        except AttributeError:
            print("No collection found")


mode = None
while not mode == "q":
    try:
        print("Modes: Rescan (r), Actor(a), IMDB List(l), "
              "Add to Existing Collection (+), Delete(-), "
              "Search(s), Quit(q)")
        mode = input("Select Mode: ")

        if mode == "a":
            actor = input("Enter actor name: ")
            a_rkey = plex_tools.get_actor_rkey(plex, actor)
            if isinstance(a_rkey, int):
                c_name = input("Enter collection name: ")
                plex_tools.add_to_collection(plex, "actors", a_rkey, c_name)
            else:
                print("Invalid actor")
            print("\n")

        elif mode == "r":
            update_from_config(plex)

        elif mode == "l":
            url = input("Enter IMDB List URL: ")
            c_name = input("Enter collection name: ")
            print("Processing IMDB List: {}".format(url))
            try:
                missing = plex_tools.add_to_collection(plex, "imdb-list", url, c_name)
                if missing:
                    print("{} missing movies from IMDB List: {}".format(len(missing), url))
                    if input("Add missing movies to Radarr? (y/n)").upper() == "Y":
                        add_to_radarr(missing)
            except:
                print("Bad IMDB List URL")
            print("\n")

        elif mode == "+":
            if input("Add to collection in config file? (y/n): ") == "y":
                collections = Config().collections
                for i, collection in enumerate(collections):
                    print("{}) {}".format(i + 1, collection))
                selection = None
                while selection not in collections:
                    selection = input("Enter Collection Number: ")
                    try:
                        if int(selection) > 0:
                            selection = list(collections)[int(selection) - 1]
                        else:
                            print("Invalid selection")
                    except (IndexError, ValueError) as e:
                        print("Invalid selection")
                append_collection(selection)
            else:
                append_collection()

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
                print("Found collection {}".format(collection.title))
                movies = collection.children
                print("Movies in collection: ")
                for i, m in enumerate(movies):
                    print("{}) {}".format(i + 1, m.title))
            else:
                print(collection)
            print("\n")
    except KeyboardInterrupt:
        print("\n")
        pass
