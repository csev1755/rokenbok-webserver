import os
import json
import asyncio
import aiohttp
import aiohttp_jinja2
import jinja2

from aiohttp import web


def init_webserver(bundle_dir, config, command_deck, server_name):
    web_dir = os.path.join(bundle_dir, "server", "web")

    app = web.Application()
    aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader(web_dir))

    # Store active WebSocket connections
    app["websockets"] = set()

    @aiohttp_jinja2.template("player.html")
    async def index(request):
        """
        Returns:
            dict: Video configuration and stream settings to be rendered by the template.
        """
        stream_config = {
            stream: f"http://{request.host.split(':')[0]}:1984/stream.html?src={stream}"
            for stream, device in config.items("video_streams")
            if device
        }
        return {
            "enable_video": config["webserver"].getboolean("enable_video"),
            "video_streams": stream_config,
        }

    async def script(request):
        """
        Returns:
            Response: The player.js file from the web directory.
        """
        return web.FileResponse(os.path.join(web_dir, "player.js"))

    async def stylesheet(request):
        """
        Returns:
            Response: The style.css file from the web directory.
        """
        return web.FileResponse(os.path.join(web_dir, "player.css"))

    async def broadcast_state(event, data):
        """
        Broadcast the player list to all clients.
        """
        payload = json.dumps({event: data})
        for ws in list(app["websockets"]):
            try:
                await ws.send_str(payload)
            except Exception:
                app["websockets"].remove(ws)

    async def handle_connect(sid):
        """
        Assigns a controller to the connecting player and broadcasts
        the updated player list to all clients.
        """
        command_deck.assign_controller(sid)
        await broadcast_state("players", command_deck.get_players())

    async def handle_disconnect(sid):
        """
        Releases the controller from the disconnecting player.
        """
        command_deck.release_controller(sid)
        await broadcast_state("players", command_deck.get_players())

    async def handle_controller(sid, data):
        """
        Updates the player name and processes controller input.

        Args:
            sid (str): Session identifier
            data (dict): Controller data containing:
                - 'player_name' (str): Display name of the player
                - 'button' (str): Button identifier
                - 'pressed' (bool): Button state
        """
        controller = command_deck.get_controller(sid)
        if controller:
            controller.player_name = data.get("player_name", controller.player_name)
            controller.handle_input(data)
            await broadcast_state("players", command_deck.get_players())

    async def handle_websocket(request):
        """
        Handles player connections, disconnections, and controller input.
        """
        ws = web.WebSocketResponse()
        await ws.prepare(request)

        sid = str(id(ws))
        request.app["websockets"].add(ws)

        try:
            await handle_connect(sid)
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    data = json.loads(msg.data)
                    await handle_controller(sid, data)
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    print(f"WebSocket connection closed with exception {ws.exception()}")
        # Handle interrupts
        except asyncio.CancelledError:
            pass
        finally:
            request.app["websockets"].remove(ws)
            try:
                await handle_disconnect(sid)
            except Exception:
                pass

        return ws

    app.router.add_get("/", index)
    app.router.add_get("/player.js", script)
    app.router.add_get("/player.css", stylesheet)
    app.router.add_get("/ws", handle_websocket)

    return app
