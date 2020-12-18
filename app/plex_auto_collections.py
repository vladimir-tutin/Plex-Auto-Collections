try:
    import os
    import argparse
    import re
    import sys
    import threading
    import glob
    import datetime
    from plexapi.server import PlexServer
    from plexapi.video import Movie
    from plexapi.video import Show
    from plexapi.library import MovieSection
    from plexapi.library import ShowSection
    from plexapi.library import Collections
    from plex_tools import get_map
    from plex_tools import add_to_collection
    from plex_tools import delete_collection
    from plex_tools import get_actor_rkey
    from plex_tools import get_collection
    from plex_tools import get_item
    from imdb_tools import tmdb_get_metadata
    from imdb_tools import imdb_get_ids
    from config_tools import Config
    from config_tools import Plex
    from config_tools import Radarr
    from config_tools import TMDB
    from config_tools import Tautulli
    from config_tools import TraktClient
    from config_tools import ImageServer
    from config_tools import modify_config
    from config_tools import check_for_attribute
    from radarr_tools import add_to_radarr
    from urllib.parse import urlparse
except ModuleNotFoundError:
    print('|\n| Requirements Error: Please install requirements using "pip install -r requirements.txt"\n|')
    sys.exit(0)

def regex_first_int(data, method, id_type="number", default=None):
    try:
        id = re.search('(\\d+)', str(data)).group(1)
        if len(str(id)) != len(str(data)):
            print("| Config Warning: {} can be replaced with {}".format(data, id))
        return id
    except AttributeError:
        if default is None:
            raise ValueError("| Config Error: Skipping {} failed to parse {} from {}".format(method, id_type, data))
        else:
            print("| Config Error: {} failed to parse {} from {} using {} as default".format(method, id_type, data, default))
            return default

def get_attribute_list(values_to_parse):
    return values_to_parse if isinstance(values_to_parse, list) else str(values_to_parse).split(", ")

def get_int_attribute_list(method_to_parse, values_to_parse, id_type):
    values_to_parse = get_attribute_list(values_to_parse)
    new_values = []
    for v in values_to_parse:
        try:
            new_values.append(regex_first_int(v, method_to_parse, id_type))
        except ValueError as e:
            print(e)
    return new_values

def get_method_pair_int(method_to_parse, values_to_parse, id_type):
    return (method_to_parse, get_int_attribute_list(method_to_parse, values_to_parse, id_type))

def get_method_pair_tmdb(method_to_parse, values_to_parse, id_type):
    values = get_attribute_list(values_to_parse)
    new_ids = []
    for v in values:
        try:
            id = regex_first_int(v, method_to_parse, id_type)
            tmdb_get_metadata(config_path, id, "overview")
            new_ids.append(id)
        except ValueError as e:
            print(e)
    return (method_to_parse, new_ids)

def get_method_pair_year(method_to_parse, values_to_parse):
    years = get_attribute_list(values_to_parse)
    final_years = []
    current_year = datetime.datetime.now().year
    for year in years:
        try:
            year_range = re.search('(\\d{4})-(\\d{4}|NOW)', str(year))
            start = year_range.group(1)
            end = year_range.group(2)
            if end == "NOW":
                end = current_year
            if int(start) < 1800 or int(start) > current_year:
                print("| Config Error: Skipping {} starting year {} must be between 1800 and {}".format(method_to_parse, start, current_year))
            elif int(end) < 1800 or int(end) > current_year:
                print("| Config Error: Skipping {} ending year {} must be between 1800 and {}".format(method_to_parse, end, current_year))
            elif int(start) > int(end):
                print("| Config Error: Skipping {} starting year {} cannot be greater then ending year {}".format(method_to_parse, start, end))
            else:
                for i in range(int(start), int(end) + 1):
                    final_years.append(i)
        except AttributeError:
            try:
                id = re.search('(\\d+)', str(year)).group(1)
                if len(str(id)) != len(str(year)):
                    print("| Config Warning: {} can be replaced with {}".format(year, id))
                final_years.append(id)
            except AttributeError:
                print("| Config Error: Skipping {} failed to parse year from {}".format(method_to_parse, year))
    return (method_to_parse, final_years)

def update_from_config(config_path, plex, headless=False, no_meta=False, no_images=False):
    config = Config(config_path)
    collections = config.collections
    if not headless:
        print("|\n|===================================================================================================|")
    if isinstance(plex.Library, MovieSection):
        radarr = Radarr(config_path) if Radarr.valid else None
        libtype = "movie"
    elif isinstance(plex.Library, ShowSection):
        radarr = None
        libtype = "show"
    plex_map = get_map(config_path, plex)
    alias = {
        "actors": "actor", "role": "actor", "roles": "actor",
        "content_ratings": "content_rating", "contentRating": "content_rating", "contentRatings": "content_rating",
        "countries": "country",
        "decades": "decade",
        "directors": "director",
        "genres": "genre",
        "studios": "studio", "network": "studio", "networks": "studio",
        "years": "year",
        "writers": "writer",
        "tmdb-list": "tmdb_collection",
        "tmdb-poster": "tmdb_poster",
        "imdb-list": "imdb_list",
        "trakt-list": "trakt_list",
        "video-resolution": "video_resolution",
        "audio-language": "audio_language",
        "subtitle-language": "subtitle_language",
        "subfilters": "filters",
        "collection_sort": "collection_order"
    }
    pretty_names = {
        "tmdb_collection": "TMDb Collection",
        "tmdb_id": "TMDb ID",
        "tmdb_company": "TMDb Company",
        "tmdb_network": "TMDb Network",
        "tmdb_discover": "TMDb Discover",
        "tmdb_popular": "TMDb Popular",
        "tmdb_top_rated": "TMDb Top Rated",
        "tmdb_now_playing": "TMDb Now Playing",
        "tmdb_trending_daily": "TMDb Trending Daily",
        "tmdb_trending_weekly": "TMDb Trending Weekly",
        "tmdb_list": "TMDb List",
        "tmdb_movie": "TMDb Movie",
        "tmdb_show": "TMDb Show",
        "tvdb_show": "TVDb Show",
        "imdb_list": "IMDb List",
        "trakt_list": "Trakt List",
        "trakt_trending": "Trakt Trending",
        "trakt_watchlist": "Trakt Watchlist"
    }
    all_lists = [
        "plex_search",
        "plex_collection",
        "tmdb_collection",
        "tmdb_id",
        "tmdb_actor",
        "tmdb_director",
        "tmdb_writer",
        "tmdb_company",
        "tmdb_network",
        "tmdb_discover",
        "tmdb_popular",
        "tmdb_top_rated",
        "tmdb_now_playing",
        "tmdb_trending_daily",
        "tmdb_trending_weekly",
        "tmdb_list",
        "tmdb_movie",
        "tmdb_show",
        "tvdb_show",
        "imdb_list",
        "trakt_list",
        "trakt_trending",
        "trakt_watchlist",
        "tautulli"
    ]
    plex_searches = [
        "actor", #"actor.not", # Waiting on PlexAPI to fix issue
        "country", #"country.not",
        "decade", #"decade.not",
        "director", #"director.not",
        "genre", #"genre.not",
        "studio", #"studio.not",
        "year", #"year.not",
        "writer", #"writer.not",
        "tmdb_actor", "tmdb_director", "tmdb_writer"
    ]
    show_only_lists = [
        "tmdb_show",
        "tvdb_show",
        "tmdb_network"
    ]
    movie_only_lists = [
        "tmdb_collection",
        "tmdb_id",
        "tmdb_actor",
        "tmdb_company",
        "tmdb_director",
        "tmdb_writer",
        "tmdb_now_playing",
        "tmdb_movie",
        "imdb_list",
    ]
    movie_only_searches = [
        "actor", #"actor.not", # Waiting on PlexAPI to fix issue
        "country", #"country.not",
        "decade", #"decade.not",
        "director", #"director.not",
        "writer", #"writer.not",
        "tmdb_actor", "tmdb_director", "tmdb_writer"
    ]
    all_filters = [
        "actor", "actor.not",
        "content_rating", "content_rating.not",
        "country", "country.not",
        "director", "director.not",
        "genre", "genre.not",
        "studio", "studio.not",
        "year", "year.not", "year.gte", "year.lte",
        "writer", "writer.not",
        "rating.gte", "rating.lte",
        "max_age",
        "originally_available.gte", "originally_available.lte",
        "video_resolution", "video_resolution.not",
        "audio_language", "audio_language.not",
        "subtitle_language", "subtitle_language.not",
        "plex_collection", "plex_collection.not"
    ]
    movie_only_filters = [
        "country", "country.not",
        "director", "director.not",
        "writer", "writer.not",
        "video_resolution", "video_resolution.not",
        "audio_language", "audio_language.not",
        "subtitle_language", "subtitle_language.not"
    ]
    all_details = [
        "sort_title", "content_rating",
        "summary", "tmdb_summary", "tmdb_biography",
        "collection_mode", "collection_order",
        "poster", "tmdb_poster", "tmdb_profile", "file_poster",
        "background", "file_background",
        "name_mapping", "add_to_radarr"
    ]
    discover_movie = [
        "language", "with_original_language", "region", "sort_by",
        "certification_country", "certification", "certification.lte", "certification.gte",
        "include_adult",
        "primary_release_year", "primary_release_date.gte", "primary_release_date.lte",
        "release_date.gte", "release_date.lte", "year",
        "vote_count.gte", "vote_count.lte",
        "vote_average.gte", "vote_average.lte",
        "with_cast", "with_crew", "with_people",
        "with_companies",
        "with_genres", "without_genres",
        "with_keywords", "without_keywords",
        "with_runtime.gte", "with_runtime.lte"
    ]
    discover_tv = [
        "language", "with_original_language", "timezone", "sort_by",
        "air_date.gte", "air_date.lte",
        "first_air_date.gte", "first_air_date.lte", "first_air_date_year",
        "vote_count.gte", "vote_count.lte",
        "vote_average.gte", "vote_average.lte",
        "with_genres", "without_genres",
        "with_keywords", "without_keywords",
        "with_networks", "with_companies",
        "with_runtime.gte", "with_runtime.lte",
        "include_null_first_air_dates",
        "screened_theatrically"
    ]
    discover_movie_sort = [
        "popularity.asc", "popularity.desc",
        "release_date.asc", "release_date.desc",
        "revenue.asc", "revenue.desc",
        "primary_release_date.asc", "primary_release_date.desc",
        "original_title.asc", "original_title.desc",
        "vote_average.asc", "vote_average.desc",
        "vote_count.asc", "vote_count.desc"
    ]
    discover_tv_sort = [
        "vote_average.desc", "vote_average.asc",
        "first_air_date.desc", "first_air_date.asc",
        "popularity.desc", "popularity.asc"
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
            try:
                plex_collection = get_collection(plex, c, headless)
                for item in plex_collection.children:
                    map[item.ratingKey] = item
            except ValueError as e:
                print("| Config Error: {}".format(e))
        else:
            print("| Sync Mode: append")

        tmdb_id = None
        person_id = None
        person_method = None
        details = {}
        methods = []
        filters = []
        posters_found = []
        backgrounds_found = []

        # Loops through every method and validates to make sure that that the input is right where it can
        # After this loop all the methods and values should be defined in methods, filters, and details
        for m in collections[c]:
            if ("tmdb" in m or "imdb" in m) and not TMDB.valid:
                print("| Config Error: {} skipped. tmdb incorrectly configured".format(m))
                map = {}
            elif "trakt" in m and not TraktClient.valid:
                print("| Config Error: {} skipped. trakt incorrectly configured".format(m))
                map = {}
            elif m == "tautulli" and not Tautulli.valid:
                print("| Config Error: {} skipped. tautulli incorrectly configured".format(m))
                map = {}
            elif collections[c][m]:
                if m in alias:
                    method_name = alias[m]
                    print("| Config Warning: {} attribute will run as {}".format(m, method_name))
                else:
                    method_name = m
                def check_details(check_name, check_value):
                    if check_name in ["tmdb_summary", "tmdb_biography"]:
                        if check_name == "tmdb_summary":
                            tmdb_type = "overview"
                        elif check_name == "tmdb_biography":
                            tmdb_type = "biography"
                        try:
                            details["summary"] = tmdb_get_metadata(config_path, check_value, tmdb_type)
                        except ValueError as e:
                            print(e)
                    elif check_name == "collection_mode":
                        if check_value in ('default', 'hide', 'hide_items', 'show_items', 'hideItems', 'showItems'):
                            if check_value == 'hide_items':
                                details[check_name] = 'hideItems'
                            elif check_value == 'show_items':
                                details[check_name] = 'showItems'
                            else:
                                details[check_name] = check_value
                        else:
                            print("| Config Error: {} collection_mode Invalid\n| \tdefault (Library default)\n| \thide (Hide Collection)\n| \thide_items (Hide Items in this Collection)\n| \tshow_items (Show this Collection and its Items)".format(check_value))
                    elif check_name == "collection_order":
                        if check_value in ('release', 'alpha'):
                            details[check_name] = check_value
                        else:
                            print("| Config Error: {} collection_order Invalid\n| \trelease (Order Collection by release dates)\n| \talpha (Order Collection Alphabetically)".format(check_value))
                    elif check_name == "poster":
                        posters_found.append(["url", check_value, check_name])
                    elif check_name == "tmdb_poster":
                        try:
                            posters_found.append(["url", tmdb_get_metadata(config_path, check_value, "poster"), check_name])
                        except ValueError as e:
                            print(e)
                    elif check_name == "tmdb_profile":
                        try:
                            posters_found.append(["url", tmdb_get_metadata(config_path, check_value, "profile"), check_name])
                        except ValueError as e:
                            print(e)
                    elif check_name == "file_poster":
                        if os.path.exists(check_value):
                            posters_found.append(["file", os.path.abspath(check_value), check_name])
                        else:
                            print("| Config Error: Poster Path Does Not Exist: {}".format(os.path.abspath(check_value)))
                    elif check_name == "background":
                        backgrounds_found.append(["url", check_value, check_name])
                    elif check_name == "tmdb_background":
                        try:
                            backgrounds_found.append(["url", tmdb_get_metadata(config_path, check_value, "backdrop"), check_name])
                        except ValueError as e:
                            print(e)
                    elif check_name == "file_background":
                        if os.path.exists(check_value):
                            backgrounds_found.append(["file", os.path.abspath(check_value), check_name])
                        else:
                            print("| Config Error: Background Path Does Not Exist: {}".format(os.path.abspath(check_value)))
                    elif check_name == "add_to_radarr":
                        if check_value == True or check_value == False:
                            details[check_name] = check_value
                        else:
                            print("| Config Error: add_to_radarr must be either true or false")
                    else:
                        details[check_name] = check_value
                if method_name in show_only_lists and libtype == "movie":
                    print("| Config Error: {} attribute only works for show libraries".format(method_name))
                elif (method_name in movie_only_filters or method_name in movie_only_lists) and libtype == "show":
                    print("| Config Error: {} attribute only works for movie libraries".format(method_name))
                elif method_name == "details":
                    print("| Config Error: Please remove the details attribute all its old sub-attributes should be one level higher")
                    for detail_m in collections[c][m]:
                        if detail_m in alias:
                            detail_name = alias[detail_m]
                            print("| Config Warning: {} attribute will run as {}".format(detail_m, detail_name))
                        else:
                            detail_name = detail_m
                        if detail_name in all_details:
                            check_details(detail_name, collections[c][m][detail_m])
                        else:
                            print("| Config Error: {} attribute not supported".format(detail_name))
                elif method_name in all_details:
                    check_details(method_name, collections[c][m])
                elif method_name in movie_only_searches and libtype == "show":
                    print("| Config Error: {} plex search only works for movie libraries".format(method_name))
                elif method_name in ["year", "year.not"]:
                    methods.append(("plex_search", [[get_method_pair_year(method_name, collections[c][m])]]))
                elif method_name in ["decade", "decade.not"]:
                    methods.append(("plex_search", [[get_method_pair_int(method_name, collections[c][m], method_name[:-4] if method_name.endswith(".not") else method_name)]]))
                elif method_name in ["tmdb_actor", "tmdb_director", "tmdb_writer"]:
                    ids = get_int_attribute_list(method_name, collections[c][m], "TMDb Person ID")
                    new_ids = []
                    for id in ids:
                        try:
                            name = tmdb_get_metadata(config_path, id, "name")
                            if person_id is None:
                                if "summary" not in details:
                                    details["summary"] = tmdb_get_metadata(config_path, id, "biography")
                                details["poster"] = ["url", tmdb_get_metadata(config_path, id, "profile"), method_name]
                                person_id = id
                                person_method = method_name
                            if method_name == "tmdb_actor":
                                get_actor_rkey(plex, name)
                            new_ids.append(name)
                        except ValueError as e:
                            print(e)
                    methods.append(("plex_search", [[(method_name[5:], new_ids)]]))
                elif method_name in plex_searches:
                    methods.append(("plex_search", [[(method_name, get_attribute_list(collections[c][m]))]]))
                elif method_name == "plex_collection":
                    collection_list = collections[c][m] if isinstance(collections[c][m], list) else [collections[c][m]]
                    final_collections = []
                    for new_collection in collection_list:
                        try:
                            final_collections.append(get_collection(plex, str(new_collection), headless))
                        except ValueError as e:
                            print("| Config Error: {} {} Not Found".format(method_name, new_collection))
                    if len(final_collections) > 0:
                        methods.append(("plex_collection", final_collections))
                elif method_name == "tmdb_collection":
                    methods.append(get_method_pair_tmdb(method_name, collections[c][m], "TMDb Collection ID"))
                elif method_name == "tmdb_company":
                    methods.append(get_method_pair_int(method_name, collections[c][m], "TMDb Company ID"))
                elif method_name == "tmdb_id":
                    id = get_method_pair_tmdb(method_name, collections[c][m], "TMDb ID")
                    if tmdb_id is None:
                        if "summary" not in details:
                            try:
                                details["summary"] = tmdb_get_metadata(config_path, id[1][0], "overview")
                            except ValueError as e:
                                print(e)
                        try:
                            details["poster"] = ["url", tmdb_get_metadata(config_path, id[1][0], "poster"), method_name]
                        except ValueError as e:
                            print(e)
                        try:
                            details["background"] = ["url", tmdb_get_metadata(config_path, id[1][0], "backdrop"), method_name]
                        except ValueError as e:
                            print(e)
                        tmdb_id = id[1][0]
                    methods.append(id)
                elif method_name in ["tmdb_popular", "tmdb_top_rated", "tmdb_now_playing", "tmdb_trending_daily", "tmdb_trending_weekly"]:
                    methods.append((method_name, [regex_first_int(collections[c][m], method_name, default=20)]))
                elif method_name == "tmdb_list":
                    methods.append(get_method_pair_int(method_name, collections[c][m], "TMDb List ID"))
                elif method_name == "tmdb_movie":
                    methods.append(get_method_pair_tmdb(method_name, collections[c][m], "TMDb Movie ID"))
                elif method_name == "tmdb_network":
                    methods.append(get_method_pair_int(method_name, collections[c][m], "TMDb Network ID"))
                elif method_name == "tmdb_show":
                    methods.append(get_method_pair_tmdb(method_name, collections[c][m], "TMDb Show ID"))
                elif method_name == "tvdb_show":
                    methods.append(get_method_pair_int(method_name, collections[c][m], "TVDb Show ID"))
                elif method_name == "imdb_list":
                    imdb_lists = get_attribute_list(collections[c][m])
                    good_lists = []
                    for imdb_url in imdb_lists:
                        title_ids = imdb_get_ids(plex, imdb_url)
                        if title_ids:
                            good_lists.append((imdb_url, title_ids))
                    methods.append((method_name, good_lists))
                elif method_name == "trakt_list": #TODO: validate
                    methods.append((method_name, get_attribute_list(collections[c][m])))
                elif method_name == "trakt_trending":
                    methods.append((method_name, [regex_first_int(collections[c][m], method_name, default=30)]))
                elif method_name == "trakt_watchlist":
                    methods.append((method_name, get_attribute_list(collections[c][m])))
                elif method_name in ["filters", "plex_search", "tmdb_discover", "tautulli"]:
                    if isinstance(collections[c][m], dict):
                        if method_name == "filters":
                            for filter in collections[c][m]:
                                if filter in alias or (filter.endswith(".not") and filter[:-4] in alias):
                                    final_filter = (alias[filter[:-4]] + filter[-4:]) if filter.endswith(".not") else alias[filter]
                                    print("| Config Warning: {} filter will run as {}".format(filter, final_filter))
                                else:
                                    final_filter = filter
                                if final_filter in movie_only_filters and libtype == "show":
                                    print("| Config Error: {} filter only works for movie libraries".format(final_filter))
                                elif final_filter in all_filters:
                                    filters.append((final_filter, collections[c][m][filter])) #TODO: validate filters contents
                                else:
                                    print("| Config Error: {} filter not supported".format(filter))
                        elif method_name == "plex_search":
                            search = []
                            searches_used = []
                            for search_attr in collections[c][m]:
                                if search_attr in alias or (search_attr.endswith(".not") and search_attr[:-4] in alias):
                                    final_attr = (alias[search_attr[:-4]] + search_attr[-4:]) if search_attr.endswith(".not") else alias[search_attr]
                                    print("| Config Warning: {} plex search attribute will run as {}".format(search_attr, final_attr))
                                else:
                                    final_attr = search_attr
                                if final_attr in movie_only_searches and libtype == "show":
                                    print("| Config Error: {} plex search attribute only works for movie libraries".format(final_attr))
                                elif (final_attr[:-4] if final_attr.endswith(".not") else final_attr) in searches_used:
                                    print("| Config Error: Only one instance of {} can be used try using it as a filter instead".format(final_attr))
                                elif final_attr in ["year", "year.not"]:
                                    year_pair = get_method_pair_year(final_attr, collections[c][m][search_attr])
                                    if len(year_pair[1]) > 0:
                                        searches_used.append(final_attr[:-4] if final_attr.endswith(".not") else final_attr)
                                        search.append(get_method_pair_int(final_attr, year_pair[1], final_attr[:-4] if final_attr.endswith(".not") else final_attr))
                                elif final_attr in plex_searches:
                                    if final_attr.startswith("tmdb_"):
                                        final_attr = final_attr[5:]
                                    searches_used.append(final_attr[:-4] if final_attr.endswith(".not") else final_attr)
                                    search.append((final_attr, get_attribute_list(collections[c][m][search_attr])))
                                else:
                                    print("| Config Error: {} plex search attribute not supported".format(search_attr))
                            methods.append((method_name, [search]))
                        elif method_name == "tmdb_discover":
                            new_dictionary = {"limit": 100}
                            for attr in collections[c][m]:
                                if collections[c][m][attr]:
                                    attr_data = collections[c][m][attr]
                                    if (libtype == "movie" and attr in discover_movie) or (libtype == "show" and attr in discover_tv):
                                        if attr == "language":
                                            if re.compile("([a-z]{2})-([A-Z]{2})").match(str(attr_data)):
                                                new_dictionary[attr] = str(attr_data)
                                            else:
                                                print("| Config Error: Skipping {} attribute {}: {} must match pattern ([a-z]{2})-([A-Z]{2}) e.g. en-US".format(m, attr, attr_data))
                                        elif attr == "region":
                                            if re.compile("^[A-Z]{2}$").match(str(attr_data)):
                                                new_dictionary[attr] = str(attr_data)
                                            else:
                                                print("| Config Error: Skipping {} attribute {}: {} must match pattern ^[A-Z]{2}$ e.g. US".format(m, attr, attr_data))
                                        elif attr == "sort_by":
                                            if (libtype == "movie" and attr_data in discover_movie_sort) or (libtype == "show" and attr_data in discover_tv_sort):
                                                new_dictionary[attr] = attr_data
                                            else:
                                                print("| Config Error: Skipping {} attribute {}: {} is invalid".format(m, attr, attr_data))
                                        elif attr == "certification_country":
                                            if "certification" in collections[c][m] or "certification.lte" in collections[c][m] or "certification.gte" in collections[c][m]:
                                                new_dictionary[attr] = attr_data
                                            else:
                                                print("| Config Error: Skipping {} attribute {}: must be used with either certification, certification.lte, or certification.gte".format(m, attr))
                                        elif attr in ["certification", "certification.lte", "certification.gte"]:
                                            if "certification_country" in collections[c][m]:
                                                new_dictionary[attr] = attr_data
                                            else:
                                                print("| Config Error: Skipping {} attribute {}: must be used with certification_country".format(m, attr))
                                        elif attr in ["include_adult", "include_null_first_air_dates", "screened_theatrically"]:
                                            if attr_data is True:
                                                new_dictionary[attr] = attr_data
                                        elif attr in ["primary_release_date.gte", "primary_release_date.lte", "release_date.gte", "release_date.lte", "air_date.gte", "air_date.lte", "first_air_date.gte", "first_air_date.lte"]:
                                            if re.compile("[0-1]?[0-9][/-][0-3]?[0-9][/-][1-2][890][0-9][0-9]").match(str(attr_data)):
                                                the_date = str(attr_data).split("/") if "/" in str(attr_data) else str(attr_data).split("-")
                                                new_dictionary[attr] = "{}-{}-{}".format(the_date[2], the_date[0], the_date[1])
                                            elif re.compile("[1-2][890][0-9][0-9][/-][0-1]?[0-9][/-][0-3]?[0-9]").match(str(attr_data)):
                                                the_date = str(attr_data).split("/") if "/" in str(attr_data) else str(attr_data).split("-")
                                                new_dictionary[attr] = "{}-{}-{}".format(the_date[0], the_date[1], the_date[2])
                                            else:
                                                print("| Config Error: Skipping {} attribute {}: {} must match pattern MM/DD/YYYY e.g. 12/25/2020".format(m, attr, attr_data))
                                        elif attr in ["primary_release_year", "year", "first_air_date_year"]:
                                            if isinstance(attr_data, int) and 1800 < attr_data and attr_data < 2200:
                                                new_dictionary[attr] = attr_data
                                            else:
                                                print("| Config Error: Skipping {} attribute {}: must be a valid year e.g. 1990".format(m, attr))
                                        elif attr in ["vote_count.gte", "vote_count.lte", "vote_average.gte", "vote_average.lte", "with_runtime.gte", "with_runtime.lte"]:
                                            if (isinstance(attr_data, int) or isinstance(attr_data, float)) and 0 < attr_data:
                                                new_dictionary[attr] = attr_data
                                            else:
                                                print("| Config Error: Skipping {} attribute {}: must be a valid number greater then 0".format(m, attr))
                                        elif attr in ["with_cast", "with_crew", "with_people", "with_companies", "with_networks", "with_genres", "without_genres", "with_keywords", "without_keywords", "with_original_language", "timezone"]:
                                            new_dictionary[attr] = attr_data
                                        else:
                                            print("| Config Error: {} attribute {} not supported".format(m, attr))
                                    elif attr == "limit":
                                        if isinstance(attr_data, int) and attr_data > 0:
                                            new_dictionary[attr] = attr_data
                                        else:
                                            print("| Config Error: Skipping {} attribute {}: must be a valid number greater then 0".format(m, attr))
                                    else:
                                        print("| Config Error: {} attribute {} not supported".format(m, attr))
                                else:
                                    print("| Config Error: {} parameter {} is blank".format(m, attr))
                            if len(new_dictionary) > 1:
                                methods.append((method_name, [new_dictionary]))
                            else:
                                print("| Config Error: {} had no valid fields".format(m))
                        elif method_name == "tautulli":
                            try:
                                new_dictionary = {}
                                new_dictionary["list_type"] = check_for_attribute(collections[c][m], "list_type", parent="tautulli", test_list=["popular", "watched"], options="| \tpopular (Most Popular List)\n| \twatched (Most Watched List)", throw=True, save=False)
                                new_dictionary["list_days"] = check_for_attribute(collections[c][m], "list_days", parent="tautulli", var_type="int", default=30, save=False)
                                new_dictionary["list_size"] = check_for_attribute(collections[c][m], "list_size", parent="tautulli", var_type="int", default=10, save=False)
                                new_dictionary["list_buffer"] = check_for_attribute(collections[c][m], "list_buffer", parent="tautulli", var_type="int", default=20, save=False)
                                methods.append((method_name, [new_dictionary]))
                            except SystemExit as e:
                                print(e)
                    else:
                        print("| Config Error: {} attribute is not a dictionary: {}".format(m, collections[c][m]))
                elif method_name == "all":
                    methods.append((method_name, [""]))
                elif method_name != "sync_mode":
                    print("| Config Error: {} attribute not supported".format(method_name))
            else:
                print("| Config Error: {} attribute is blank".format(m))

        first_filter = True
        for f in filters:
            if first_filter == True:
                print("| ")
                first_filter = False
            print("| Collection Filter {}: {}".format(f[0], f[1]))

        do_radarr = False
        if radarr:
            do_radarr = radarr.add_to_radarr
            if "add_to_radarr" in details:
                do_radarr = details["add_to_radarr"]

        # Loops though and actually processes the methods
        for m, values in methods:
            for v in values:
                if m == "imdb_list":
                    print("| \n| Processing {}: {}".format(m, v[0]))
                elif m == "plex_collection":
                    print("| \n| Processing {}: {}".format(m, v.title))
                elif m not in ["plex_search", "tmdb_list", "tmdb_id", "tmdb_movie", "tmdb_collection", "tmdb_company", "tmdb_network", "tmdb_discover", "tmdb_show"]:
                    print("| \n| Processing {}: {}".format(m, v))
                try:
                    missing, map = add_to_collection(config_path, plex, m, v, c, plex_map, map, filters)
                except (KeyError, ValueError, SystemExit) as e:
                    print(e)
                    missing = False
                if missing:
                    def missing_print(display_value):
                        print("| {} missing {}{} from {}: {}".format(len(missing), libtype, "s" if len(missing) > 1 else "", pretty_names[m], display_value))

                    if m in ["tmdb_popular", "tmdb_top_rated", "tmdb_now_playing", "tmdb_trending_daily", "tmdb_trending_weekly", "trakt_trending"]:
                        missing_print("Top {}".format(v))
                    elif m == "imdb_list":
                        missing_print(v[0])
                    else:
                        missing_print(v)

                    if do_radarr:
                        print("| Adding missing movies to Radarr")
                        add_to_radarr(config_path, missing)
                    elif do_radarr is None and not headless and input("| Add missing movies to Radarr? (y/n): ").upper() == "Y":
                        add_to_radarr(config_path, missing)
                        # if not skip_sonarr:
                        #     if input("Add missing shows to Sonarr? (y/n): ").upper() == "Y":
                        #         add_to_radarr(missing_shows)

        for ratingKey, item in map.items():
            if item is not None:
                print("| {} Collection | - | {}".format(c, item.title))
                item.removeCollection(c)

        print("| ")

        try:
            plex_collection = get_collection(plex, c, headless)
        except ValueError as e:
            print("| Config Error: {}".format(e))
            continue       # No collections created with requested criteria

        if not no_meta:
            def edit_details (name, key=None):
                if key is None:
                    key = name
                if name in details:
                    if name == "collection_mode":
                        plex_collection.modeUpdate(mode=details[name])
                    elif name == "collection_order":
                        plex_collection.sortUpdate(sort=details[name])
                    else:
                        edits = {"{}.value".format(key): details[name], "{}.locked".format(key): 1}
                        plex_collection.edit(**edits)
                        plex_collection.reload()
                    print("| Detail: {} updated to {}".format(name, details[name]))

            edit_details("sort_title", "titleSort")
            edit_details("content_rating", "contentRating")
            edit_details("summary")
            edit_details("collection_mode")
            edit_details("collection_order")

        if not no_images:
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

            if not poster and "poster" in details:
                poster = details["poster"]
            if not background and "background" in details:
                background = details["background"]

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
        selected_collection = None
        try:
            if config_update:
                collection_name = config_update
                selected_collection = get_collection(plex, collection_name, True)
            else:
                collection_name = input("| Enter collection to add to: ")
                selected_collection = get_collection(plex, collection_name)
        except ValueError as e:
            print("| Config Error: {}".format(e))
            break

        try:
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
                                plex_movie = get_item(plex, int(value))
                                print('| +++ Adding %s to collection %s' % (
                                    plex_movie.title, selected_collection.title))
                                plex_movie.addCollection(selected_collection.title)
                            else:
                                results = get_item(plex, value)
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
                        print("| Please read the below link to see valid search types. "
                              "Please note not all have been tested")
                        print(
                            "| https://python-plexapi.readthedocs.io/en/latest/modules/video.html?highlight=plexapi.video.Movie#plexapi.video.Movie")
                        while True:
                            method = input("| Enter Search method (q to quit): ")
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
                                print("| Search method did not match an attribute for plexapi.video.Movie")
                except TypeError:
                    print("| Bad {} URL".format(l_type))
                except KeyError as e:
                    print("| " + str(e))
                if input("| Add more to collection? (y/n): ") == "n":
                    finished = True
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
print("| Version 2.8.1")
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
    print("|\n|===================================================================================================|")
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
                if method == "imdb_list":
                    title_ids = imdb_get_ids(plex, url)
                    if title_ids:
                        url = (url, title_ids)
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
            try:
                delete_collection(get_collection(plex, data))
            except ValueError as e:
                print("| Config Error: {}".format(e))

        elif mode == "s":
            print("|\n|===================================================================================================|")
            data = input("| \n| Enter collection name to search for (blank for all): ")
            try:
                collection = get_collection(plex, data)
                print("| Found {} collection {}".format(collection.subtype, collection.title))
                items = collection.children
                print("| {}s in collection: ".format(collection.subtype).capitalize())
                for i, m in enumerate(items):
                    print("| {}) {}".format(i + 1, m.title))
            except ValueError as e:
                print("| Error: {}".format(e))
    except KeyboardInterrupt:
        print()
        pass

print("|\n|===================================================================================================|\n")
