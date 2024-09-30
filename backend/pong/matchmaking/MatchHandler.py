from pong.matchmaking.MatchSession import MatchSession
from channels.generic.websocket import AsyncWebsocketConsumer
import logging
import asyncio
from threading import Lock

logger = logging.getLogger("MatchHandler")

class MatchHandler(object):
    _instance = None
    _lock = Lock()

    def __new__(cls):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(MatchHandler, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):  # Prevent re-initialization
            self.match_sessions = []
            self.online_matchmaking_queue = []
            self.initialized = True

    def register_client(self, client: AsyncWebsocketConsumer):
        logger.info(f"Registered client: {client.channel_name}")
        self.add_to_online_matchmaking_queue(client)
        logger.info(f"Client connected: {client.channel_name}")

    def unregister_client(self, client: AsyncWebsocketConsumer):
        try:
            self.online_matchmaking_queue.remove(client)
            logger.info(f"Client disconnected: {client.channel_name}")
        except ValueError:
            logger.warning(f"Client {client.channel_name} not found in matchmaking queue")

    def create_match(self, player_1: AsyncWebsocketConsumer, player_2: AsyncWebsocketConsumer):
        match = MatchSession(player_1, player_2)
        self.match_sessions.append(match)
        logger.info(f"Match created between {player_1.channel_name} and {player_2.channel_name}")
        return match

    def remove_match(self, match: MatchSession):
        self.match_sessions.remove(match)
        logger.info(f"Match removed: {match}")

    async def try_matchmaking(self):
        if len(self.online_matchmaking_queue) >= 2:
            player_1 = self.online_matchmaking_queue.pop(0)
            player_2 = self.online_matchmaking_queue.pop(0)
            match = self.create_match(player_1, player_2)
            asyncio.create_task(match.run_game())
            logger.info(f"Match started between {player_1.channel_name} and {player_2.channel_name}")

    def add_to_online_matchmaking_queue(self, client: AsyncWebsocketConsumer):
        self.online_matchmaking_queue.append(client)
        logger.info(f"Client added to matchmaking queue: {client.channel_name}")
        asyncio.create_task(self.try_matchmaking())
        
    def get_searching_message(self) -> dict:
        return {
            "type": "gamestatus",
            "state": "searching",
        }

    def get_found_match_message(self) -> dict:
        return {
            "type": "gamestatus",
            "state": "found",
        }
    
    def get_failed_match_message(self) -> dict:
        return {
            "type": "gamestatus",
            "state": "failed",
        }
    
    def get_error_message(self, message: str) -> dict:
        return {
            "type": "gamestatus",
            "message": "error",
        }
    
    def get_matchmaking_queue_message(self) -> dict:
        return {
            "type": "gamestatus",
            "state": "queue",
            "queue_length": len(self.online_matchmaking_queue),
        }
