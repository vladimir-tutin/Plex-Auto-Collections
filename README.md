# Plex Auto Collections
![https://i.imgur.com/iHAYFIZ.png](https://i.imgur.com/iHAYFIZ.png)
Plex Auto Collections is a Python 3 script/[standalone builds](https://github.com/vladimir-tutin/Plex-Auto-Collections/tree/master/dist) that 
works off a configuration file to create/update Plex collection. Collection management with this tool can be automated 
in a varying degree of customizability. Supports IMDB, TMDb, and Trakt lists as well as built in Plex 
filters such as actors, genres, year, studio and more. For more filters refer to the 
[plexapi.video.Movie](https://python-plexapi.readthedocs.io/en/latest/modules/video.html#plexapi.video.Movie) 
documentation. Not everything has been tested, so results may vary based off the filter. A TMDb api key is required to 
scan TMDb URLs.

When parsing IMDB or TMBd lists the script will create a list of movies that are missing from Plex. If an TMDb and 
Radarr api-key are supplied then the option will be presented to pass the list of movies along to Radarr. Trakt lists will be matched against items in both a Movie and a TV library, each.

As well as updating collections based off configuration files there is the ability to add new collections based off 
filters, delete collections, search for collections and manage the collections in the configuration file. Collection 
poster and summary can also be managed with this script.

Thanks to [/u/deva5610](https://www.reddit.com/user/deva5610) for 
[IMDBList2PlexCollection](https://github.com/deva5610/IMDBList2PlexCollection) which prompted the idea for a 
configuration based collection manager.

Subfilters also allows for a little more granular selection of movies to add to a collection. Unlike regular filters, a 
movie must match at least one value from each subfilter to be added to a collection.

# Configuration
Modify the supplied config.yml.template file.

If using TMDb lists be sure to include your TMDb api-key. If you do not have an api-key please refer to this 
[document](https://developers.themoviedb.org/3/getting-started/introduction).

If you do not want it to have the option to submit movies that are missing from IMDB or TMBd lists do not include the 
api-key for Radarr. Radarr support has not been tested with Trakt lists. Sonarr support has not yet been implemented.

Adding a summary to the collection is possible by either pulling the overview from TMDb or by using a custom entry. To
use a TMDb entry a TMDb api-key as well as language is required, the default language is set to en. Match the following 
in the configuration file, input only the TMDb collections page's ID. Use the actor's page ID on TMBd if you wish to 
use their biography as the summary.

    Jurassic Park:
        tmdb-list: https://www.themoviedb.org/collection/328
        details:
            tmdb-summary: 328

If you would like to use a custom summary, enter as follows

    Jurassic Park:
        tmdb-list: https://www.themoviedb.org/collection/328
        details:
            summary: A collection of Jurassic Park movies
            
Adding a poster can be done by adding the URL to the image.

    Jurassic Park:
        tmdb-list: https://www.themoviedb.org/collection/328
        details:
            tmdb-summary: 328
            poster: https://i.imgur.com/QMjbyCX.png

Local assets are supported by running the script with the image server running. If there are no details filled out for 
the poster in the configuration file and the image server is running the script will attempt to match a collection name 
with an image file of the same name. Images should be placed in the ./images folder. Port forwarding is not required.

If you want movies to add to Radarr but not automatically search, change search to "false".

In order to find your Plex token follow 
[this guide](https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/).

Trakt lists require a client id and client secret.
1. [Create](https://trakt.tv/oauth/applications/new) a Trakt API application.
2. Enter a `Name` for the application.
3. Enter `urn:ietf:wg:oauth:2.0:oob` for `Redirect uri`.
4. Click the `SAVE APP` button.
5. Record the `Client ID` and `Client Secret`. 

Library should be the name of the Plex library that you are wanting to search and create collections in.

Main filters allowed are actors, imdb-list as well as many attributes that can found in the [plexapi.video.Movie 
documentation](https://python-plexapi.readthedocs.io/en/latest/modules/video.html#plexapi.video.Movie). In addition 
subfilters for audio language, subtitle language and video-resolution have been created. Take note that the values for 
each must match what Plex has including special characters in order to match.

    subfilters:
        video-resolution: 1080 (further examples: sd, 720, 4k)
        audio-language: Français
        subtitle-language: English

If you do not want to use subfilters simply remove the section.

**Once complete it should look like**
```
collections:
  Jurassic Park:
    tmdb-list: https://www.themoviedb.org/collection/328
       details:
         tmdb-summary: 328
         poster: https://i.imgur.com/QMjbyCX.png
  1080p Documentaries:
    genres: Documentary
    subfilters:
      video-resolution: 1080
    details:
       summary: A collection of 1080p Documentaries
  Daniel Craig only James Bonds:
    imdb-list: https://www.imdb.com/list/ls006405458/
    subfilters:
      actors: Daniel Craig
  Christmas:
    trakt-list:
      - https://trakt.tv/users/movistapp/lists/christmas-movies
      - https://trakt.tv/users/2borno2b/lists/christmas-movies-extravanganza
  Marvel:
    trakt-list: https://trakt.tv/users/movistapp/lists/marvel
plex:
  library: Movies
  library_type: movie # or 'show'
  token: ################ 
  url: http://192.168.1.5:32400
radarr:
  url: http://192.168.1.5:7878/radarr/
  token: ################ 
  quality_profile_id: 4
  root_folder_path: /mnt/user/PlexMedia/movies
  search: true
tmdb:
  apikey: ################ 
  language: en
trakt:
  client_id: ################ 
  client_secret: ################ 
  # Below is filled in automatically when the script is run
  authorization:
    access_token:
    token_type:
    expires_in:
    refresh_token:
    scope:
    created_at:
image-server:
  host: 192.168.1.41
  port: 5000
```

# Usage
[Standalone binaries](https://github.com/vladimir-tutin/Plex-Auto-Collections/tree/master/dist) have been created for both Windows and Linux.

If you would like to run from Python I have only tested this fully on Python 3.7.4. Dependencies must be installed by running

    pip install -r requirements.txt
    
If there are issues installing PyYAML 1.5.4 try

    pip install -r requirements.txt --ignore-installed
    
Make sure that plexapi is installed from the github source in requirements.txt. The one provided by pip contains a bug 
that will cause certain movies to crash the script when processing IMDB lists. To ensure that you are running the of 
plexapi check utils.py contains the following around line 172:

    def toDatetime(value, format=None):
    """ Returns a datetime object from the specified value.

        Parameters:
            value (str): value to return as a datetime
            format (str): Format to pass strftime (optional; if value is a str).
    """
    if value and value is not None:
        if format:
            value = datetime.strptime(value, format)
        else:
            value = datetime.fromtimestamp(int(value))
    return value

To run the script in a terminal run

    python plex_auto_collections.py
    
If you would like to schedule the script to run on a schedule the script can be launched to automatically and only 
based off the collection and then quit by running. This applies to the standalones as well.

    python plex_auto_collections.py --update

If you would like to not run the image server add the --noserver flag to the command

    python plex_auto_collections.py --noserver
    
A different configuration file can be specified with the -c <path_to_config> or --config_path <path_to_config>. This is useful for creating collections against different libraries, such as a Movie and TV library. In this case, be sure to update the `library_type` in the configuration file.

```
python plex_auto_collections.py -c <path_to_config>
```
