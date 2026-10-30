import os

from flask import Flask, request, send_from_directory, render_template
from flask_socketio import SocketIO


def init_webserver(bundle_dir, config, play_manager, server_name):
    flask_dir = os.path.join(bundle_dir, "server", "web")

    flask = Flask(server_name, static_folder=flask_dir, template_folder=flask_dir)
    socketio = SocketIO(flask)

    @flask.route("/")
    def index():
        """
        Returns:
            str: Rendered HTML template with video configuration.
        """
        stream_config = {
            stream: f"http://{request.host.split(':')[0]}:1984/stream.html?src={stream}"
            for stream, device in config.items("video_streams")
            if device
        }
        return render_template(
            "player.html",
            enable_video=config["webserver"].getboolean("enable_video"),
            video_streams=stream_config,
        )

    @flask.route("/player.js")
    def script():
        """
        Returns:
            Response: The player.js file from the web directory.
        """
        return send_from_directory(flask_dir, "player.js")

    @flask.route("/player.css")
    def stylesheet():
        """
        Returns:
            Response: The style.css file from the web directory.
        """
        return send_from_directory(flask_dir, "player.css")

    @socketio.on("connect")
    def handle_connect():
        """
        Directs the play manager to handle the connected player and broadcasts
        the updated player list to all clients.
        """
        play_manager.player_join(request.sid)  # pyright: ignore[reportAttributeAccessIssue]
        socketio.emit("players", {"players": play_manager.get_player_info()})

    @socketio.on("disconnect")
    def handle_disconnect():
        """
        Directs the play manager to handle the disconnected player and broadcasts
        the updated player list to all clients.
        """
        play_manager.player_quit(request.sid)  # pyright: ignore[reportAttributeAccessIssue]
        socketio.emit("players", {"players": play_manager.get_player_info()})

    @socketio.on("input")
    def handle_input(data):
        """
        Updates the player name and processes player inputs, then broadcasts
        the updated player list to all clients.

        Args:
            data (dict): Player data containing:
                - 'player_name' (str): Display name of the player
                - 'button' (str): Button identifier
                - 'pressed' (bool): Button state
        """
        player = play_manager.get_player_from_socket_id(request.sid)  # pyright: ignore[reportAttributeAccessIssue]
        if player:
            player.player_name = data.get("player_name", player.player_name)
            player.handle_input(data)
            socketio.emit("players", {"players": play_manager.get_player_info()})

    return flask, socketio
