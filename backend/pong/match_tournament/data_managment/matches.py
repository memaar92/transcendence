from typing import Dict, Optional
from pong.match_tournament.match_session import MatchSession
import logging
import sys

logger = logging.getLogger("data_managment")

class Matches:
    matches: Dict[str, MatchSession] = {}

    @classmethod
    def add_match(cls, match: MatchSession) -> None:
        match_id = match.get_id()
        cls.matches[match_id] = match

    @classmethod
    def get_match(cls, match_id) -> MatchSession:
        return cls.matches.get(match_id)

    @classmethod
    def remove_match(cls, match_id) -> bool:
        if match_id in cls.matches:
            logger.debug(f"Removing match {match_id}")
            logger.debug(f"Match refcount: {sys.getrefcount(cls.matches[match_id])}")
            del cls.matches[match_id]
            logger.info(f"Match {match_id} removed")
            return True
        return False

    @classmethod
    def get_matches(cls) -> Dict[str, MatchSession]:
        return cls.matches
    
    @classmethod
    def get_user_match_id(cls, user_id: str) -> Optional[str]:
        '''Get the match id of a user'''
        for match in cls.matches.values():
            if match.is_user_assigned(user_id):
                return match.get_id()
        return None
    
    @classmethod
    def is_user_registered(cls, user_id: str) -> bool:
        '''Check if a user is registered to a match or the matchmaking queue'''
        for match in cls.matches.values():
            if match.is_user_assigned(user_id):
                return True
        return False
    
    @classmethod
    def is_match_registered(cls, match_id: str) -> bool:
        '''Check if a match is registered'''
        return match_id in cls.matches

    @classmethod
    def is_user_assigned_to_match(cls, match_id: str, user_id: str) -> bool:
        '''Check if a user is assigned to a match'''
        match = cls.get_match(match_id)
        if match:
            return match.is_user_assigned(user_id)
        return False