from trakt import Trakt

import json
import os
import six
import copy
import ruamel.yaml
import webbrowser

def authenticate(authorization=None, headless=False):

    if authorization['access_token']:
        # Test authorization
        with Trakt.configuration.oauth.from_response(authorization, refresh=True):
            if Trakt['users/settings']:
                # Successful authorization
                return authorization
    if not headless:
        url = Trakt['oauth'].authorize_url('urn:ietf:wg:oauth:2.0:oob')
        print('| Navigate to: %s' % url)
        print("| If you get an OAuth error your client_id or client_secret is invalid")
        webbrowser.open(url, new=2)

        code = six.moves.input('| trakt pin: ')
        if not code:
            exit("| No Input")

        authorization = Trakt['oauth'].token(code, 'urn:ietf:wg:oauth:2.0:oob')
        if not authorization:
            exit("| Invalid trakt pin")

        # print('Authorization: %r' % authorization)
        return authorization

def save_authorization(config_file, authorization):
    ruamel.yaml.YAML().allow_duplicate_keys = True
    from ruamel.yaml.util import load_yaml_guess_indent
    config, ind, bsi = load_yaml_guess_indent(open(config_file))
    config['trakt']['authorization']['access_token'] = authorization['access_token']
    config['trakt']['authorization']['token_type'] = authorization['token_type']
    config['trakt']['authorization']['expires_in'] = authorization['expires_in']
    config['trakt']['authorization']['refresh_token'] = authorization['refresh_token']
    config['trakt']['authorization']['scope'] = authorization['scope']
    config['trakt']['authorization']['created_at'] = authorization['created_at']
    print('| Saving authorization information to {}'.format(config_file))
    ruamel.yaml.round_trip_dump(
        config,
        open(config_file, 'w'),
        indent=ind,
        block_seq_indent=bsi
    )
