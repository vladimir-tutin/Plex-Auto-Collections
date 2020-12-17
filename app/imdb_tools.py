import re
import requests
import math
import sys
import os
import config_tools
try:
    from urllib.parse import urlparse
    from lxml import html
    from tmdbv3api import TMDb
    from tmdbv3api import Movie
    from tmdbv3api import List
    from tmdbv3api import TV
    from tmdbv3api import Discover
    from tmdbv3api import Collection
    from tmdbv3api import Company
    from tmdbv3api import Network
    from tmdbv3api import Person
    from tmdbv3api import Trending
except ImportError:
    print('|\n| Requirements Error: Please update requirements using "pip install -r requirements.txt"\n|')
    sys.exit(0)

def imdb_get_ids(plex, imdb_url):
    imdb_url = imdb_url.strip()
    if imdb_url.startswith("https://www.imdb.com/list/ls") or imdb_url.startswith("https://www.imdb.com/search/title/?"):
        try:
            if imdb_url.startswith("https://www.imdb.com/list/ls"):
                imdb_url = "https://www.imdb.com/list/ls{}".format(re.search('(\\d+)', str(imdb_url)).group(1))
            else:
                if "&start=" in imdb_url:
                    imdb_url = re.sub("&start=\d+", "", imdb_url)
                if "&count=" in imdb_url:
                    imdb_url = re.sub("&count=\d+", "&count=100", imdb_url)
                else:
                    imdb_url += "&count=100"
            library_language = plex.Library.language
            r = requests.get(imdb_url, headers={'Accept-Language': library_language})
            tree = html.fromstring(r.content)
            title_ids = tree.xpath("//div[contains(@class, 'lister-item-image')]"
                                   "//a/img//@data-tconst")
            if imdb_url.startswith("https://www.imdb.com/list/ls"):
                results = re.search('(?<=<div class="desc lister-total-num-results">).*?(?=</div>)', str(r.content))
                total = 100 if results is None else re.search('(\\d+)', results.group(0).replace(',', '')).group(1)
            else:
                results = re.search('<span>\\d+-\\d+ of \\d+ titles.</span>', str(r.content))
                total = 100 if results is None else re.findall('(\\d+)', results.group(0).replace(',', ''))[2]
            for i in range(1, math.ceil(int(total) / 100)):
                if imdb_url.startswith("https://www.imdb.com/list/ls"):
                    r = requests.get(imdb_url + '?page={}'.format(i + 1), headers={'Accept-Language': library_language})
                else:
                    r = requests.get(imdb_url + '&start={}'.format(i * 100 + 1), headers={'Accept-Language': library_language})
                tree = html.fromstring(r.content)
                title_ids.extend(tree.xpath("//div[contains(@class, 'lister-item-image')]"
                                            "//a/img//@data-tconst"))
            if title_ids:
                return title_ids
            else:
                print("| Config Error: No Movies Found at {}".format(imdb_url))

        except AttributeError:
            print("| Config Error: Skipping imdb_list failed to parse List ID from {}".format(imdb_url))
        except requests.exceptions.MissingSchema:
            print("| Config Error: URL Lookup Failed for {}".format(imdb_url))
    else:
        print("| Config Error {} must begin with either:\n| https://www.imdb.com/list/ls (For Lists)\n| https://www.imdb.com/search/title/? (For Searches)")
    return None

def tmdb_get_imdb(config_path, tmdb_id):
    movie = Movie()
    movie.api_key = config_tools.TMDB(config_path).apikey
    return str(movie.external_ids(tmdb_id)['imdb_id'])

def tmdb_get_tvdb(config_path, tmdb_id):
    show = TV()
    show.api_key = config_tools.TMDB(config_path).apikey
    return str(show.external_ids(tmdb_id)['tvdb_id'])

def imdb_get_tmdb(config_path, imdb_id):
    movie = Movie()
    movie.api_key = config_tools.TMDB(config_path).apikey
    search = movie.external(external_id=imdb_id, external_source="imdb_id")['movie_results']
    if len(search) == 1:
        try:
            return str(search[0]['id'])
        except IndexError:
            return None
    else:
        return None

def tvdb_get_tmdb(config_path, tvdb_id):
    movie = Movie()
    movie.api_key = config_tools.TMDB(config_path).apikey
    search = movie.external(external_id=tvdb_id, external_source="tvdb_id")['tv_results']
    if len(search) == 1:
        try:
            return str(search[0]['id'])
        except IndexError:
            return None
    else:
        return None

def imdb_get_movies(config_path, plex, plex_map, data):
    title_ids = data[1]
    print("| {} Movies found on IMDb".format(len(title_ids)))
    t_movie = Movie()
    t_movie.api_key = config_tools.TMDB(config_path).apikey
    matched = []
    missing = []
    for imdb_id in title_ids:
        tmdb_id = imdb_get_tmdb(config_path, imdb_id)
        if tmdb_id in plex_map:
            matched.append(plex.Server.fetchItem(plex_map[tmdb_id]))
        else:
            missing.append(tmdb_id)
    return matched, missing

def tmdb_get_movies(config_path, plex, plex_map, data, method):
    t_movs = []
    t_movie = Movie()
    t_movie.api_key = config_tools.TMDB(config_path).apikey  # Set TMDb api key for Movie
    if t_movie.api_key == "None":
        raise KeyError("Invalid TMDb API Key")

    count = 0
    if method == "tmdb_discover":
        attrs = data.copy()
        discover = Discover()
        discover.api_key = t_movie.api_key
        discover.discover_movies(attrs)
        total_pages = int(os.environ["total_pages"])
        total_results = int(os.environ["total_results"])
        limit = int(attrs.pop('limit'))
        amount = total_results if limit == 0 or total_results < limit else limit
        print("| Processing {}: {} movies".format(method, amount))
        for attr, value in attrs.items():
            print("|            {}: {}".format(attr, value))
        for x in range(total_pages):
            attrs["page"] = x + 1
            tmdb_movies = discover.discover_movies(attrs)
            for tmovie in tmdb_movies:
                count += 1
                t_movs.append(tmovie.id)
                if count == amount:
                    break
            if count == amount:
                break
    elif method in ["tmdb_popular", "tmdb_top_rated", "tmdb_now_playing", "tmdb_trending_daily", "tmdb_trending_weekly"]:
        trending = Trending()
        trending.api_key = t_movie.api_key
        for x in range(int(int(data) / 20) + 1):
            if method == "tmdb_popular":
                tmdb_movies = t_movie.popular(x + 1)
            elif method == "tmdb_top_rated":
                tmdb_movies = t_movie.top_rated(x + 1)
            elif method == "tmdb_now_playing":
                tmdb_movies = t_movie.now_playing(x + 1)
            elif method == "tmdb_trending_daily":
                tmdb_movies = trending.movie_day(x + 1)
            elif method == "tmdb_trending_weekly":
                tmdb_movies = trending.movie_week(x + 1)
            for tmovie in tmdb_movies:
                count += 1
                t_movs.append(tmovie.id)
                if count == data:
                    break
            if count == data:
                break
        print("| Processing {}: {} Items".format(method, data))
    else:
        tmdb_id = int(data)
        if method == "tmdb_list":
            tmdb = List()
            tmdb.api_key = t_movie.api_key
            try:
                t_col = tmdb.details(tmdb_id)
                tmdb_name = str(t_col)
                for tmovie in t_col:
                    if tmovie.media_type == "movie":
                        t_movs.append(tmovie.id)
            except:
                raise ValueError("| Config Error: TMDb List: {} not found".format(tmdb_id))
        elif method == "tmdb_company":
            tmdb = Company()
            tmdb.api_key = t_movie.api_key
            tmdb_name = str(tmdb.details(tmdb_id))
            company_movies = tmdb.movies(tmdb_id)
            for tmovie in company_movies:
                t_movs.append(tmovie.id)
        else:
            tmdb = Collection()
            tmdb.api_key = t_movie.api_key
            t_col = tmdb.details(tmdb_id)
            tmdb_name = str(t_col)
            try:
                for tmovie in t_col.parts:
                    t_movs.append(tmovie['id'])
            except AttributeError:
                try:
                    t_movie.details(tmdb_id).imdb_id
                    tmdb_name = str(t_movie.details(tmdb_id))
                    t_movs.append(tmdb_id)
                except:
                    raise ValueError("| Config Error: TMDb ID: {} not found".format(tmdb_id))
        print("| Processing {}: ({}) {}".format(method, tmdb_id, tmdb_name))

    matched = []
    missing = []
    for mid in t_movs:
        mid = str(mid)
        if mid in plex_map:
            matched.append(plex.Server.fetchItem(plex_map[mid]))
        else:
            missing.append(mid)

    return matched, missing

def get_tautulli(config_path, plex, data):
    tautulli = config_tools.Tautulli(config_path)

    response = requests.get("{}/api/v2?apikey={}&cmd=get_home_stats&time_range={}&stats_count={}".format(tautulli.url, tautulli.apikey, data["list_days"], int(data["list_size"]) + int(data["list_buffer"]))).json()
    stat_id = ("popular" if data["list_type"] == "popular" else "top") + "_" + ("movies" if plex.library_type == "movie" else "tv")

    items = None
    for entry in response['response']['data']:
        if entry['stat_id'] == stat_id:
            items = entry['rows']
            break
    if items is None:
        sys.exit("| No Items found in the response")

    section_id = None
    response = requests.get("{}/api/v2?apikey={}&cmd=get_library_names".format(tautulli.url, tautulli.apikey)).json()
    for entry in response['response']['data']:
        if entry['section_name'] == plex.library:
            section_id = entry['section_id']
            break
    if section_id is None:
        sys.exit("| No Library named {} in the response".format(plex.library))

    matched = []
    missing = []
    count = 0
    for item in items:
        if item['section_id'] == section_id and count < int(data["list_size"]):
            matched.append(plex.Library.fetchItem(item['rating_key']))
            count = count + 1

    return matched, missing

def tmdb_get_shows(config_path, plex, plex_map, data, method):
    config_tools.TraktClient(config_path)

    t_tvs = []
    t_tv = TV()
    t_tv.api_key = config_tools.TMDB(config_path).apikey
    if t_tv.api_key == "None":
        raise KeyError("Invalid TMDb API Key")

    count = 0
    if method in ["tmdb_discover", "tmdb_company", "tmdb_network"]:
        if method in ["tmdb_company", "tmdb_network"]:
            tmdb = Company() if method == "tmdb_company" else Network()
            tmdb.api_key = t_tv.api_key
            tmdb_id = int(data)
            tmdb_name = str(tmdb.details(tmdb_id))
            discover_method = "with_companies" if method == "tmdb_company" else "with_networks"
            attrs = {discover_method: tmdb_id}
            limit = 0
        else:
            attrs = data.copy()
            limit = int(attrs.pop('limit'))
        discover = Discover()
        discover.api_key = t_tv.api_key
        discover.discover_tv_shows(attrs)
        total_pages = int(os.environ["total_pages"])
        total_results = int(os.environ["total_results"])
        amount = total_results if limit == 0 or total_results < limit else limit
        if method in ["tmdb_company", "tmdb_network"]:
            print("| Processing {}: {} ({} {} shows)".format(method, tmdb_id, amount, tmdb_name))
        else:
            print("| Processing {}: {} shows".format(method, amount))
            for attr, value in attrs.items():
                print("|            {}: {}".format(attr, value))
        for x in range(total_pages):
            attrs["page"] = x + 1
            tmdb_shows = discover.discover_tv_shows(attrs)
            for tshow in tmdb_shows:
                count += 1
                t_tvs.append(tshow.id)
                if count == amount:
                    break
            if count == amount:
                break
    elif method in ["tmdb_popular", "tmdb_top_rated", "tmdb_trending_daily", "tmdb_trending_weekly"]:
        trending = Trending()
        trending.api_key = t_movie.api_key
        for x in range(int(int(data) / 20) + 1):
            if method == "tmdb_popular":
                tmdb_shows = t_tv.popular(x + 1)
            elif method == "tmdb_top_rated":
                tmdb_shows = t_tv.top_rated(x + 1)
            elif method == "tmdb_trending_daily":
                tmdb_shows = trending.tv_day(x + 1)
            elif method == "tmdb_trending_weekly":
                tmdb_shows = trending.tv_week(x + 1)
            for tshow in tmdb_shows:
                count += 1
                t_tvs.append(tshow.id)
                if count == amount:
                    break
            if count == amount:
                break
        print("| Processing {}: {} Items".format(method, data))
    else:
        tmdb_id = int(data)
        if method == "tmdb_list":
            tmdb = List()
            tmdb.api_key = t_tv.api_key
            try:
                t_col = tmdb.details(tmdb_id)
                tmdb_name = str(t_col)
                for ttv in t_col:
                    if ttv.media_type == "tv":
                        t_tvs.append(ttv.id)
            except:
                raise ValueError("| Config Error: TMDb List: {} not found".format(tmdb_id))
        else:
            try:
                t_tv.details(tmdb_id).number_of_seasons
                tmdb_name = str(t_tv.details(tmdb_id))
                t_tvs.append(tmdb_id)
            except:
                raise ValueError("| Config Error: TMDb ID: {} not found".format(tmdb_id))
        print("| Processing {}: ({}) {}".format(method, tmdb_id, tmdb_name))

    matched = []
    missing = []
    for mid in t_tvs:
        tvdb_id = tmdb_get_tvdb(config_path, mid)
        if tvdb_id is None:
            print("| TMDb Error: tmdb_id: {} ({}) has no associated tvdb_id try just using tvdb_id instead".format(mid, t_tv.details(mid).name))
        elif tvdb_id in plex_map:
            matched.append(plex.Server.fetchItem(plex_map[tvdb_id]))
        else:
            missing.append(tvdb_id)

    return matched, missing

def tvdb_get_shows(config_path, plex, plex_map, data):
    tvdb_id = str(data)
    matched = []
    missing = []
    if tvdb_id in plex_map:
        matched.append(plex.Server.fetchItem(plex_map[tvdb_id]))
    else:
        missing.append(tvdb_id)

    return matched, missing

def tmdb_get_metadata(config_path, data, type):
    # Instantiate TMDB objects
    tmdb_id = int(data)

    api_key = config_tools.TMDB(config_path).apikey
    language = config_tools.TMDB(config_path).language
    is_movie = config_tools.Plex(config_path).library_type == "movie"

    if type in ["overview", "poster", "backdrop"]:
        collection = Collection()
        collection.api_key = api_key
        collection.language = language
        try:
            if type == "overview":
                meta = collection.details(tmdb_id).overview
            elif type == "poster":
                meta = collection.details(tmdb_id).poster_path
            elif type == "backdrop":
                meta = collection.details(tmdb_id).backdrop_path
        except AttributeError:
            media = Movie() if is_movie else TV()
            media.api_key = api_key
            media.language = language
            try:
                if type == "overview":
                    meta = media.details(tmdb_id).overview
                elif type == "poster":
                    meta = media.details(tmdb_id).poster_path
                elif type == "backdrop":
                    meta = media.details(tmdb_id).backdrop_path
            except AttributeError:
                raise ValueError("| TMDb Error: TMBd {} ID: {} not found".format("Movie/Collection" if is_movie else "Show", tmdb_id))
    elif type in ["biography", "profile", "name"]:
        person = Person()
        person.api_key = api_key
        person.language = language
        try:
            if type == "biography":
                meta = person.details(tmdb_id).biography
            elif type == "profile":
                meta = person.details(tmdb_id).profile_path
            elif type == "name":
                meta = person.details(tmdb_id).name
        except AttributeError:
            raise ValueError("| TMDb Error: TMBd Actor ID: {} not found".format(tmdb_id))
    else:
        raise RuntimeError("type {} not yet supported in tmdb_get_metadata".format(type))

    if meta is None:
        raise ValueError("| TMDb Error: TMDB ID {} has no {}".format(tmdb_id, type))
    elif type in ["profile", "poster", "backdrop"]:
        return "https://image.tmdb.org/t/p/original" + meta
    else:
        return meta
