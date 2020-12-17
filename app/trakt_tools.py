import config_tools
from urllib.parse import urlparse
import trakt
import os


def trakt_tmdb_to_imdb(config_path, tmdb_id):
    config_tools.TraktClient(config_path)
    lookup = trakt.Trakt['search'].lookup(tmdb_id, 'tmdb', 'movie')
    if lookup:
        lookup = lookup[0] if isinstance(lookup, list) else lookup
        return lookup.get_key('imdb')
    else:
        return None

def trakt_imdb_to_tmdb(config_path, imdb_id):
    config_tools.TraktClient(config_path)
    lookup = trakt.Trakt['search'].lookup(imdb_id, 'imdb', 'movie')
    if lookup:
        lookup = lookup[0] if isinstance(lookup, list) else lookup
        return lookup.get_key('tmdb')
    else:
        return None

def trakt_tmdb_to_tvdb(config_path, tmdb_id):
    config_tools.TraktClient(config_path)
    lookup = trakt.Trakt['search'].lookup(id, 'tmdb', 'show')
    if lookup:
        lookup = lookup[0] if isinstance(lookup, list) else lookup
        return lookup.get_key('tvdb')
    else:
        return None

def trakt_get_movies(config_path, plex, plex_map, data, method):
    config_tools.TraktClient(config_path)
    if method == "trakt_trending":
        max_items = int(data)
        trakt_list_items = trakt.Trakt['movies'].trending(per_page=max_items)
    elif method == "trakt_watchlist":
        trakt_url = data
        if trakt_url[-1:] == " ":
            trakt_url = trakt_url[:-1]
        trakt_list_path = 'users/{}/watchlist'.format(data)
        trakt_list_items = [movie for movie in trakt.Trakt[trakt_list_path].movies()]
    else:
        trakt_url = data
        if trakt_url[-1:] == " ":
            trakt_url = trakt_url[:-1]
        trakt_list_path = urlparse(trakt_url).path
        trakt_list_items = trakt.Trakt[trakt_list_path].items()
    title_ids = [str(m.get_key('tmdb')) for m in trakt_list_items if isinstance(m, trakt.objects.movie.Movie)]

    print("| {} Movies found on Trakt".format(len(title_ids)))
    matched = []
    missing = []
    for tmdb_id in title_ids:
        if tmdb_id in plex_map:
            matched.append(plex.Server.fetchItem(plex_map[tmdb_id]))
        else:
            missing.append(tmdb_id)
    return matched, missing

def trakt_get_shows(config_path, plex, plex_map, data, method):
    config_tools.TraktClient(config_path)
    if method == "trakt_trending":
        max_items = int(data)
        trakt_list_items = trakt.Trakt['shows'].trending(per_page=max_items)
    elif method == "trakt_watchlist":
        trakt_url = data
        if trakt_url[-1:] == " ":
            trakt_url = trakt_url[:-1]
        trakt_list_path = 'users/{}/watchlist'.format(data)
        trakt_list_items = [show for show in trakt.Trakt[trakt_list_path].shows()]
    else:
        trakt_url = data
        if trakt_url[-1:] == " ":
            trakt_url = trakt_url[:-1]
        trakt_list_path = urlparse(trakt_url).path
        trakt_list_items = trakt.Trakt[trakt_list_path].items()

    title_ids = []
    for m in trakt_list_items:
        if isinstance(m, trakt.objects.show.Show):
            if m.pk[1] not in title_ids:
                title_ids.append(m.pk[1])
        elif isinstance(m, trakt.objects.season.Season):
            if m.show.pk[1] not in title_ids:
                title_ids.append(m.show.pk[1])
        elif isinstance(m, trakt.objects.episode.Episode):
            if m.show.pk[1] not in title_ids:
                title_ids.append(m.show.pk[1])

    matched = []
    missing = []
    for tvdb_id in title_ids:
        if tvdb_id in plex_map:
            matched.append(plex.Server.fetchItem(plex_map[tvdb_id]))
        else:
            missing.append(tvdb_id)
    return matched, missing
