import configparser
import logging
import os
import time
import requests
import signal
import subprocess
import sys
import yaml
from flask import Flask, request, send_from_directory, render_template
from flask_socketio import SocketIO
from server.deck import VirtualCommandDeck

version_string = "rokenbok-webserver (dev)"

if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    app_dir = os.path.abspath(os.path.dirname(sys.executable))
    bundle_dir = sys._MEIPASS
else:
    app_dir = "."
    bundle_dir = "."

bin_dir = os.path.join(bundle_dir, "bin")
web_dir = os.path.join(bundle_dir, "server", "web")
flask_dir = os.path.join(web_dir, "flask")

flask = Flask(version_string, static_folder=flask_dir, template_folder=flask_dir)
socketio = SocketIO(flask)

config = configparser.ConfigParser()
config.optionxform = str
config_file = os.path.join(app_dir, "rokenbok_webserver.ini")

go2rtc_bin = os.path.join(bin_dir, "go2rtc")
go2rtc_yaml = os.path.join(bin_dir, "go2rtc.yaml")
go2rtc_www = os.path.join(web_dir, "go2rtc")

@flask.route('/')
def index():
    """
    Returns:
        str: Rendered HTML template with video configuration.
    """
    stream_config = {
        stream: f"http://{request.host.split(':')[0]}:1984/stream.html?src={stream}"
        for stream, device in config.items('video_streams')
        if device
    }
    return render_template('player.html', enable_video=config['webserver'].getboolean('enable_video'), video_streams=stream_config)

@flask.route('/player.js')
def script():
    """
    Returns:
        Response: The player.js file from the web directory.
    """
    return send_from_directory(flask_dir, 'player.js')

@socketio.on("connect")
def handle_connect():
    """
    Assigns a controller to the connecting player and broadcasts
    the updated player list to all clients.
    """
    command_deck.assign_controller(request.sid)
    socketio.emit("players", {"players": command_deck.get_players()})

@socketio.on("disconnect")
def handle_disconnect():
    """
    Releases the controller from the disconnecting player and broadcasts
    the updated player list to all clients.
    """
    command_deck.release_controller(request.sid)
    socketio.emit("players", {"players": command_deck.get_players()})

@socketio.on("controller")
def handle_controller(data):
    """
    Updates the player name and processes controller input, then broadcasts
    the updated player list to all clients.

    Args:
        data (dict): Controller data containing:
            - 'player_name' (str): Display name of the player
            - 'button' (str): Button identifier
            - 'pressed' (bool): Button state
    """
    controller = command_deck.get_controller(request.sid)
    if controller:
        controller.player_name = data['player_name']
        controller.handle_input(data)
        socketio.emit("players", {"players": command_deck.get_players()})

def handle_exit(signal, frame):
    print("Program interrupted, exiting...")
    proc.terminate()
    sys.exit(0)

signal.signal(signal.SIGINT, handle_exit)

if __name__ == '__main__':

    # Read config file
    if not os.path.exists(config_file):
        input(f"Config file '{config_file}' not found, press Enter to quit ")
        sys.exit(0)
    config.read(config_file)

    # Set log level and config for main app
    srv_log_lvl = config['webserver']['log_level']
    logging.basicConfig(level=srv_log_lvl, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(version_string)
    command_deck = VirtualCommandDeck(config=config, logger=logger)

    # Set log level for Flask
    if not config['webserver'].getboolean('flask_logs'):
        logging.getLogger('werkzeug').setLevel(logging.ERROR)

    if config['webserver'].getboolean('enable_video') is True:

        # Configure go2rtc
        go2rtc_streams = {
            stream: device
            for stream, device in config.items('video_streams')
            if device
        }
        go2rtc_config = {
            'api': {
                'static_dir': go2rtc_www
            },
            'webrtc': {
                'listen': ':8555',
                'candidates': ['stun:8555']
            },
            'streams': go2rtc_streams,
            'log': {
                'format': 'text',
                'level': srv_log_lvl,
            }
        }
        with open(go2rtc_yaml, 'w') as f:
            yaml.dump(go2rtc_config, f, default_flow_style=False, sort_keys=False)    

        # Start go2rtc subprocess
        proc = subprocess.Popen([go2rtc_bin, "-c", go2rtc_yaml])
        for i in range(10):
            try:
                response = requests.get('http://127.0.0.1:1984/api/ffmpeg/devices')
                data = response.json()
                print("Available go2rtc Devices:")
                for source in data.get('sources', []):
                    print(f" - {source.get('url')}")
                break
            except: 
                time.sleep(0.2)
                pass

    # Launch app
    socketio.run(flask, host=config['webserver']['listen_ip'], port=config['webserver']['listen_port'])
