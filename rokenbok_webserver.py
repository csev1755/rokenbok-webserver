import argparse
import colorlog
import configparser
import logging
import os
import signal
import sys

from server.flask import init_webserver
from server.go2rtc import Go2RTC
from server.deck import VirtualCommandDeck

version_string = "rokenbok-webserver (dev)"

if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    app_dir = os.path.abspath(os.path.dirname(sys.executable))
    bundle_dir = sys._MEIPASS
else:
    app_dir = "."
    bundle_dir = "."

argparser = argparse.ArgumentParser()
config = configparser.ConfigParser()
config.optionxform = str

if __name__ == '__main__':

    argparser.add_argument("-c", "--config", dest="config_file", help="Name of the config file", default="settings.ini")
    args = argparser.parse_args()

    # Read config file
    config_file = os.path.join(app_dir, args.config_file)
    if not os.path.exists(config_file):
        input(f"Config file '{config_file}' not found, press Enter to quit ")
        sys.exit(0)
    config.read(config_file)

    # Set log level and config for main app
    main_log_level = config['logging']['main']
    flask_log_level = config['logging']['flask']
    go2rtc_log_level = config['logging']['go2rtc']

    console_handler = colorlog.StreamHandler()
    console_handler.setLevel(main_log_level)
    console_handler.setFormatter(colorlog.ColoredFormatter(
        '%(asctime)s - %(log_color)s%(levelname)s%(reset)s - %(name)s - %(message)s',
        log_colors={
		'DEBUG':    'cyan',
		'INFO':     'green',
		'WARNING':  'yellow',
		'ERROR':    'red',
		'CRITICAL': 'red,bg_white',
	},))

    logging.basicConfig(level=main_log_level, handlers=[console_handler])
    logger = logging.getLogger(version_string)

    # Set log level for Flask
    logging.getLogger('werkzeug').setLevel(flask_log_level)

    # Init command deck and webserver
    command_deck = VirtualCommandDeck(config=config, logger=logger)
    flask, socketio = init_webserver(bundle_dir, config, command_deck, version_string)

    # Start go2rtc if configured
    go2rtc = None
    if config['webserver'].getboolean('enable_video'):
        go2rtc = Go2RTC(bundle_dir, config, go2rtc_log_level, logger)
        go2rtc.start()

    def handle_exit(sig, frame):
        print("Program interrupted, exiting...")
        if go2rtc:
            go2rtc.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_exit)

    socketio.run(flask, host=config['webserver']['listen_ip'], port=config['webserver']['listen_port'])
