import re, json, requests, os, yaml
from tmdbv3api import TMDb
from tmdbv3api import Movie

def add_to_radarr(missing):
    config_path = os.path.join(os.getcwd(), 'config.yml')
    config = yaml.load(open(config_path), Loader=yaml.FullLoader)

    tmdb = TMDb()
    tmdb.api_key = config['tmdb']['apikey']
    tmdb.language = "en"

    url = config['radarr']['url'] + "/api/movie"
    quality = config['radarr']['quality_profile_id']
    token = config['radarr']['token']
    search = config['radarr']['search']
    querystring = {"apikey": "{}".format(token)}

    if "None" in (tmdb.api_key, url, quality, token):
        print("All TMDB / Radarr details must be filled out in the configuration "
              "file to import missing movies into Radarr")
        print("\n")
        return

    movie = Movie()
    for m in missing:
        try:
            tmdb_details = movie.external(external_id=str(m), external_source="imdb_id")['movie_results'][0]
        except:
            continue

        tmdb_title = tmdb_details['title']
        try:
            tmdb_year = tmdb_details['release_date'].split("-")[0]
        except:
            tmdb_year = ''
        tmdb_id = tmdb_details['id']
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
            "rootFolderPath": "//mnt//user//PlexMedia//movies",
            "images": [{
                "covertype": "poster",
                "url": tmdb_poster
            }],
            "addOptions": {
                "searchForMovie": search
            }
        }
        headers = {
            'Content-Type': "application/json",
            'cache-control': "no-cache",
            'Postman-Token': "0eddcc07-12ba-49d3-9756-3aa8256deaf3"
        }

        response = requests.request("POST", url, data=json.dumps(payload), headers=headers, params=querystring)
        r_json = json.loads(response.text)

        try:
            if r_json[0]['errorMessage'] == "This movie has already been added":
                print(tmdb_title + " already added to Radarr")
        except KeyError:
            print("+++ " + tmdb_title + " added to Radarr")