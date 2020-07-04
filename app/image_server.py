from flask import Flask
from flask import send_from_directory
from flask import abort
from config_tools import ImageServer
import requests
import logging
import os
import time

def check_running(config_path):
    time.sleep(1)
    config_client = ImageServer(config_path, "client")
    try:
        r = requests.get("http://" + config_client.host + ":" + str(config_client.port), verify=False, timeout=1)
        return "IMAGE SERVER RUNNING ON http://{}:{}/images/".format(config_client.host, config_client.port)
    except (requests.exceptions.ConnectTimeout, requests.exceptions.ConnectionError):
        return "IMAGE SERVER NOT RUNNING"


def start_srv(config_path):
    config_server = ImageServer(config_path, "server")
    server = Flask(__name__)
    server.upload_folder = config_server.posterdirectory
    log = logging.getLogger("werkzeug")
    os.environ['WERKZEUG_RUN_MAIN'] = 'true'
    log.setLevel(logging.ERROR)
    @server.route('/images/<path:c_name>')
    def send_file(c_name):
        app_dir = os.path.dirname(os.path.realpath(__file__))
        poster_dir = os.path.join(app_dir, config_server.posterdirectory)
        posters = os.listdir(poster_dir)
        for img in posters:
            if (c_name + ".") in img:
                return send_from_directory(server.upload_folder, img)
        return abort(404)

    try:
        server.run(host=config_server.host, port=config_server.port)
    except (OSError, TypeError) as e:
        print(e)


if __name__ == '__main__':
    start_srv(config_path)
