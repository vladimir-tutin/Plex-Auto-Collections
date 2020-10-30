import os
import argparse
import re
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
from config_tools import Tautulli
from config_tools import TraktClient
from config_tools import ImageServer
from config_tools import modify_config
from radarr_tools import add_to_radarr
from urllib.parse import urlparse

def update_from_config(config_path, plex, headless=False, no_meta=False, no_images=False):
    config = Config(config_path)
    collections = config.collections
    if isinstance(plex.Library, MovieSection):
        libtype = "movie"
    elif isinstance(plex.Library, ShowSection):
        libtype = "show"
    if not headless:
        print("|\n|===================================================================================================|")
    method_alias = {
        "actors": "actor", "role": "actor", "roles": "actor",
        "content_ratings": "content_rating", "contentRating": "content_rating", "contentRatings": "content_rating",
        "countries": "country",
        "decades": "decade",
        "directors": "director",
        "genres": "genre",
        "studios": "studio", "network": "studio", "networks": "studio",
        "years": "year",
        "writers": "writer",
    }
    all_lists = [
        "tmdb_collection",
        "tmdb_id",
        "tmdb_actor",
        "tmdb_director"
        "tmdb_writer"
        "tmdb_list",
        "tmdb_movie",
        "tmdb_show",
        "tvdb_show",
        "imdb_list",
        "trakt_list",
        "trakt_trending",
        "tautulli"
    ]
    all_filters = [
        "all",
        "actor", "actor!",
        "country", "country!",
        "decade", "decade!",
        "director", "director!",
        "genre", "genre!",
        "studio", "studio!",
        "year", "year!",
        "writer", "writer!"
    ]
    show_only_lists = [
        "tmdb_show",
        "tvdb_show"
    ]
    movie_only_lists = [
        "tmdb_collection",
        "tmdb_id",
        "tmdb_movie",
        "imdb_list",
    ]
    movie_only_filters = [
        "actor", "actor!",
        "country", "country!",
        "decade", "decade!",
        "director", "director!",
        "writer", "writer!"
    ]
    all_subfilters = [
        "actor", "actor!",
        "content_rating", "content_rating!",
        "country", "country!",
        "director", "director!",
        "genre", "genre!",
        "studio", "studio!",
        "year", "year!", "year.gte", "year.lte",
        "writer", "writer!",
        "rating.gte", "rating.lte",
        "max_age",
        "originally_available.gte", "originally_available.lte",
        "video_resolution", "video_resolution!",
        "audio_language", "audio_language!",
        "subtitle_language", "subtitle_language!"
    ]
    movie_only_subfilters = [
        "country", "country!",
        "director", "director!",
        "writer", "writer!",
        "video_resolution", "video_resolution!",
        "audio_language", "audio_language!",
        "subtitle_language", "subtitle_language!"
    ]
    details = [
        "tmdb-list", "imdb-list", "trakt-list", "tmdb-poster", "details",
        "sync_mode", "subfilters", "and_filters", "sort_title", "content_rating",
        "summary", "tmdb_summary", "tmdb_biography",
        "collection_mode", "collection_order",
        "poster", "tmdb_poster", "tmdb_profile", "file_poster",
        "background", "file_background",
        "name_mapping"
    ]
    print("|\n| Running collection update press Ctrl+C to abort at anytime")
    for c in collections:
        print("| \n|===================================================================================================|\n|")
        print("| Updating collection: {}...".format(c))
        map = {}
        sync_collection = True if plex.sync_mode == "sync" else False
        if "sync_mode" in collections[c]:
            if collections[c]["sync_mode"]:
                if collections[c]["sync_mode"] == "append" or collections[c]["sync_mode"] == "sync":
                    if collections[c]["sync_mode"] == "sync":
                        sync_collection = True
                    else:
                        sync_collection = False
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
        actor_id = None
        actor_method = None
        methods = [m for m in collections[c] if m not in details]
        def alias(filter, alias):
            if filter[-1] == "!":
                return alias[filter[:-1]] + "!"
            elif filter[-4] == ".lte":
                return alias[filter[:-4]] + ".lte"
            elif filter[-4] == ".gte":
                return alias[filter[:-4]] + ".gte"
            else:
                return alias[filter]
        subfilters = []
        if "subfilters" in collections[c]:
            if collections[c]["subfilters"]:
                for sf in collections[c]["subfilters"]:
                    try:
                        final_sf = alias(sf, method_alias)
                        print("| Config Warning: {} subfilter will run as {}".format(sf, final_sf))
                    except KeyError:
                        final_sf = sf
                    if final_sf in movie_only_subfilters and libtype == "show":
                        print("| Config Error: {} subfilter only works for movie libraries".format(final_sf))
                    elif final_sf in all_subfilters:
                        sf_string = final_sf, collections[c]["subfilters"][sf]
                        subfilters.append(sf_string)
                    else:
                        print("| Config Error: {} subfilter not supported".format(sf))
            else:
                print("| Config Error: subfilters attribute is blank")
        and_filters = []
        if "and_filters" in collections[c]:
            if collections[c]["and_filters"]:
                for af in collections[c]["and_filters"]:
                    try:
                        final_af = alias(af, method_alias)
                        print("| Config Warning: {} and_filter will run as {}".format(sf, final_sf))
                    except KeyError:
                        final_af = af
                    method = final_af[:-1] if final_af[-1] == "!" else final_af
                    if final_af in movie_only_filters and libtype == "show":
                        print("| Config Error: {} and_filter only works for movie libraries".format(final_af))
                    elif final_af == "all":
                        print("| Config Error: all cannot be an and_filter")
                    elif method in collections[c] or method + "!" in collections[c]:
                        print("| Config Error: {} cannot be an and_filter while {} or {}! is a filter use it as a subfilter instead".format(final_af, method, method))
                    elif final_af in all_filters:
                        af_string = final_af, collections[c]["and_filters"][af]
                        and_filters.append(af_string)
                    else:
                        print("| Config Error: {} and_filter not supported".format(sf))
            else:
                print("| Config Error: and_filters attribute is blank")
        for m in methods:
            if ("tmdb" in m or "imdb" in m) and not TMDB.valid:
                print("| Config Error: {} skipped. tmdb incorrectly configured".format(m))
            elif (m == "trakt_list" or ("tmdb" in m and plex.library_type == "show")) and not TraktClient.valid:
                print("| Config Error: {} skipped. trakt incorrectly configured".format(m))
            elif m == "tautulli" and not Tautulli.valid:
                print("| Config Error: {} skipped. tautulli incorrectly configured".format(m))
            elif collections[c][m]:
                try:
                    final_method = (method_alias[m[:-1]] + "!") if m[-1] == "!" else method_alias[m]
                    print("| Config Warning: {} filter will run as {}".format(m, final_method))
                except KeyError:
                    final_method = m
                if final_method in show_only_lists and libtype == "movie":
                    print("| Config Error: {} filter only works for show libraries".format(final_method))
                elif (final_method in movie_only_filters or final_method in movie_only_lists) and libtype == "show":
                    print("| Config Error: {} filter only works for movie libraries".format(final_method))
                elif final_method in all_filters or final_method in all_lists:
                    if final_method in ["tautulli", "all"]:
                        values = [collections[c][m]]
                    elif isinstance(collections[c][m], list):
                        values = collections[c][m]
                    else:
                        values = str(collections[c][m]).split(", ")   # Support multiple imdb/tmdb/trakt lists
                    for v in values:
                        add = True
                        v_print = v
                        if final_method == "tmdb_id" and tmdb_id is None:
                            try:
                                tmdb_id = re.search('.*?(\\d+)', str(v)).group(1)
                            except AttributeError:
                                print("| Config Error: TMDb ID: {} is invalid".format(v))
                                add = False
                        try:
                            if final_method in ["tmdb_actor", "tmdb_director", "tmdb_writer"]:
                                name = tmdb_get_summary(config_path, v, "name")
                                if actor_id is None:
                                    actor_id = v
                                    actor_method = final_method
                                v = name
                                if final_method == "tmdb_actor":
                                    final_method = "actor"
                                elif final_method == "tmdb_director":
                                    final_method =  "director"
                                elif final_method == "tmdb_writer":
                                    final_method =  "writer"
                                v_print = v_print + " " + v
                            if final_method == "actor":
                                v = get_actor_rkey(plex, v)
                        except ValueError as e:
                            print(e)
                            add = False
                        if add:
                            print("| \n| Processing {}: {}".format(final_method, v_print))
                            if final_method == "studio" and libtype == "show":
                                final_method = "network"
                            try:
                                missing, map = add_to_collection(config_path, plex, final_method, v, c, map, and_filters, subfilters)
                            #except UnboundLocalError as e:
                            #    missing, map = add_to_collection(config_path, plex, final_method, v, c, map)               # No sub-filters
                            except (KeyError, ValueError, SystemExit) as e:
                                print(e)
                                missing = False
                            if missing:
                                if libtype == "movie":
                                    method_name = "IMDb" if "imdb" in m else "Trakt" if "trakt" in m else "TMDb"
                                    if m in ["trakt_list", "tmdb_list", "imdb_list"]:
                                        print("| {} missing movie{} from {} List: {}".format(len(missing), "s" if len(missing) > 1 else "", method_name, v))
                                    elif m == "tmdb_collection":
                                        print("| {} missing movie{} from {} Collection: {}".format(len(missing), "s" if len(missing) > 1 else "", method_name, v))
                                    elif m == "trakt_trending":
                                        print("| {} missing movie{} from {} List: Trending (top {})".format(len(missing), "s" if len(missing) > 1 else "", method_name, v))
                                    else:
                                        print("| {} ID: {} missing".format(method_name, v))
                                    if Radarr.valid:
                                        radarr = Radarr(config_path)
                                        if radarr.add_movie:
                                            print("| Adding missing movies to Radarr")
                                            add_to_radarr(config_path, missing)
                                        elif not headless and radarr.add_movie is None and input("| Add missing movies to Radarr? (y/n): ").upper() == "Y":
                                            add_to_radarr(config_path, missing)
                                elif libtype == "show":
                                    method_name = "Trakt" if "trakt" in m else "TVDb" if "tvdb" in m else "TMDb"
                                    if m in ["trakt_list", "tmdb_list"]:
                                        print("| {} missing show{} from {} List: {}".format(len(missing), "s" if len(missing) > 1 else "", method_name, v))
                                    elif m == "trakt_trending":
                                        print("| {} missing show{} from {} List: Trending (top {})".format(len(missing), "s" if len(missing) > 1 else "", method_name, v))
                                    else:
                                        print("| {} ID: {} missing".format(method_name, v))

                                    # if not skip_sonarr:
                                    #     if input("Add missing shows to Sonarr? (y/n): ").upper() == "Y":
                                    #         add_to_radarr(missing_shows)
                else:
                    print("| Config Error: {} attribute not supported".format(m))
            else:
                print("| Config Error: {} attribute is blank".format(m))

        for ratingKey, item in map.items():
            if item is not None:
                print("| {} Collection | - | {}".format(c, item.title))
                item.removeCollection(c)

        print("| ")

        if "tmdb-list" in collections[c]:
            print("| Config Error: Please change the attribute tmdb-list to tmdb_collection")
        if "imdb-list" in collections[c]:
            print("| Config Error: Please change the attribute imdb-list to imdb_list")
        if "trakt-list" in collections[c]:
            print("| Config Error: Please change the attribute trakt-list to trakt_list")
        if "details" in collections[c]:
            print("| Config Error: Please remove the attribute details attribute all its old sub-attributes should be one level higher")
        if "tmdb-poster" in collections[c]:
            print("| Config Error: Please change the attribute tmdb-poster to tmdb_poster")
        if "subfilters" in collections[c] and collections[c]["subfilters"]:
            if "video-resolution" in collections[c]["subfilters"]:
                print("| Config Error: Please change the subfilter attribute video-resolution to video_resolution")
            if "audio-language" in collections[c]["subfilters"]:
                print("| Config Error: Please change the subfilter attribute audio-language to audio_language")
            if "subtitle-language" in collections[c]["subfilters"]:
                print("| Config Error: Please change the subfilter attribute subtitle-language to subtitle_language")

        plex_collection = get_collection(plex, c, headless)

        if not isinstance(plex_collection, Collections):
            continue       # No collections created with requested criteria

        if not no_meta:
            def edit_value (plex_collection, name, group, key=None):
                if key is None:
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
                if collections[c]["summary"]:
                    summary = collections[c]["summary"]
                else:
                    print("| Config Error: summary attribute is blank")
            elif "tmdb_summary" in collections[c]:
                if TMDB.valid:
                    if collections[c]["tmdb_summary"]:
                        try:
                            summary = tmdb_get_summary(config_path, collections[c]["tmdb_summary"], "overview")
                        except ValueError as e:
                            print(e)
                    else:
                        print("| Config Error: tmdb_summary attribute is blank")
                else:
                    print("| Config Error: tmdb_summary skipped. tmdb incorrectly configured")
            elif "tmdb_biography" in collections[c]:
                if TMDB.valid:
                    if collections[c]["tmdb_biography"]:
                        try:
                            summary = tmdb_get_summary(config_path, collections[c]["tmdb_biography"], "biography")
                        except ValueError as e:
                            print(e)
                    else:
                        print("| Config Error: tmdb_biography attribute is blank")
                else:
                    print("| Config Error: tmdb_biography skipped. tmdb incorrectly configured")
            elif actor_id and TMDB.valid:
                try:
                    summary = tmdb_get_summary(config_path, actor_id, "biography")
                except ValueError as e:
                    pass
            elif tmdb_id and TMDB.valid:
                try:
                    summary = tmdb_get_summary(config_path, tmdb_id, "overview")
                except ValueError as e:
                    pass

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
                        if collection_mode == 'hide_items':
                            collection_mode = 'hideItems'
                        if collection_mode == 'show_items':
                            collection_mode = 'showItems'
                        plex_collection.modeUpdate(mode=collection_mode)
                        print("| Detail: collection_mode updated to {}".format(collection_mode))
                    else:
                        print("| Config Error: {} collection_mode Invalid\n| \tdefault (Library default)\n| \thide (Hide Collection)\n| \thide_items (Hide Items in this Collection)\n| \tshow_items (Show this Collection and its Items)".format(collection_mode))
                else:
                    print("| Config Error: collection_mode attribute is blank")

            # Handle collection collection_order
            if "collection_order" in collections[c]:
                if collections[c]["collection_order"]:
                    collection_order = collections[c]["collection_order"]
                    if collection_order in ('release', 'alpha'):
                        plex_collection.sortUpdate(sort=collection_order)
                        print("| Detail: collection_order updated to {}".format(collection_order))
                    else:
                        print("| Config Error: {} collection_order Invalid\n| \trelease (Order Collection by release dates)\n| \talpha (Order Collection Alphabetically)".format(collection_order))
                else:
                    print("| Config Error: collection_order attribute is blank")

        tmdb_url_prefix = "https://image.tmdb.org/t/p/original"
        if not no_images:
            posters_found = []
            backgrounds_found = []
            # Handle collection posters
            if "poster" in collections[c]:
                if collections[c]["poster"]:
                    posters_found.append(["url", collections[c]["poster"], "poster"])
                else:
                    print("| Config Error: poster attribute is blank")
            if "tmdb_poster" in collections[c]:
                if TMDB.valid:
                    if collections[c]["tmdb_poster"]:
                        try:
                            posters_found.append(["url", tmdb_url_prefix + tmdb_get_summary(config_path, collections[c]["tmdb_poster"], "poster_path"), "tmdb_poster"])
                        except ValueError as e:
                            print(e)
                    else:
                        print("| Config Error: tmdb_poster attribute is blank")
                else:
                    print("| Config Error: tmdb_poster skipped. tmdb incorrectly configured")
            if "tmdb_profile" in collections[c]:
                if TMDB.valid:
                    if collections[c]["tmdb_profile"]:
                        try:
                            posters_found.append(["url", tmdb_url_prefix + tmdb_get_summary(config_path, collections[c]["tmdb_profile"], "profile_path"), "tmdb_profile"])
                        except ValueError as e:
                            print(e)
                    else:
                        print("| Config Error: tmdb_profile attribute is blank")
                else:
                    print("| Config Error: tmdb_profile skipped. tmdb incorrectly configured")
            if "file_poster" in collections[c]:
                if collections[c]["file_poster"]:
                    posters_found.append(["file", collections[c]["file_poster"], "file_poster"])
                else:
                    print("| Config Error: file_poster attribute is blank")

            # Handle collection backgrounds
            if "background" in collections[c]:
                if collections[c]["background"]:
                    backgrounds_found.append(["url", collections[c]["background"], "background"])
                else:
                    print("| Config Error: background attribute is blank")
            if "tmdb_background" in collections[c]:
                if TMDB.valid:
                    if collections[c]["tmdb_background"]:
                        try:
                            backgrounds_found.append(["url", tmdb_url_prefix + tmdb_get_summary(config_path, collections[c]["tmdb_background"], "backdrop_path"), "tmdb_background"])
                        except ValueError as e:
                            print(e)
                    else:
                        print("| Config Error: tmdb_background attribute is blank")
                else:
                    print("| Config Error: tmdb_background skipped. tmdb incorrectly configured")
            if "file_background" in collections[c]:
                if collections[c]["file_background"]:
                    backgrounds_found.append(["file", collections[c]["file_background"], "file_background"])
                else:
                    print("| Config Error: file_background attribute is blank")


            # Handle Image Server
            image_server = ImageServer(config_path)
            if image_server.valid:
                name_mapping = c
                if "name_mapping" in collections[c]:
                    if collections[c]["name_mapping"]:
                        name_mapping = collections[c]["name_mapping"]
                    else:
                        print("| Config Error: name_mapping attribute is blank")
                if image_server.poster:
                    path = os.path.join(image_server.poster, "{}.*".format(name_mapping))
                    matches = glob.glob(path)
                    if len(matches) > 0 or len(posters_found) > 0:
                        for match in matches:
                            posters_found.append(["file", os.path.abspath(match), "poster_directory"])
                    else:
                        print("| poster not found at: {}".format(os.path.abspath(path)))
                if image_server.background:
                    path = os.path.join(image_server.background, "{}.*".format(name_mapping))
                    matches = glob.glob(path)
                    if len(matches) > 0 or len(backgrounds_found) > 0:
                        for match in matches:
                            backgrounds_found.append(["file", os.path.abspath(match), "background_directory"])
                    else:
                        print("| background not found at: {}".format(os.path.abspath(path)))
                if image_server.image:
                    path = os.path.join(image_server.image, "{}".format(name_mapping), "poster.*")
                    matches = glob.glob(path)
                    if len(matches) > 0 or len(posters_found) > 0:
                        for match in matches:
                            posters_found.append(["file", os.path.abspath(match), "image_directory"])
                    else:
                        print("| poster not found at: {}".format(os.path.abspath(path)))
                    path = os.path.join(image_server.image, "{}".format(name_mapping), "background.*")
                    matches = glob.glob(path)
                    if len(matches) > 0 or len(backgrounds_found) > 0:
                        for match in matches:
                            backgrounds_found.append(["file", os.path.abspath(match), "image_directory"])
                    else:
                        print("| background not found at: {}".format(os.path.abspath(path)))

            # Pick Images
            def choose_from_list (list_type, item_list, headless):
                if item_list:
                    if len(item_list) == 1 or (len(item_list) > 0 and headless):
                        return item_list[0]
                    names = ["| {}) [{}] {}".format(i, item[0], item[1]) for i, item in enumerate(item_list, start=1)]
                    print("| 0) Do Nothing")
                    print("\n".join(names))
                    while True:
                        try:
                            selection = int(input("| Choose {} number: ".format(list_type))) - 1
                            if selection >= 0:
                                return item_list[selection]
                            elif selection == -1:
                                return None
                            else:
                                print("| Invalid entry")
                        except (IndexError, ValueError) as E:
                            print("| Invalid entry")
                else:
                    return None
            poster = choose_from_list("poster", posters_found, headless)
            background = choose_from_list("background", backgrounds_found, headless)

            # Special case fall back for tmdb_id tag if no other poster or background is found
            if not poster and TMDB.valid:
                try:
                    if actor_id:
                        poster = ["url", tmdb_url_prefix + tmdb_get_summary(config_path, actor_id, "profile_path"), actor_method]
                    elif tmdb_id:
                        poster = ["url", tmdb_url_prefix + tmdb_get_summary(config_path, tmdb_id, "poster_path"), "tmdb_id"]
                except ValueError as e:
                    pass
            if not background and TMDB.valid and tmdb_id:
                try:
                    background = ["url", tmdb_url_prefix + tmdb_get_summary(config_path, tmdb_id, "backdrop_path"), "tmdb_id"]
                except ValueError as e:
                    pass

            # Update poster
            if poster:
                if poster[0] == "url":
                    plex_collection.uploadPoster(url=poster[1])
                else:
                    plex_collection.uploadPoster(filepath=poster[1])
                print("| Detail: {} updated poster to [{}] {}".format(poster[2], poster[0], poster[1]))

            # Update background
            if background:
                if background[0] == "url":
                    plex_collection.uploadArt(url=background[1])
                else:
                    plex_collection.uploadArt(filepath=background[1])
                print("| Detail: {} updated background to [{}] {}".format(background[2], background[0], background[1]))

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
                            try:
                                a_rkey = get_actor_rkey(plex, value)
                                if config_update:
                                    modify_config(config_path, collection_name, method, value)
                                else:
                                    add_to_collection(config_path, plex, method, a_rkey, selected_collection.title)
                            except ValueError as e:
                                print(e)

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
print("| Version 2.3.0")
print("| Locating config...")
config_path = None
app_dir = os.path.dirname(os.path.abspath(__file__))


if args.config_path and os.path.exists(args.config_path):
    config_path = os.path.abspath(args.config_path)    # Set config_path from command line switch
elif args.config_path and not os.path.exists(args.config_path):
    sys.exit("| Config Error: config not found at {}".format(os.path.abspath(args.config_path)))
elif os.path.exists(os.path.join(app_dir, "config.yml")):
    config_path = os.path.abspath(os.path.join(app_dir, "config.yml"))    # Set config_path from app_dir
elif os.path.exists(os.path.join(app_dir, "..", "config", "config.yml")):
    config_path = os.path.abspath(os.path.join(app_dir, "..", "config", "config.yml"))    # Set config_path from config_dir
else:
    sys.exit("| Config Error: No config found, exiting")

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
            try:
                a_rkey = get_actor_rkey(plex, actor)
                c_name = input("| Enter collection name: ")
                add_to_collection(config_path, plex, "actors", a_rkey, c_name)
            except ValueError as e:
                print(e)

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
