import re
import requests
import math
import sys
from urllib.parse import urlparse
from lxml import html
from tmdbv3api import TMDb
from tmdbv3api import Movie
from tmdbv3api import List
from tmdbv3api import TV
from tmdbv3api import Collection
from tmdbv3api import Person
import config_tools
import trakt


def imdb_get_movies(config_path, plex, data):
    tmdb = TMDb()
    movie = Movie()
    tmdb.api_key = config_tools.TMDB(config_path).apikey
    imdb_url = data
    if imdb_url[-1:] == " ":
        imdb_url = imdb_url[:-1]
    imdb_map = {}
    library_language = plex.Library.language
    if "/search/" in imdb_url:
        if "&count=" in imdb_url:
            imdb_url = re.sub("&count=\d+", "&count=100", imdb_url)
        else:
            imdb_url = imdb_url + "&count=100"
    try:
        r = requests.get(imdb_url, headers={'Accept-Language': library_language})
    except requests.exceptions.MissingSchema:
        return
    tree = html.fromstring(r.content)
    title_ids = tree.xpath("//div[contains(@class, 'lister-item-image')]"
                           "//a/img//@data-tconst")
    if "/search/" in imdb_url:
        results = re.search('<span>\\d+-\\d+ of \\d+ titles.</span>', str(r.content))
        total = 100 if results is None else re.findall('(\\d+)', results.group(0))[2]
    else:
        results = re.search('(?<=<div class="desc lister-total-num-results">).*?(?=</div>)', str(r.content))
        total = 100 if results is None else re.search('.*?(\\d+)', results.group(0)).group(1)

    for i in range(1, math.ceil(int(total) / 100)):
        try:
            if "/search/" in imdb_url:
                r = requests.get(imdb_url + '&start={}'.format(i * 100 + 1), headers={'Accept-Language': library_language})
            else:
                r = requests.get(imdb_url + '?page={}'.format(i + 1), headers={'Accept-Language': library_language})
        except requests.exceptions.MissingSchema:
            return
        tree = html.fromstring(r.content)
        title_ids.extend(tree.xpath("//div[contains(@class, 'lister-item-image')]"
                                    "//a/img//@data-tconst"))
    matched_imdb_movies = []
    missing_imdb_movies = []
    if title_ids:
        for m in plex.Library.all():
            try:
                if 'themoviedb://' in m.guid:
                    if not tmdb.api_key == "None":
                        tmdb_id = m.guid.split('themoviedb://')[1].split('?')[0]
                        tmdbapi = movie.details(tmdb_id)
                        imdb_id = tmdbapi.imdb_id
                    else:
                        imdb_id = None
                elif 'imdb://' in m.guid:
                    imdb_id = m.guid.split('imdb://')[1].split('?')[0]
                else:
                    imdb_id = None
            except:
                imdb_id = None

            if imdb_id and imdb_id in title_ids:
                imdb_map[imdb_id] = m
            else:
                imdb_map[m.ratingKey] = m

        for imdb_id in title_ids:
            movie = imdb_map.pop(imdb_id, None)
            if movie:
                matched_imdb_movies.append(plex.Server.fetchItem(movie.ratingKey))
            else:
                missing_imdb_movies.append(imdb_id)

    return matched_imdb_movies, missing_imdb_movies


def tmdb_get_movies(config_path, plex, data, is_list=False):
    tmdb_id = int(data)
    t_movs = []
    t_movie = Movie()
    t_movie.api_key = config_tools.TMDB(config_path).apikey  # Set TMDb api key for Movie
    if t_movie.api_key == "None":
        raise KeyError("Invalid TMDb API Key")

    tmdb = List() if is_list else Collection()
    tmdb.api_key = t_movie.api_key
    t_col = tmdb.details(tmdb_id)

    if is_list:
        try:
            for tmovie in t_col:
                if tmovie.media_type == "movie":
                    t_movs.append(tmovie.id)
        except:
            raise ValueError("| Config Error: TMDb List: {} not found".format(tmdb_id))
    else:
        try:
            for tmovie in t_col.parts:
                t_movs.append(tmovie['id'])
        except AttributeError:
            try:
                t_movie.details(tmdb_id).imdb_id
                t_movs.append(tmdb_id)
            except:
                raise ValueError("| Config Error: TMDb ID: {} not found".format(tmdb_id))


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
        else:
            guid = "None"
        p_m_map[m] = guid

    matched = []
    missing = []
    # We want to search for a match first to limit TMDb API calls
    # Too many rapid calls can cause a momentary block
    # If needed in future maybe add a delay after x calls to let the limit reset
    for mid in t_movs:  # For each TMBd ID in TMBd Collection
        match = False
        for m in p_m_map:  # For each movie in Plex
            if "tt" not in p_m_map[m] != "None":  # If the Plex movie's guid does not start with tt
                if int(p_m_map[m]) == int(mid):
                    match = True
                    break
        if not match:
            imdb_id = t_movie.details(mid).imdb_id
            for m in p_m_map:
                if "tt" in p_m_map[m]:
                    if p_m_map[m] == imdb_id:
                        match = True
                        break
        if match:
            matched.append(m)
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

def tmdb_get_shows(config_path, plex, data, is_list=False):
    config_tools.TraktClient(config_path)

    tmdb_id = int(data)

    t_tvs = []
    t_tv = TV()
    t_tv.api_key = config_tools.TMDB(config_path).apikey  # Set TMDb api key for Movie
    if t_tv.api_key == "None":
        raise KeyError("Invalid TMDb API Key")

    if is_list:
        tmdb = List()
        tmdb.api_key = t_tv.api_key
        try:
            t_col = tmdb.details(tmdb_id)
            for ttv in t_col:
                if ttv.media_type == "tv":
                    t_tvs.append(ttv.id)
        except:
            raise ValueError("| Config Error: TMDb List: {} not found".format(tmdb_id))
    else:
        try:
            t_tv.details(tmdb_id).number_of_seasons
            t_tvs.append(tmdb_id)
        except:
            raise ValueError("| Config Error: TMDb ID: {} not found".format(tmdb_id))

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
        for t in p_tv_map:
            if p_tv_map[t] and "tt" not in p_tv_map[t] != "None":
                if int(p_tv_map[t]) == int(tvdb_id):
                    match = True
                    break
        if match:
            matched.append(t)
        else:
            missing.append(tvdb_id)

    return matched, missing

def tvdb_get_shows(config_path, plex, data, is_list=False):
    config_tools.TraktClient(config_path)

    id = int(data)

    p_tv_map = {}
    for item in plex.Library.all():
        guid = urlparse(item.guid)
        item_type = guid.scheme.split('.')[-1]
        if item_type == 'thetvdb':
            tvdb_id = guid.netloc
        elif item_type == 'themoviedb' and TraktClient.valid:
            tvdb_id = get_tvdb_id_from_tmdb_id(guid.netloc)
        else:
            tvdb_id = None
        p_tv_map[item] = tvdb_id

    matched = []
    missing = []
    match = False
    for t in p_tv_map:
        if p_tv_map[t] and "tt" not in p_tv_map[t] != "None":
            if int(p_tv_map[t]) == int(id):
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
