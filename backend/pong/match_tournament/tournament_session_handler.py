import logging
from pong.match_tournament.tournament_session import TournamentSession
from pong.match_tournament.data_managment import Tournaments
from uuid import uuid4

logger = logging.getLogger("PongConsumer")

class TournamentSessionHandler:

    @classmethod
    def create_online_tournament_session(cls, tournament_name: str) -> TournamentSession:
        '''Create an online tournament session'''
        tournament_id = uuid4()
        tournament_session = TournamentSession(tournament_id, tournament_name, cls.remove_tournament_session)
        Tournaments.add(tournament_session)
        return tournament_session

    @classmethod
    def remove_tournament_session(cls, tournament_id: str) -> None:
        '''Remove a tournament session'''
        tournament = Tournaments.get(tournament_id)
        if tournament:
            if tournament.is_running() and not tournament.is_finished():
                return
        Tournaments.remove(tournament_id)

    @classmethod
    def get_tournament_session(cls, tournament_id: str) -> TournamentSession:
        '''Get a tournament session'''
        return Tournaments.get(tournament_id)

    @classmethod
    def add_user_to_tournament(cls, tournament_id: str, user_id: str) -> None:
        '''Add a user to a tournament'''
        tournament = Tournaments.get(tournament_id)
        if tournament:
            tournament.add_user(user_id)

    @classmethod
    def remove_user_from_tournament(cls, tournament_id: str, user_id: str) -> None:
        '''Remove a user from a tournament'''
        tournament = Tournaments.get(tournament_id)
        if tournament:
            tournament.remove_user(user_id)

    @classmethod
    def remove_user_from_all_inactive_tournaments(cls, user_id: str) -> None:
        '''Remove a user from all tournaments if they are not running or finished'''
        for tournament in Tournaments.get_all().values():
            if tournament.is_running() or tournament.is_finished():
                continue
            else:
                tournament.remove_user(user_id)

    @classmethod
    async def start_tournament(cls, tournament_id: str) -> None:
        '''Start a tournament'''
        tournament = Tournaments.get(tournament_id)
        if tournament:
            await tournament.start()
        else:
            logger.error(f"Tournament {tournament_id} not found")