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
        # Validate TMDb information (very few TMDb entries don't yet have basic information)
        try:
            tmdb_details = movie.external(external_id=str(m), external_source="imdb_id")['movie_results'][0]
            tmdb_title = tmdb_details['title']
            tmdb_id = tmdb_details['id']
        except IndexError:
            print("Unable to fetch necessary external information, skipping")
            continue

        # Validate TMDb year (several TMDb entries don't yet have release dates)        
        try: 
            tmdb_year = tmdb_details['release_date'].split("-")[0]
        except KeyError:
            print(tmdb_title + " does not have a release date yet, skipping")
            continue

        if tmdb_year.isdigit() == False:
            print(tmdb_title + " does not have a release date yet, skipping")
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

        url = config_radarr.url + "/api/movie"
        querystring = {"apikey": "{}".format(config_radarr.token)}

        response = requests.post(url, json=payload, params=querystring)

        try:
            if response.json()[0]['errorMessage'] == "This movie has already been added":
                print(tmdb_title + " already added to Radarr")
        except KeyError:
            print("+++ " + tmdb_title + " added to Radarr")
