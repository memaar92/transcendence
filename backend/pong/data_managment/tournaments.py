from typing import Dict, Optional
from ..tournament.tournament_session import TournamentSession
import logging

logger = logging.getLogger("data_managment")

class Tournaments:
    tournaments: Dict[str, TournamentSession] = {} 

    @classmethod
    def add(cls, tournament: TournamentSession) -> None:
        '''Add a tournament to the registered tournaments'''
        tournament_id = tournament.get_id()
        cls.tournaments[tournament_id] = tournament

    @classmethod
    def get(cls, tournament_id: str) -> TournamentSession:
        '''Get a tournament by id'''
        return cls.tournaments.get(tournament_id)

    @classmethod
    def remove(cls, tournament_id: str) -> bool:
        '''Remove a tournament from registered tournaments'''
        if tournament_id in cls.tournaments:
            del cls.tournaments[tournament_id]
            return True
        return False

    @classmethod
    def get_all(cls) -> dict[str, TournamentSession]:
        '''Get all tournaments'''
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
    def get_user_tournament_id(cls, user_id: int) -> Optional[str]:
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
    def is_user_registered(cls, user_id: int) -> bool:
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