from pong.match_tournament.data_managment.matchmaking_queue import MatchmakingQueue
from pong.match_tournament.data_managment.matches import Matches
from pong.match_tournament.data_managment.tournaments import Tournaments
from typing import Optional
import logging

logger = logging.getLogger("data_managment")

class User:

    @classmethod
    def is_user_registered(self, user_id) -> bool:
        '''Check if a user is registered for the matchmaking queue, a match or a tournament'''
        return MatchmakingQueue.is_user_registered(user_id) or Matches.is_user_registered(user_id) or Tournaments.is_user_registered(user_id)

    @classmethod
    def is_user_connected_to_match(self, user_id: str, match_id: str) -> bool:
        '''Check if a user is connected to a match'''
        match = Matches.get_match(match_id)
        if match:
            return match.is_user_connected(user_id)
        return False

    @classmethod
    def get_user_match_id(self, user_id) -> Optional[str]:
        '''Get the match id of a user'''
        return Matches.get_user_match_id(user_id)
    
    @classmethod
    def is_user_blocked(cls, user_id: str, match_id: str) -> bool:
        '''Check if a user is blocked from the matchmaking queue'''
        match = Matches.get_match(match_id)
        if match:
            return match.is_user_blocked(user_id)
        return False
    
    @classmethod
    def check_if_user_is_registered_somewhere(cls, user_id: str) -> None:
        '''Check if a user is registered for the matchmaking queue, a match or a tournament and raise an error if so'''
        if Matches.is_user_registered(user_id):
            raise ValueError(f"registered to match")
        elif Tournaments.is_user_registered(user_id):
            raise ValueError(f"registered to tournament")
        elif MatchmakingQueue.is_user_registered(user_id):
            raise ValueError(f"registered to queue")