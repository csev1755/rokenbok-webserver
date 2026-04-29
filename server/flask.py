import os

from flask import Flask, request, send_from_directory, render_template
from flask_socketio import SocketIO

def init_webserver(bundle_dir, config, command_deck, server_name):
    web_dir = os.path.join(bundle_dir, "server", "web")
    flask_dir = os.path.join(web_dir, "flask")

    flask = Flask(server_name, static_folder=flask_dir, template_folder=flask_dir)
    socketio = SocketIO(flask)

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
        return render_template(
            'player.html',
            enable_video=config['webserver'].getboolean('enable_video'),
            video_streams=stream_config
        )

    @flask.route('/player.js')
    def script():
        """
        Returns:
            Response: The player.js file from the web directory.
        """
        return send_from_directory(flask_dir, 'player.js')
    
    @flask.route('/player.css')
    def stylesheet():
        """
        Returns:
            Response: The style.css file from the web directory.
        """
        return send_from_directory(flask_dir, 'player.css')

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
            controller.player_name = data.get('player_name', controller.player_name)
            controller.handle_input(data)
            socketio.emit("players", {"players": command_deck.get_players()})

    return flask, socketio
