from trakt import Trakt

import json
import os
import six
import copy
import ruamel.yaml
import webbrowser

def authenticate(authorization=None):
    url = Trakt['oauth'].authorize_url('urn:ietf:wg:oauth:2.0:oob')
    print('| Navigate to: %s' % url)
    print("| If you get an OAuth error your client_id or client_secret is invalid")
    webbrowser.open(url, new=2)

    code = six.moves.input('| trakt pin (case insensitive): ')
    if not code:
        exit("| No Input")

    authorization = Trakt['oauth'].token(code, 'urn:ietf:wg:oauth:2.0:oob')
    if not authorization:
        exit("| Invalid trakt pin. If you're sure you typed it in correctly your client_id or client_secret may be invalid")

    # print('Authorization: %r' % authorization)
    return authorization

def save_authorization(config_file, authorization):
    ruamel.yaml.YAML().allow_duplicate_keys = True
    from ruamel.yaml.util import load_yaml_guess_indent
    config, ind, bsi = load_yaml_guess_indent(open(config_file))
    config['trakt']['authorization'] = {'access_token': None, 'token_type': None, 'expires_in': None, 'refresh_token': None, 'scope': None, 'created_at': None}
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
