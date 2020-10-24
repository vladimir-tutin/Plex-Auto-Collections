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
from config_tools import Radarr
from config_tools import TMDB
from config_tools import TraktClient
from config_tools import ImageServer
from config_tools import modify_config
from radarr_tools import add_to_radarr
from urllib.parse import urlparse

def update_from_config(config_path, plex, headless=False, no_meta=False, no_images=False):
    config = Config(config_path)
    collections = config.collections
    if isinstance(plex.Library, MovieSection):      libtype = "movie"
    elif isinstance(plex.Library, ShowSection):     libtype = "show"
    if not headless:
        print("|\n|===================================================================================================|")
    print("|\n| Running collection update press Ctrl+C to abort at anytime")
    for c in collections:
        print("| \n|===================================================================================================|\n|")
        print("| Updating collection: {}...".format(c))
        map = {}
        sync_collection = True if plex.sync_mode == "sync" else False
        if "sync_mode" in collections[c]:
            if collections[c]["sync_mode"]:
                if collections[c]["sync_mode"] == "append" or collections[c]["sync_mode"] == "sync":
                    if collections[c]["sync_mode"] == "sync":           sync_collection = True
                    else:                                               sync_collection = False
                else:
                    print("| Config Error: {} sync_mode Invalid\n| \tappend (Only Add Items to the Collection)\n| \tsync (Add & Remove Items from the Collection)".format(collections[c]["sync_mode"]))
            else:
                print("| Config Error: sync_mode attribute is blank")
        if sync_collection == True:
            print("| Sync Mode: sync")
            plex_collection = get_collection(plex, c, headless)
            if isinstance(plex_collection, Collections):
                for item in plex_collection.children:
                    map[item.ratingKey] = item
        else:
            print("| Sync Mode: append")

        tmdb_id = None
        methods = [m for m in collections[c] if m not in ("sync_mode","tmdb-list", "imdb-list", "trakt-list", "tmdb-poster", "details", "subfilters", "sort_title", "content_rating", "summary", "tmdb_summary", "collection_mode", "collection_sort", "poster", "tmdb_poster", "file_poster", "background", "file_background", "name_mapping")]
        subfilters = []
        if "subfilters" in collections[c]:
            for sf in collections[c]["subfilters"]:
                sf_string = sf, collections[c]["subfilters"][sf]
                subfilters.append(sf_string)
        for m in methods:
            if ("tmdb" in m or "imdb" in m) and not TMDB.valid:
                print("| Config Error: {} skipped. tmdb incorrectly configured".format(m))
            elif (m == "trakt_list" or ("tmdb" in m and plex.library_type == "show")) and not TraktClient.valid:
                print("| Config Error: {} skipped. trakt incorrectly configured".format(m))
            elif collections[c][m]:
                values = collections[c][m] if isinstance(collections[c][m], list) else str(collections[c][m]).split(", ")   # Support multiple imdb/tmdb/trakt lists
                for v in values:
                    m_print = m[:-1] if m[-1:] == "s" else m
                    print("| Processing {}: {}".format(m_print, v))
                    if m == "actors" or m == "actor":       v = get_actor_rkey(plex, v)
                    try:                                    missing, map = add_to_collection(config_path, plex, m, v, c, map, subfilters)
                    except UnboundLocalError:               missing, map = add_to_collection(config_path, plex, m, v, c, map)               # No sub-filters
                    except (KeyError, ValueError) as e:
                        print(e)
                        missing = False
                    if missing:
                        if libtype == "movie":
                            method_name = "IMDb" if "imdb" in m else "Trakt" if "trakt" in m else "TMDb"
                            if m == "tmdb_list" or m == "tmdb_list" or m == "imdb_list":
                                print("| {} missing movie{} from {} List: {}".format(len(missing), "s" if len(missing) > 1 else "", method_name, v))
                            elif m == "tmdb_collection":
                                print("| {} missing movie{} from {} Collection: {}".format(len(missing), "s" if len(missing) > 1 else "", method_name, v))
                            else:
                                print("| {} ID: {} missing".format(method_name, v))
                            if Radarr.valid:
                                radarr = Radarr(config_path)
                                if radarr.add_movie:
                                    print("| Adding missing movies to Radarr")
                                    add_to_radarr(config_path, missing)
                                elif not headless and radarr.add_movie == None and input("| Add missing movies to Radarr? (y/n): ").upper() == "Y":
                                    add_to_radarr(config_path, missing)
                        elif libtype == "show":
                            method_name = "Trakt" if "trakt" in m else "TVDb" if "tvdb" in m else "TMDb"
                            if m == "trakt_list" or m == "tmdb_list":
                                print("| {} missing show{} from {} List: {}".format(len(missing), "s" if len(missing) > 1 else "", method_name, v))
                            else:
                                print("| {} ID: {} missing".format(method_name, v))

                            # if not skip_sonarr:
                            #     if input("Add missing shows to Sonarr? (y/n): ").upper() == "Y":
                            #         add_to_radarr(missing_shows)
            else:
                print("| Config Error: {} attribute is blank".format(m))

        if "tmdb-list" in collections[c]:                       print("| Config Error: Please change the attribute tmdb-list to tmdb_collection")
        if "imdb-list" in collections[c]:                       print("| Config Error: Please change the attribute imdb-list to imdb_list")
        if "trakt-list" in collections[c]:                      print("| Config Error: Please change the attribute trakt-list to trakt_list")
        if "details" in collections[c]:                         print("| Config Error: Please remove the attribute details attribute all its old sub-attributes should be one level higher")
        if "tmdb-poster" in collections[c]:                     print("| Config Error: Please change the attribute tmdb-poster to tmdb_poster")
        if "subfilters" in collections[c] and collections[c]["subfilters"]:
            if "video-resolution" in collections[c]["subfilters"]:      print("| Config Error: Please change the subfilter attribute video-resolution to video_resolution")
            if "audio-language" in collections[c]["subfilters"]:        print("| Config Error: Please change the subfilter attribute audio-language to audio_language")
            if "subtitle-language" in collections[c]["subfilters"]:     print("| Config Error: Please change the subfilter attribute subtitle-language to subtitle_language")

        plex_collection = get_collection(plex, c, headless)

        if not isinstance(plex_collection, Collections): continue       # No collections created with requested criteria

        for ratingKey, item in map.items():
            if item is not None:
                print("| --- {} Collection: {}".format(c, item.title))
                item.removeCollection(c)

        def get_summary (config_path, data, meta, prefix):
            for m in meta:
                try:                        return prefix + tmdb_get_summary(config_path, data, m)
                except AttributeError:      pass

        if not no_meta:
            def edit_value (plex_collection, name, group, key=None):
                if key == None:
                    key = name
                if name in group:
                    if group[name]:
                        edits = {"{}.value".format(key): group[name], "{}.locked".format(key): 1}
                        plex_collection.edit(**edits)
                        plex_collection.reload()
                        print("| Detail: {} updated to {}".format(name, group[name]))
                    else:
                        print("| Config Error: {} attribute is blank".format(name))

            # Handle collection sort_title
            edit_value(plex_collection, "sort_title", collections[c], key="titleSort")

            # Handle collection content_rating
            edit_value(plex_collection, "content_rating", collections[c], key="contentRating")

            # Handle collection summary
            summary = None
            if "summary" in collections[c]:
                if collections[c]["summary"]:                       summary = collections[c]["summary"]
                else:                                               print("| Config Error: summary attribute is blank")
            elif "tmdb_summary" in collections[c]:
                if TMDB.valid:
                    if collections[c]["tmdb_summary"]:                  summary = get_summary(config_path, collections[c]["tmdb_summary"], ["overview", "biography"], "")
                    else:                                               print("| Config Error: tmdb_summary attribute is blank")
                else:                                               print("| Config Error: tmdb_summary skipped. tmdb incorrectly configured")

            if not summary and "tmdb_id" in collections[c] and TMDB.valid:
                summary = get_summary(config_path, tmdb_id, ["overview", "biography"], "")

            if summary:
                edits = {"summary.value": summary, "summary.locked": 1}
                plex_collection.edit(**edits)
                plex_collection.reload()
                print('| Detail: summary updated to "{}"'.format(summary))

            # Handle collection collection_mode
            if "collection_mode" in collections[c]:
                if collections[c]["collection_mode"]:
                    collection_mode = collections[c]["collection_mode"]
                    if collection_mode in ('default', 'hide', 'hide_items', 'show_items'):
                        if collection_mode == 'hide_items':              collection_mode = 'hideItems'
                        if collection_mode == 'show_items':              collection_mode = 'showItems'
                        plex_collection.modeUpdate(mode=collection_mode)
                        print("| Detail: collection_mode updated to {}".format(collection_mode))
                    else:                                                   print("| Config Error: {} collection_mode Invalid\n| \tdefault (Library default)\n| \thide (Hide Collection)\n| \thide_items (Hide Items in this Collection)\n| \tshow_items (Show this Collection and its Items)".format(collection_mode))
                else:                                                       print("| Config Error: collection_mode attribute is blank")

            # Handle collection collection_sort
            if "collection_sort" in collections[c]:
                if collections[c]["collection_sort"]:
                    collection_sort = collections[c]["collection_sort"]
                    if collection_sort in ('release', 'alpha'):
                        plex_collection.sortUpdate(sort=collection_sort)
                        print("| Detail: collection_sort updated to {}".format(collection_sort))
                    else:                                                   print("| Config Error: {} collection_sort Invalid\n| \trelease (Order Collection by release dates)\n| \talpha (Order Collection Alphabetically)".format(collection_sort))
                else:                                                       print("| Config Error: collection_sort attribute is blank")

        if not no_images:
            posters_found = []
            backgrounds_found = []
            # Handle collection posters
            if "poster" in collections[c]:
                if collections[c]["poster"]:                        posters_found.append(["url", collections[c]["poster"]])
                else:                                               print("| Config Error: poster attribute is blank")
            if "tmdb_poster" in collections[c]:
                if TMDB.valid:
                    if collections[c]["tmdb_poster"]:                   posters_found.append(["url", get_summary(config_path, collections[c]["tmdb_poster"], ["poster_path", "profile_path"], "https://image.tmdb.org/t/p/original")])
                    else:                                               print("| Config Error: tmdb_poster attribute is blank")
                else:                                               print("| Config Error: tmdb_poster skipped. tmdb incorrectly configured")
            if "file_poster" in collections[c]:
                if collections[c]["file_poster"]:                   posters_found.append(["file", collections[c]["file_poster"]])
                else:                                               print("| Config Error: file_poster attribute is blank")

            # Handle collection backgrounds
            if "background" in collections[c]:
                if collections[c]["background"]:                    backgrounds_found.append(["url", collections[c]["background"]])
                else:                                               print("| Config Error: background attribute is blank")
            if "tmdb_background" in collections[c]:
                if TMDB.valid:
                    if collections[c]["tmdb_background"]:           posters_found.append(["url", get_summary(config_path, collections[c]["tmdb_background"], ["backdrop_path"], "https://image.tmdb.org/t/p/original")])
                    else:                                               print("| Config Error: tmdb_background attribute is blank")
                else:                                               print("| Config Error: tmdb_background skipped. tmdb incorrectly configured")
            if "file_background" in collections[c]:
                if collections[c]["file_background"]:               backgrounds_found.append(["file", collections[c]["file_background"]])
                else:                                               print("| Config Error: file_background attribute is blank")


            # Handle Image Server
            image_server = ImageServer(config_path)
            if image_server.valid:
                system_name = c
                if "system_name" in collections[c]:
                    if collections[c]["system_name"]:       system_name = collections[c]["system_name"]
                    else:                                   print("| Config Error: system_name attribute is blank")
                if image_server.poster:
                    path = os.path.join(image_server.poster, "{}.*".format(system_name))
                    matches = glob.glob(path)
                    if len(matches) > 0 or len(posters_found) > 0:
                        for match in matches:       posters_found.append(["file", os.path.abspath(match)])
                    else:
                        print("| poster not found at: {}".format(os.path.abspath(path)))
                if image_server.background:
                    path = os.path.join(image_server.background, "{}.*".format(system_name))
                    matches = glob.glob(path)
                    if len(matches) > 0 or len(backgrounds_found) > 0:
                        for match in matches:       backgrounds_found.append(["file", os.path.abspath(match)])
                    else:
                        print("| background not found at: {}".format(os.path.abspath(path)))
                if image_server.image:
                    path = os.path.join(image_server.image, "{}".format(system_name), "poster.*")
                    matches = glob.glob(path)
                    if len(matches) > 0 or len(posters_found) > 0:
                        for match in matches:       posters_found.append(["file", os.path.abspath(match)])
                    else:
                        print("| poster not found at: {}".format(os.path.abspath(path)))
                    path = os.path.join(image_server.image, "{}".format(system_name), "background.*")
                    matches = glob.glob(path)
                    if len(matches) > 0 or len(backgrounds_found) > 0:
                        for match in matches:       backgrounds_found.append(["file", os.path.abspath(match)])
                    else:
                        print("| background not found at: {}".format(os.path.abspath(path)))

            # Pick Images
            def choose_from_list (list_type, item_list, headless):
                if item_list:
                    if len(item_list) == 1 or (len(item_list) > 0 and headless):  return item_list[0]
                    names = ["| {}) [{}] {}".format(i, item[0], item[1]) for i, item in enumerate(item_list, start=1)]
                    print("| 0) Do Nothing")
                    print("\n".join(names))
                    while True:
                        try:
                            selection = int(input("| Choose {} number: ".format(list_type))) - 1
                            if selection >= 0:                                  return item_list[selection]
                            elif selection == -1:                               return None
                            else:                                               print("| Invalid entry")
                        except (IndexError, ValueError) as E:               print("| Invalid entry")
                else:                                                   return None
            poster = choose_from_list("poster", posters_found, headless)
            background = choose_from_list("background", backgrounds_found, headless)

            # Special case fall back for tmdb_id tag if no other poster or background is found
            if not poster and "tmdb_id" in collections[c] and TMDB.valid:
                poster = ["url", str(get_summary(config_path, tmdb_id, ["poster_path", "profile_path"], "https://image.tmdb.org/t/p/original/"))]
            if not background and "tmdb_id" in collections[c] and TMDB.valid:
                background = ["url", str(get_summary(config_path, tmdb_id, ["backdrop_path"], "https://image.tmdb.org/t/p/original/"))]

            # Update poster
            if poster:
                if poster[0] == "url":          plex_collection.uploadPoster(url=poster[1])
                else:                           plex_collection.uploadPoster(filepath=poster[1])
                print("| Detail: poster updated to [{}] {}".format(poster[0], poster[1]))

            # Update background
            if background:
                if background[0] == "url":      plex_collection.uploadArt(url=background[1])
                else:                           plex_collection.uploadArt(filepath=background[1])
                print("| Detail: background updated to [{}] {}".format(background[0], background[1]))

def append_collection(config_path, config_update=None):
    while True:
        if config_update:
            collection_name = config_update
            selected_collection = get_collection(plex, collection_name, True)
        else:
            collection_name = input("| Enter collection to add to: ")
            selected_collection = get_collection(plex, collection_name)
        try:
            if not isinstance(selected_collection, str):
                print("| \"{}\" Selected.".format(selected_collection.title))
                finished = False
                while not finished:
                    try:
                        collection_type = selected_collection.subtype
                        if collection_type == 'movie':
                            method = input("| Add Movie(m), Actor(a), IMDb/TMDb/Trakt List(l), Custom(c), Back(b)?: ")
                        else:
                            method = input("| Add Show(s), Actor(a), IMDb/TMDb/Trakt List(l), Custom(c), Back(b)?: ")
                        if method == "m":
                            if not config_update:
                                method = "movie"
                                value = input("| Enter Movie (Name or Rating Key): ")
                                if value is int:
                                    plex_movie = get_movie(plex, int(value))
                                    print('| +++ Adding %s to collection %s' % (
                                        plex_movie.title, selected_collection.title))
                                    plex_movie.addCollection(selected_collection.title)
                                else:
                                    results = get_movie(plex, value)
                                    if len(results) > 1:
                                        while True:
                                            i = 1
                                            for result in results:
                                                print("| {POS}) {TITLE} - {RATINGKEY}".format(POS=i, TITLE=result.title,
                                                                                            RATINGKEY=result.ratingKey))
                                                i += 1
                                            s = input("| Select movie (N for None): ")
                                            if int(s):
                                                s = int(s)
                                                if len(results) >= s > 0:
                                                    result = results[s - 1]
                                                    print('| +++ Adding %s to collection %s' % (
                                                        result.title, selected_collection.title))
                                                    result.addCollection(selected_collection.title)
                                                    break
                                            else:
                                                break
                            else:
                                print("| Movies in configuration file not yet supported")

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
                            value = input("| Enter Actor Name: ")
                            a_rkey = get_actor_rkey(plex, value)
                            if config_update:
                                modify_config(config_path, collection_name, method, value)
                            else:
                                add_to_collection(config_path, plex, method, a_rkey, selected_collection.title)

                        elif method == "l":
                            l_type = input("| Enter list type IMDb(i) TMDb(t) Trakt(k): ")
                            if l_type == "i":
                                l_type = "IMDb"
                                method = "imdb_list"
                            elif l_type == "t":
                                l_type = "TMDb"
                                method = "tmdb_collection"
                            elif l_type == "k":
                                l_type = "Trakt"
                                method = "trakt_list"
                            else:
                                return
                            url = input("| Enter {} List URL: ".format(l_type)).strip()
                            print("| Processing {} List: {}".format(l_type, url))
                            if config_update:
                                modify_config(config_path, collection_name, method, url)
                            else:
                                missing = add_to_collection(config_path, plex, method, url, selected_collection.title)
                                if missing:
                                    if collection_type == 'movie':
                                        print("| {} missing movies from {} List: {}".format(len(missing), l_type, url))
                                        if input("| Add missing movies to Radarr? (y/n)").upper() == "Y":
                                            add_to_radarr(config_path, missing)
                                    # elif collection_type == 'show':
                                    #     print("{} missing shows from {} List: {}".format(len(missing_shows), l_type, url))
                                    #     if input("Add missing shows to Sonarr? (y/n)").upper() == "Y":
                                    #         add_to_sonarr(missing_shows)
                                print("| Bad {} List URL".format(l_type))

                        elif method == "c":
                            print("| Please read the below link to see valid filter types. "
                                  "Please note not all have been tested")
                            print(
                                "| https://python-plexapi.readthedocs.io/en/latest/modules/video.html?highlight=plexapi.video.Movie#plexapi.video.Movie")
                            while True:
                                method = input("| Enter filter method (q to quit): ")
                                if method in "quit":
                                    break
                                m_search = "  " + method + " "
                                if m_search in Movie.__doc__ or hasattr(Movie, m_search):
                                    if method[-1:] == "s":
                                        method_p = method[:-1]
                                    else:
                                        method_p = method
                                    value = input("| Enter {}: ".format(method_p))
                                    if config_update:
                                        modify_config(config_path, collection_name, method, value)
                                    else:
                                        add_to_collection(config_path, plex, method, value, selected_collection.title)
                                    break
                                else:
                                    print("| Filter method did not match an attribute for plexapi.video.Movie")
                    except TypeError:
                        print("| Bad {} URL".format(l_type))
                    except KeyError as e:
                        print("| " + str(e))
                    if input("| Add more to collection? (y/n): ") == "n":
                        finished = True
                break
            else:
                print("| " + selected_collection)
                break
        except AttributeError:
            print("| No collection found")

if hasattr(__builtins__, 'raw_input'):
    input = raw_input

parser = argparse.ArgumentParser()
parser.add_argument("-c", "--config-path", "--config_path",
                    dest="config_path",
                    help="Run with desired config.yml file",
                    nargs='?',
                    const="",
                    type=str)
parser.add_argument("-u", "--update",
                    help="Update collections using config without user interaction",
                    action="store_true")
parser.add_argument("-nm", "--no_meta",
                    help="If using --update this option will not update metadata while adding movies to collections",
                    action="store_true")
parser.add_argument("-ni", "--no_images",
                    help="If using --update this option will not update images while adding movies to collections",
                    action="store_true")

args = parser.parse_args()
print()
print("|===================================================================================================|")
print("|     ___  _               _         _           ___       _  _           _    _                    |")
print("|    | _ \| | ___ __ __   /_\  _  _ | |_  ___   / __| ___ | || | ___  __ | |_ (_) ___  _ _   ___    |")
print("|    |  _/| |/ -_)\ \ /  / _ \| || ||  _|/ _ \ | (__ / _ \| || |/ -_)/ _||  _|| |/ _ \| ' \ (_-<    |")
print("|    |_|  |_|\___|/_\_\ /_/ \_\\\\_,_| \__|\___/  \___|\___/|_||_|\___|\__| \__||_|\___/|_||_|/__/    |")
print("|                                                                                                   |")
print("|===================================================================================================|")
print("| Version 2.0.0")
print("| Locating config...")
config_path = None
app_dir = os.path.dirname(os.path.abspath(__file__))


if args.config_path and os.path.exists(args.config_path):                   config_path = os.path.abspath(args.config_path)                                         # Set config_path from command line switch
elif args.config_path and not os.path.exists(args.config_path):             sys.exit("| Config Error: config not found at {}".format(os.path.abspath(args.config_path)))
elif os.path.exists(os.path.join(app_dir, "config.yml")):                   config_path = os.path.abspath(os.path.join(app_dir, "config.yml"))                      # Set config_path from app_dir
elif os.path.exists(os.path.join(app_dir, "..", "config", "config.yml")):   config_path = os.path.abspath(os.path.join(app_dir, "..", "config", "config.yml"))      # Set config_path from config_dir
else:                                                                       sys.exit("| Config Error: No config found, exiting")

print("| Using {} as config".format(config_path))


if args.update:
    config = Config(config_path, headless=True)
    plex = Plex(config_path)
    update_from_config(config_path, plex, True, args.no_meta, args.no_images)
    sys.exit(0)


config = Config(config_path)
plex = Plex(config_path)

try:
    if input("| \n| Update Collections from Config? (y/n): ").upper() == "Y":
        update_from_config(config_path, plex, False)
except KeyboardInterrupt:
    pass

mode = None
while not mode == "q":
    try:
        print("| ")
        print("|===================================================================================================|")
        print("| \n| Modes: Rescan(r), Actor(a), IMDb/TMDb/Trakt List(l), "
              "Add to Existing Collection(+), Delete(-), "
              "Search(s), Quit(q)\n| Note: Type Ctrl+C to come back to this menu\n| ")
        mode = input("| Select Mode: ")

        if mode == "r":
            try:
                update_from_config(config_path, plex)
            except KeyboardInterrupt:
                pass

        elif mode == "a":
            print("|\n|===================================================================================================|")
            actor = input("| \n| Enter actor name: ")
            a_rkey = get_actor_rkey(plex, actor)
            if isinstance(a_rkey, int):
                c_name = input("| Enter collection name: ")
                add_to_collection(config_path, plex, "actors", a_rkey, c_name)
            else:
                print("| Invalid actor")

        elif mode == "l":
            print("|\n|===================================================================================================|")
            l_type = input("| \n| Enter list type IMDb(i) TMDb(t) Trakt(k): ")
            method_map = {"i": ("IMDb", "imdb_list"), "t": ("TMDb", "tmdb_collection"), "k": ("Trakt", "trakt_list")}
            if (l_type in ("i", "t") and TMDB.valid) or (l_type == "k" and TraktClient.valid):
                l_type, method = method_map[l_type]
                url = input("| Enter {} List URL: ".format(l_type)).strip()
                c_name = input("| Enter collection name: ")
                print("| Processing {} List: {}".format(l_type, url))
                try:
                    missing = add_to_collection(config_path, plex, method, url, c_name)
                    if missing:
                        if isinstance(plex.Library, MovieSection):
                            print("| {} missing items from {} List: {}".format(len(missing), l_type, url))
                            if input("| Add missing movies to Radarr? (y/n)").upper() == "Y":
                                add_to_radarr(config_path, missing)
                        elif isinstance(plex.Library, ShowSection):
                            print("| {} missing shows from {} List: {}".format(len(missing), l_type, url))
                            # if input("Add missing shows to Sonarr? (y/n)").upper() == "Y":
                            #     add_to_sonarr(missing)
                except (NameError, TypeError) as f:
                    print("| Bad {} list URL".format(l_type))
                except KeyError as e:
                    print("| " + str(e))

        elif mode == "+":
            print("|\n|===================================================================================================|")
            if input("| \n| Add to collection in config file? (y/n): ") == "y":
                collections = Config(config_path).collections
                for i, collection in enumerate(collections):
                    print("| {}) {}".format(i + 1, collection))
                selection = None
                while selection not in list(collections):
                    selection = input("| Enter Collection Number: ")
                    try:
                        if int(selection) > 0:
                            selection = list(collections)[int(selection) - 1]
                        else:
                            print("| Invalid selection")
                    except (IndexError, ValueError) as e:
                        print("| Invalid selection")
                append_collection(config_path, selection)
            else:
                append_collection(config_path)

        elif mode == "-":
            print("|\n|===================================================================================================|")
            data = input("| \n| Enter collection name to search for (blank for all): ")
            collection = get_collection(plex, data)
            if not isinstance(collection, str):
                delete_collection(collection)
            else:
                print("| " + collection)

        elif mode == "s":
            print("|\n|===================================================================================================|")
            data = input("| \n| Enter collection name to search for (blank for all): ")
            collection = get_collection(plex, data)
            if not isinstance(collection, str):
                print("| Found {} collection {}".format(collection.subtype, collection.title))
                items = collection.children
                print("| {}s in collection: ".format(collection.subtype).capitalize())
                for i, m in enumerate(items):
                    print("| {}) {}".format(i + 1, m.title))
            else:
                print("| " + collection)
    except KeyboardInterrupt:
        print()
        pass

print("|\n|===================================================================================================|\n")
