import re, requests, os, yaml
import config_tools
from tmdbv3api import TMDb
from tmdbv3api import Movie

def add_to_radarr(config_path, missing):
    config_tmdb = config_tools.TMDB(config_path)
    config_radarr = config_tools.Radarr(config_path)

    tmdb = TMDb()
    tmdb.api_key = config_tmdb.apikey
    tmdb.language = config_tmdb.language

    movie = Movie()
    for m in missing:
        # Get TMDb ID data from IMDb ID
        search = movie.external(external_id=str(m), external_source="imdb_id")['movie_results']
        if len(search) == 1:
            tmdb_details = search[0]
        else:
            print("--- Unable to match TMDb ID for IMDb ID {}, skipping".format(m))
            continue
        
        # Validate TMDb information (very few TMDb entries don't yet have basic information)
        try:
            tmdb_title = tmdb_details['title']
            tmdb_id = tmdb_details['id']
        except IndexError:
            print("--- Unable to fetch necessary TMDb information for IMDb ID {}, skipping".format(m))
            continue

        # Validate TMDb year (several TMDb entries don't yet have release dates)        
        try: 
            # This might be overly punitive
            tmdb_year = tmdb_details['release_date'].split("-")[0]
        except KeyError:
            print("--- {} does not have a release date on TMDb yet, skipping".format(tmdb_title))
            continue

        if tmdb_year.isdigit() == False:
            print("--- {} does not have a release date on TMDb yet, skipping".format(tmdb_title))
            continue

        tmdb_poster = "https://image.tmdb.org/t/p/original{}".format(tmdb_details['poster_path'])

        titleslug = "{} {}".format(tmdb_title, tmdb_year)
        titleslug = re.sub(r'([^\s\w]|_)+', '', titleslug)
        titleslug = titleslug.replace(" ", "-")
        titleslug = titleslug.lower()

        payload = {
            "title": tmdb_title,
            "qualityProfileId": config_radarr.quality_profile_id,
            "year": int(tmdb_year),
            "tmdbid": str(tmdb_id),
            "titleslug": titleslug,
            "monitored": "true",
            "rootFolderPath": config_radarr.root_folder_path,
            "images": [{
                "covertype": "poster",
                "url": tmdb_poster
            }],
            "addOptions": {
                "searchForMovie": config_radarr.search_movie
            }
        }

        if config_radarr.version == "v3":
            slug = "/api/v3/movie"
        else:
            slug = "/api/movie"
        url = config_radarr.url + slug
        querystring = {"apikey": "{}".format(config_radarr.token)}

        response = requests.post(url, json=payload, params=querystring)

        if response.status_code < 400:
            print("+++ {}: Added to Radarr".format(tmdb_title))
        else:
            print("--- {}: {}".format(tmdb_title, response.json()[0]['errorMessage']))