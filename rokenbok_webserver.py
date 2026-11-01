import argparse
import colorlog
import configparser
import datetime
import logging
import os
import sys

from aiohttp import web

from server.web import init_webserver
from server.go2rtc import Go2RTC
from server.manager import PlayManager

version_string = "rokenbok-webserver (dev)"

# Handle paths when bundled via PyInstaller
if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    app_dir = os.path.abspath(os.path.dirname(sys.executable))
    bundle_dir = getattr(sys, "_MEIPASS")
else:
    app_dir = "."
    bundle_dir = "."

argparser = argparse.ArgumentParser()
config = configparser.ConfigParser()
config.optionxform = lambda optionstr: optionstr

if __name__ == "__main__":
    argparser.add_argument(
        "-c",
        "--config",
        dest="config_file",
        help="Name of the config file",
        default="settings.ini",
    )
    args = argparser.parse_args()

    # Read config file
    config_file = os.path.join(app_dir, args.config_file)
    if not os.path.exists(config_file):
        input(f"Config file '{config_file}' not found, press Enter to quit ")
        sys.exit(0)
    config.read(config_file)

    # Configure logging
    main_log_level = config["logging"]["main"]

    console_handler = colorlog.StreamHandler()
    console_handler.setLevel(main_log_level)
    console_handler.setFormatter(
        colorlog.ColoredFormatter(
            "%(asctime)s - %(log_color)s%(levelname)s%(reset)s - %(name)s - %(message)s",
            log_colors={
                "DEBUG": "cyan",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "red,bg_white",
            },
        )
    )

    handlers: list[logging.Handler] = [console_handler]
    if config["logging"].getboolean("file"):
        log_filename = f"rokenbok-webserver-{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"
        logfile_handler = logging.FileHandler(os.path.join(app_dir, log_filename))
        logfile_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s"))
        handlers.append(logfile_handler)
    logging.basicConfig(level=main_log_level, handlers=handlers)

    aiohttp_log_level = config["logging"]["aiohttp"]
    logging.getLogger("aiohttp.access").setLevel(aiohttp_log_level)

    logger = logging.getLogger(version_string)

    print(f"{version_string}")

    # Init manager and webserver
    play_manager = PlayManager(config=config, logger=logger)
    aiortc_app = init_webserver(bundle_dir, config, play_manager, version_string)

    # Start go2rtc if configured
    go2rtc = None
    go2rtc_log_level = config["logging"]["go2rtc"]
    if config["webserver"].getboolean("enable_video"):
        go2rtc = Go2RTC(bundle_dir, config, go2rtc_log_level, logger)
        go2rtc.start()

    # Start the webserver and handle interrupts
    try:
        web.run_app(
            aiortc_app,
            host=config["webserver"]["listen_ip"],
            port=config["webserver"].getint("listen_port"),
            shutdown_timeout=0.1,
        )
    except Exception as e:
        logger.error(f"Webserver failed to start or crashed: {e}")
    finally:
        print("Program interrupted, exiting...")
        if go2rtc:
            go2rtc.stop()
        sys.exit(0)
