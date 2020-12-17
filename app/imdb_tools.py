import re
import requests
import math
import sys
import os
from urllib.parse import urlparse
from lxml import html
from tmdbv3api import TMDb
from tmdbv3api import Movie
from tmdbv3api import List
from tmdbv3api import TV
from tmdbv3api import Discover
from tmdbv3api import Collection
from tmdbv3api import Company
#from tmdbv3api import Network #TURNON:Trending
from tmdbv3api import Person
#from tmdbv3api import Trending #TURNON:Trending
import config_tools
import plex_tools
import trakt

def adjust_space(old_length, display_title):
    space_length = old_length - len(display_title)
    if space_length > 0:
        display_title += " " * space_length
    return display_title

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

def imdb_get_movies(config_path, plex, data):
    title_ids = data[1]
    print("| {} Movies found on IMDb".format(len(title_ids)))
    tmdb = TMDb()
    tmdb.api_key = config_tools.TMDB(config_path).apikey
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
        movie = imdb_map.pop(imdb_id, None)
        if movie:
            matched_imdb_movies.append(plex.Server.fetchItem(movie.ratingKey))
        else:
            missing_imdb_movies.append(imdb_id)

    return matched_imdb_movies, missing_imdb_movies

def tmdb_get_movies(config_path, plex, data, method):
    t_movs = []
    t_movie = Movie()
    t_movie.api_key = config_tools.TMDB(config_path).apikey  # Set TMDb api key for Movie
    if t_movie.api_key == "None":
        raise KeyError("Invalid TMDb API Key")

    count = 0
    if method == "tmdb_discover":
        discover = Discover()
        discover.api_key = t_movie.api_key
        discover.discover_movies(data)
        total_pages = int(os.environ["total_pages"])
        total_results = int(os.environ["total_results"])
        limit = int(data.pop('limit'))
        amount = total_results if total_results < limit else limit
        print("| Processing {}: {} items".format(method, amount))
        for attr, value in data.items():
            print("|            {}: {}".format(attr, value))
        for x in range(total_pages):
            data["page"] = x + 1
            tmdb_movies = discover.discover_movies(data)
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
            #elif method == "tmdb_trending_daily":          #TURNON:Trending
            #    tmdb_movies = trending.movie_day(x + 1)    #TURNON:Trending
            #elif method == "tmdb_trending_weekly":         #TURNON:Trending
            #    tmdb_movies = trending.movie_week(x + 1)   #TURNON:Trending
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


    # Create dictionary of movies and their guid
    # GUIDs reference from which source Plex has pulled the metadata
    p_m_map = {}
    p_movies = plex.Library.all()
    for m in p_movies:
        guid = m.guid
        if "themoviedb://" in guid:
            guid = guid.split('themoviedb://')[1].split('?')[0]
        elif "imdb://" in guid:
            guid = guid.split('imdb://')[1].split('?')[0]
        elif "plex://" in guid:
            guid = guid.split('plex://')[1].split('?')[0]
        else:
            guid = "None"
        p_m_map[m] = guid

    matched = []
    missing = []
    for mid in t_movs:
        mid = str(mid)
        if mid in plex_map:
            matched.append(plex.Server.fetchItem(plex_map[mid]))
        else:
            # Duplicate TMDb call?
            missing.append(t_movie.details(mid).imdb_id)

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

def get_tvdb_id_from_tmdb_id(id):
    lookup = trakt.Trakt['search'].lookup(id, 'tmdb', 'show')
    if lookup:
        lookup = lookup[0] if isinstance(lookup, list) else lookup
        return lookup.get_key('tvdb')
    else:
        return None

def tmdb_get_shows(config_path, plex, data, method):
    config_tools.TraktClient(config_path)

    t_tvs = []
    t_tv = TV()
    t_tv.api_key = config_tools.TMDB(config_path).apikey  # Set TMDb api key for Movie
    if t_tv.api_key == "None":
        raise KeyError("Invalid TMDb API Key")
    discover = Discover()
    discover.api_key = t_tv.api_key

    count = 0
    if method == "tmdb_discover":
        discover.discover_tv_shows(data)
        total_pages = int(os.environ["total_pages"])
        total_results = int(os.environ["total_results"])
        limit = int(data.pop('limit'))
        amount = total_results if total_results < limit else limit
        print("| Processing {}: {} items".format(method, amount))
        for attr, value in data.items():
            print("|            {}: {}".format(attr, value))
        for x in range(total_pages):
            data["page"] = x + 1
            tmdb_shows = discover.discover_tv_shows(data)
            for tshow in tmdb_shows:
                count += 1
                t_tvs.append(tshow.id)
                if count == amount:
                    break
            if count == amount:
                break
        run_discover(data)
    elif method in ["tmdb_popular", "tmdb_top_rated", "tmdb_trending_daily", "tmdb_trending_weekly"]:
        trending = Trending()
        trending.api_key = t_movie.api_key
        for x in range(int(int(data) / 20) + 1):
            if method == "tmdb_popular":
                tmdb_shows = t_tv.popular(x + 1)
            elif method == "tmdb_top_rated":
                tmdb_shows = t_tv.top_rated(x + 1)
            #elif method == "tmdb_trending_daily":      #TURNON:Trending
            #    tmdb_shows = trending.tv_day(x + 1)    #TURNON:Trending
            #elif method == "tmdb_trending_weekly":     #TURNON:Trending
            #    tmdb_shows = trending.tv_week(x + 1)   #TURNON:Trending
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
        elif method in ["tmdb_company", "tmdb_network"]:
            if method == "tmdb_company":
                tmdb = Company()
                tmdb.api_key = t_tv.api_key
                tmdb_name = str(tmdb.details(tmdb_id))
            else:
                #tmdb = Network()                           #TURNON:Trending
                #tmdb.api_key = t_tv.api_key                #TURNON:Trending
                tmdb_name = ""#str(tmdb.details(tmdb_id))   #TURNON:Trending
            discover_method = "with_companies" if method == "tmdb_company" else "with_networks"
            tmdb_shows = discover.discover_tv_shows({discover_method: tmdb_id})
            for tshow in tmdb_shows:
                t_tvs.append(tshow.id)
        else:
            try:
                t_tv.details(tmdb_id).number_of_seasons
                tmdb_name = str(t_tv.details(tmdb_id))
                t_tvs.append(tmdb_id)
            except:
                raise ValueError("| Config Error: TMDb ID: {} not found".format(tmdb_id))
        print("| Processing {}: ({}) {}".format(method, tmdb_id, tmdb_name))

    p_tv_map = {}
    for item in plex.Library.all():
        guid = urlparse(item.guid)
        item_type = guid.scheme.split('.')[-1]
        if item_type == 'thetvdb':
            tvdb_id = guid.netloc
        elif item_type == 'themoviedb':
            tvdb_id = get_tvdb_id_from_tmdb_id(guid.netloc)
        else:
            tvdb_id = None
        p_tv_map[item] = tvdb_id

    matched = []
    missing = []
    for mid in t_tvs:
        match = False
        tvdb_id = get_tvdb_id_from_tmdb_id(mid)
        if tvdb_id is None:
            print("| Trakt Error: tmbd_id: {} could not converted to tvdb_id try just using tvdb_id instead".format(mid))
        else:
            for t in p_tv_map:
                if p_tv_map[t] and "tt" not in p_tv_map[t] != "None":
                    if p_tv_map[t] is not None and int(p_tv_map[t]) == int(tvdb_id):
                        match = True
                        break
        if match:
            matched.append(t)
        else:
            missing.append(tvdb_id)

    return matched, missing

def tvdb_get_shows(config_path, plex, plex_map, data):
    tvdb_id = str(data)
    matched = []
    missing = []
    match = False
    for t in p_tv_map:
        if p_tv_map[t] and "tt" not in p_tv_map[t] != "None":
            if p_tv_map[t] is not None and int(p_tv_map[t]) == int(id):
                match = True
                break
    if match:
        matched.append(t)
    else:
        missing.append(id)

    return matched, missing

def tmdb_get_metadata(config_path, data, type):
    # Instantiate TMDB objects
    id = int(data)

    tmdb_url_prefix = "https://image.tmdb.org/t/p/original"
    api_key = config_tools.TMDB(config_path).apikey
    language = config_tools.TMDB(config_path).language
    is_movie = config_tools.Plex(config_path).library_type == "movie"

    if type in ["overview", "poster_path", "backdrop_path"]:
        collection = Collection()
        collection.api_key = api_key
        collection.language = language
        try:
            if type == "overview":
                return collection.details(id).overview
            elif type == "poster_path":
                return tmdb_url_prefix + collection.details(id).poster_path
            elif type == "backdrop_path":
                return tmdb_url_prefix + collection.details(id).backdrop_path
        except AttributeError:
            media = Movie() if is_movie else TV()
            media.api_key = api_key
            media.language = language
            try:
                if type == "overview":
                    return media.details(id).overview
                elif type == "poster_path":
                    return tmdb_url_prefix + media.details(id).poster_path
                elif type == "backdrop_path":
                    return tmdb_url_prefix + media.details(id).backdrop_path
            except AttributeError:
                raise ValueError("| Config Error: TMBd {} ID: {} not found".format("Movie/Collection" if is_movie else "Show", id))
    elif type in ["biography", "profile_path", "name"]:
        person = Person()
        person.api_key = api_key
        person.language = language
        try:
            if type == "biography":
                return person.details(id).biography
            elif type == "profile_path":
                return tmdb_url_prefix + person.details(id).profile_path
            elif type == "name":
                return person.details(id).name
        except AttributeError:
            raise ValueError("| Config Error: TMBd Actor ID: {} not found".format(id))
    else:
        raise RuntimeError("type {} not yet supported in tmdb_get_metadata".format(type))
