import logging
from pong.match_tournament.match_session import MatchSession
from pong.match_tournament.tournament_session import TournamentSession
from typing import Dict, Any, Set, Optional


logger = logging.getLogger("PongConsumer")

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

    
class MatchmakingQueue:
    queue: Set[str] = set()

    @classmethod
    def add_to_queue(cls, user_id: str) -> None:
        '''Add a user to the matchmaking queue'''
        cls.queue.add(user_id)
        logger.info(f"User {user_id} added to matchmaking queue")

    @classmethod
    def remove_from_queue(cls, user_id: str) -> None:
        '''Remove a user from the matchmaking queue'''
        if user_id in cls.queue:
            cls.queue.remove(user_id)
            logger.info(f"User {user_id} removed from matchmaking queue")

    @classmethod
    def get_queue(cls) -> set:
        '''Get the matchmaking queue'''
        return cls.queue
    
    @classmethod
    def get_queue_length(cls) -> int:
        '''Get the length of the matchmaking queue'''
        return len(cls.queue)
    
    @classmethod
    def is_user_registered(cls, user_id: str) -> bool:
        '''Check if a user is registered for the matchmaking queue'''
        return user_id in cls.queue
    
    @classmethod
    def pop_next_user(cls) -> Optional[str]:
        '''Pop the next user from the queue'''
        if cls.queue:
            return cls.queue.pop()
        return None

    
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
    
class Tournaments:
    tournaments: Dict[str, TournamentSession] = {} 

    @classmethod
    def add(cls, tournament: TournamentSession) -> None:
        tournament_id = tournament.get_id()
        cls.tournaments[tournament_id] = tournament

    @classmethod
    def get(cls, tournament_id: str) -> TournamentSession:
        return cls.tournaments.get(tournament_id)

    @classmethod
    def remove(cls, tournament_id) -> bool:
        if tournament_id in cls.tournaments:
            del cls.tournaments[tournament_id]
            return True
        return False

    @classmethod
    def get_all(cls) -> dict[str, TournamentSession]:
        return cls.tournaments
    
    @classmethod
    def get_open_tournaments(cls) -> dict[str, TournamentSession]:
        '''Get all open tournaments'''
        open_tournaments = {}
        for tournament_id, tournament in cls.tournaments.items():
            if not tournament.is_running() and not tournament.is_finished():
                open_tournaments[tournament_id] = tournament
        return open_tournaments

    @classmethod
    def get_user_tournament_id(cls, user_id: str) -> Optional[str]:
        '''Get the tournament id of a user'''
        for tournament in cls.tournaments.values():
            if user_id in tournament.get_users():
                return tournament.get_id()
        return None
    
    @classmethod
    def get_tournament_players(cls, tournament_id: str) -> set:
        '''Get the players of a tournament'''
        tournament = cls.get(tournament_id)
        if tournament:
            return tournament.get_users()
        return set()
    
    @classmethod
    def is_user_registered(cls, user_id: str) -> bool:
        '''Check if a user is registered to a tournament'''
        for tournament in cls.tournaments.values():
            if tournament.has_user(user_id):
                return True
        return False
    
    @classmethod
    def get_by_name(cls, tournament_name: str) -> Optional[TournamentSession]:
        '''Get a tournament by name'''
        for tournament in cls.tournaments.values():
            if tournament.get_name() == tournament_name:
                return tournament
        return None
    
    @classmethod
    def get_name_by_id(cls, tournament_id: str) -> Optional[str]:
        '''Get the name of a tournament by id'''
        tournament = cls.get(tournament_id)
        if tournament:
            return tournament.get_name()
        return None