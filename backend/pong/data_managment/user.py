from ..data_managment.matchmaking_queue import MatchmakingQueue
from ..data_managment.matches import Matches
from ..data_managment.tournaments import Tournaments
from typing import Optional
import logging

logger = logging.getLogger("data_managment")

class User:

    @classmethod
    def is_user_registered(self, user_id: int) -> bool:
        '''Check if a user is registered for the matchmaking queue, a match or a tournament'''
        return MatchmakingQueue.is_user_registered(user_id) or Matches.is_user_registered(user_id) or Tournaments.is_user_registered(user_id)

    @classmethod
    def is_user_connected_to_match(self, user_id: int, match_id: str) -> bool:
        '''Check if a user is connected to a match'''
        match = Matches.get_match(match_id)
        if match:
            return match.is_user_connected(user_id)
        return False

    @classmethod
    def get_user_match_id(self, user_id: int) -> Optional[str]:
        '''Get the match id of a user'''
        return Matches.get_user_match_id(user_id)
    
    @classmethod
    def is_user_blocked(cls, user_id: int, match_id: str) -> bool:
        '''Check if a user is blocked from the matchmaking queue'''
        match = Matches.get_match(match_id)
        if match:
            return match.is_user_blocked(user_id)
        return False
    
    @classmethod
    def check_if_user_is_registered_somewhere(cls, user_id: int) -> None:
        '''Check if a user is registered for the matchmaking queue, a match or a tournament and raise an error if so'''
        if Matches.is_user_registered(user_id):
            raise ValueError(f"registered to match")
        elif Tournaments.is_user_registered(user_id):
            raise ValueError(f"registered to tournament")
        elif MatchmakingQueue.is_user_registered(user_id):
            raise ValueError(f"registered to queue")
        
    @classmethod
    def get_opponent_user_id(self, user_id: int, match_id: str) -> Optional[str]:
        '''Get the opponent user id for a match'''
        match = Matches.get_match(match_id)
        if match:
            return match.get_opponent_user_id(user_id)
        return None

    @classmethod
    def get_registered_game_type(cls, user_id: str) -> Optional[str]:
        '''Get the type of game the user is registered to'''
        if Matches.is_user_registered(user_id):
            return "match"
        elif Tournaments.is_user_registered(user_id):
            return "tournament"
        elif MatchmakingQueue.is_user_registered(user_id):
            return "queue"
        return None

    @classmethod
    def assign_to_game(cls, user_id: str, game_type: str, game_id: str) -> None:
        '''Assign a user to a game'''
        if game_type == "match":
            Matches.get_match(game_id).assign_user(user_id)
        elif game_type == "tournament":
            Tournaments.get_tournament(game_id).assign_user(user_id)
        elif game_type == "queue":
            MatchmakingQueue.assign_user(user_id)
        else:
            raise ValueError(f"Invalid game type: {game_type}")