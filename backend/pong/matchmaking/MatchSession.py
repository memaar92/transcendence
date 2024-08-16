import json
import struct
from asyncio import sleep
import asyncio
from uuid import uuid4
from pong.game_logic.paddle import Paddle
from pong.game_logic.ball import Ball
from pong.utils.vector2 import Vector2
from pong.utils.vector_utils import degree_to_vector
from channels.generic.websocket import AsyncWebsocketConsumer

import logging

logger = logging.getLogger("MatchSession")

class MatchSession:
    def __init__(self, player_1: AsyncWebsocketConsumer, player_2: AsyncWebsocketConsumer) -> None:
        self.player_1 = player_1
        self.player_2 = player_2
        self.paddle_left = Paddle(position=Vector2(0, 350), size=Vector2(20, 100), speed=10.0, world_size=Vector2(800, 800))
        self.paddle_right = Paddle(position=Vector2(780, 350), size=Vector2(20, 100), speed=10.0, world_size=Vector2(800, 800))
        self.ball = Ball(Vector2(400, 400), direction=degree_to_vector(55), speed=10.0, size=20, canvas_size=Vector2(800, 800), collider_list=[self.paddle_left, self.paddle_right])
        self.tick_rate = 60
        self.game_broadcast_name = f"game_{uuid4()}"
        self.player_1.groups.append(self.game_broadcast_name)
        self.player_2.groups.append(self.game_broadcast_name)
        self.score = { "player_1": 0, "player_2": 0 }

    def handle_player_input(self, player: AsyncWebsocketConsumer, paddle: Paddle) -> None:
        try:
            while True:
                data = player.get_receive_queue_item()
                if data is None:
                    return 
                try:
                    message = json.loads(data)
                    logger.info(f"Received data: {data}")
                except json.JSONDecodeError:
                    continue
                if message.get("type") == "player_update":
                    payload = message.get("payload")
                    if payload and "direction" in payload:
                        paddle.direction = payload["direction"]
        except Exception as e:
            logger.error(f"Failed to handle player input: {e}")

    def update_game_state(self) -> None:
        self.handle_player_input(self.player_1, self.paddle_left)
        self.handle_player_input(self.player_2, self.paddle_right)
        self.paddle_left.move()
        self.paddle_right.move()
        self.ball.move()

    async def run_game(self) -> None:
        try:
            while True:
                if self.player_1._closed or self.player_2._closed:
                    break
                self.update_game_state()
                binary_data = struct.pack('ffffff',
                                        self.paddle_left.position.x,
                                        self.paddle_left.position.y,
                                        self.paddle_right.position.x,
                                        self.paddle_right.position.y,
                                        self.ball.position.x,
                                        self.ball.position.y)                
                await self.broadcast_game_data(binary_data)
                await sleep(1/self.tick_rate)
        except asyncio.CancelledError:
            pass

    async def broadcast_game_data(self, data: bytes) -> None:
        await self.player_1.send(bytes_data=data)
        await self.player_2.send(bytes_data=data)

    def get_game_setup_message(self) -> dict:
        return { "type": "game_setup", "positions": {
            "paddle_left": self.paddle_left.position.to_dict(),
            "paddle_right": self.paddle_right.position.to_dict(),
            "ball": self.ball.position.to_dict()
        }
    }

    def get_player_scores_message(self, player_name: str) -> dict:
        return {
                "type": "player_scores",
                "scoring_player": player_name,
                "new_score": {
                    "player_left": self.score["player_1"],
                    "player_right": self.score["player_2"]
                }
            }
        
    def get_start_game_message(self) -> dict:
        return { "type": "start_game", "timer": 5000 }
    
    def get_running_game_message(self) -> dict:
        return { "type": "running_game" }
    
    def get_game_over_message(self) -> dict:
        return { "type": "game_over", "winner": "player_1" if self.score["player_1"] > self.score["player_2"] else "player_2" }
    
    def get_gamestate_message(self) -> bytes:
        return struct.pack('ffff',
                            self.paddle_left.position.y,
                            self.paddle_right.position.y,
                            self.ball.position.x,
                            self.ball.position.y)
        