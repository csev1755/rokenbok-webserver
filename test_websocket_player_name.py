
import configparser
import logging
import os
import unittest

from aiohttp.test_utils import TestClient, TestServer

from server.web import init_webserver
from server.player import Player


class FakePlayManager:
    """Minimal PlayManager substitute for the WebSocket test."""

    def __init__(self):
        self.players = {}
        self.vehicle_count = 0
        self.allow_share = False

    def player_join(self, sid):
        self.players[sid] = Player(
            self,
            player_id=1,
            logger=logging.getLogger("test"),
        )
        self.players[sid].socket_id = sid

    def player_quit(self, sid):
        self.players.pop(sid, None)

    def get_player_from_socket_id(self, sid):
        return self.players.get(sid)

    def get_player_info(self):
        return [
            {
                "player_name": player.player_name,
                "selection": player.selection,
            }
            for player in self.players.values()
        ]

    def get_vehicle_from_id(self, vehicle_id):
        return None


class PlayerNameWebSocketTest(unittest.IsolatedAsyncioTestCase):

    async def test_player_name_length_validation(self):
        config = configparser.ConfigParser()

        config.read_dict({
            "webserver": {
                "enable_video": "false",
                "max_player_name_length": "20",
            },
            "video_streams": {},
        })

        play_manager = FakePlayManager()

        app = init_webserver(
            os.getcwd(),
            config,
            play_manager,
            "test-server",
        )

        async with TestClient(TestServer(app)) as client:
            ws = await client.ws_connect("/ws")

            # Receive initial player-list broadcast.
            await ws.receive_json()

            # Get the player created by the WebSocket connection.
            player = next(iter(play_manager.players.values()))

            # Test 1: 20-character name should be accepted.
            await ws.send_json({
                "player_name": "A" * 20,
                "button": "TEST_BUTTON",
                "pressed": True,
            })

            await ws.receive_json()

            self.assertEqual(player.player_name, "A" * 20)
            self.assertIn("TEST_BUTTON", player.buttons)

            print("PASS: 20-character name accepted.")

            # Test 2: 21-character name should be rejected.
            # Button release should still be processed.
            await ws.send_json({
                "player_name": "B" * 21,
                "button": "TEST_BUTTON",
                "pressed": False,
            })

            await ws.receive_json()

            self.assertEqual(player.player_name, "A" * 20)
            self.assertNotIn("TEST_BUTTON", player.buttons)

            print("PASS: 21-character name rejected.")
            print("PASS: Normal button input still processed.")

            await ws.close()


if __name__ == "__main__":
    unittest.main()
