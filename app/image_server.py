from flask import Flask
from flask import send_from_directory
from flask import abort
from config_tools import ImageServer
import requests
import logging
import os
import time

class Server:
    def __init__(self, config_path):
        self.server = ImageServer(config_path)
        try:
            self.host = self.server.host
        except AttributeError:
            self.host = "0.0.0.0"
        try:
            self.port = self.server.port
        except AttributeError:
            self.port = "5000"


def check_running(config_path):
    time.sleep(1)
    srv = Server(config_path)
    try:
        r = requests.get("http://" + srv.host + ":" + str(srv.port), verify=False, timeout=1)
        return "IMAGE SERVER RUNNING ON http://{}:{}/images/".format(srv.host, srv.port)
    except (requests.exceptions.ConnectTimeout, requests.exceptions.ConnectionError):
        return "IMAGE SERVER NOT RUNNING"


def start_srv(config_path):
    server = Server(config_path)
    app = Flask(__name__)
    app.upload_folder = "images"
    log = logging.getLogger("werkzeug")
    os.environ['WERKZEUG_RUN_MAIN'] = 'true'
    log.setLevel(logging.ERROR)
    @app.route('/images/<path:c_name>')
    def send_file(c_name):
        cwd = os.getcwd()
        images = os.listdir(os.path.join(cwd, "images"))
        for img in images:
            if (c_name + ".") in img:
                return send_from_directory(app.upload_folder, img)
        return abort(404)

    try:
        app.run(host=server.host, port=server.port)
    except (OSError, TypeError) as e:
        print(e)


if __name__ == '__main__':
    start_srv(config_path)
