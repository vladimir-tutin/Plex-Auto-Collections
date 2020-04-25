import re, requests, os, yaml
from tmdbv3api import TMDb
from tmdbv3api import Movie

def add_to_radarr(config_path, missing):
    # config_path = os.path.join(os.getcwd(), 'config.yml')
    config = yaml.load(open(config_path), Loader=yaml.FullLoader)

    tmdb = TMDb()
    tmdb.api_key = config['tmdb']['apikey']
    tmdb.language = "en"

    url = config['radarr']['url'] + "/api/movie"
    token = config['radarr']['token']
    quality = config['radarr']['quality_profile_id']
    rootfolder = config['radarr']['root_folder_path']
    search = config['radarr']['search']
    querystring = {"apikey": "{}".format(token)}

    if "None" in (tmdb.api_key, url, token, quality, rootfolder):
        print("All TMDB / Radarr details must be filled out in the configuration "
              "file to import missing movies into Radarr")
        print("\n")
        return

    movie = Movie()
    for m in missing:
        # Validate TMDb information (very few TMDb entries don't yet have basic information)
        try:
            tmdb_details = movie.external(external_id=str(m), external_source="imdb_id")['movie_results'][0]
            tmdb_title = tmdb_details['title']
            tmdb_id = tmdb_details['id']
        except IndexError:
            print("Unable to fetch necessary external information")
            continue

        # Validate TMDb year (several TMDb entries don't yet have release dates)        
        try: 
            tmdb_year = tmdb_details['release_date'].split("-")[0]
        except KeyError:
            print(tmdb_title + " does not have a release date yet")
            continue

        if tmdb_year.isdigit() == False:
            print(tmdb_title + " does not have a release date yet")
            continue

        tmdb_poster = "https://image.tmdb.org/t/p/original{}".format(tmdb_details['poster_path'])

        titleslug = "{} {}".format(tmdb_title, tmdb_year)
        titleslug = re.sub(r'([^\s\w]|_)+', '', titleslug)
        titleslug = titleslug.replace(" ", "-")
        titleslug = titleslug.lower()

        payload = {
            "title": tmdb_title,
            "qualityProfileId": quality,
            "year": int(tmdb_year),
            "tmdbid": str(tmdb_id),
            "titleslug": titleslug,
            "monitored": "true",
            "rootFolderPath": rootfolder,
            "images": [{
                "covertype": "poster",
                "url": tmdb_poster
            }],
            "addOptions": {
                "searchForMovie": search
            }
        }

        response = requests.post(url, json=payload, params=querystring)

        try:
            if response.json()[0]['errorMessage'] == "This movie has already been added":
                print(tmdb_title + " already added to Radarr")
        except KeyError:
            print("+++ " + tmdb_title + " added to Radarr")
