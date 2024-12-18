import logging
from django.conf import settings
from ..tournament.tournament_session import TournamentSession
from ..data_managment.tournaments import Tournaments
from ..data_managment.user import User
from ..data_managment.matches import Matches
from ..data_managment.matchmaking_queue import MatchmakingQueue
from channels.layers import get_channel_layer

logger = logging.getLogger("tournament")

MIN_PLAYERS = settings.TOURNAMENT_CONFIG['min_players']
MAX_PLAYERS = settings.TOURNAMENT_CONFIG['max_players']

class TournamentSessionHandler:
    _channel_layer = get_channel_layer()

    @classmethod
    def create_online_tournament_session(cls, owner_user_id: int, tournament_name: str, size: int) -> TournamentSession:
        '''Create an online tournament session'''
        if not owner_user_id:
            raise ValueError("Owner user id is required")
        if not tournament_name:
            raise ValueError("Tournament name is required")
        if not size:
            raise ValueError("Tournament size is required")
        if size < MIN_PLAYERS:
            raise ValueError("tournament size is too small")
        if size > MAX_PLAYERS:
            raise ValueError("tournament size is too large")
        User.check_if_user_is_registered_somewhere(owner_user_id)
        if Tournaments.get_by_name(tournament_name):
            raise ValueError(f"tournament with name exists")
        tournament_session = TournamentSession(owner_user_id, tournament_name, size, Tournaments.remove)
        Tournaments.add(tournament_session)
        return tournament_session

    @classmethod
    def get_tournament_session(cls, tournament_id: str) -> TournamentSession:
        '''Get a tournament session'''
        return Tournaments.get(tournament_id)

    @classmethod
    def add_user_to_tournament(cls, tournament_id: str, user_id: int) -> None:
        '''Add a user to a tournament'''
        if not tournament_id:
            raise ValueError("Tournament id is required")
        if not user_id:
            raise ValueError("User id is required")

        tournament = Tournaments.get(tournament_id)

        if not tournament:
            raise ValueError(f"tournament does not exist")
        
        User.check_if_user_is_registered_somewhere(user_id)

        if tournament.is_full():
            raise ValueError(f"is full")
        elif tournament.is_running() or tournament.is_finished():
            raise ValueError(f"already started")

        tournament.add_user(user_id)
        logger.debug(f"User {user_id} added to tournament {tournament_id}")

    @classmethod
    async def remove_user_from_tournament(cls, tournament_id: str, user_id: int) -> None:
        '''Remove a user from a tournament'''
        if not tournament_id:
            raise ValueError("Tournament id is required")
        if not user_id:
            raise ValueError("User id is required")
        
        tournament = Tournaments.get(tournament_id)

        if not tournament:
            raise ValueError(f"tournament does not exist")
        if not tournament.has_user(user_id):
            raise ValueError(f"not registered to tournament")
        if tournament.is_running() or tournament.is_finished():
            raise ValueError(f"already started")

        if user_id == tournament.get_owner_user_id():
            await cls.cancel_tournament(tournament_id)
        else:
            tournament.remove_user(user_id)
        logger.debug(f"User {user_id} removed from tournament {tournament_id}")

    @classmethod
    async def remove_user_from_all_inactive_tournaments(cls, user_id: int) -> None:
        '''Remove a user from all tournaments if they are not running or finished'''
        tournaments = list(Tournaments.get_all().values())
        for tournament in tournaments:
            if not tournament.is_running() and not tournament.is_finished():
                logger.debug(f"Removing user {user_id} from tournament {tournament.get_id()}")
                try:
                    await cls.remove_user_from_tournament(tournament.get_id(), user_id)
                except Exception as e:
                    logger.error(f"Failed to remove user {user_id} from tournament {tournament.get_id()}: {e}")

    @classmethod
    async def start_tournament(cls, user_id, tournament_id: str) -> None:
        '''Start a tournament'''
        if not user_id:
            raise ValueError("User id is required")
        elif not tournament_id:
            raise ValueError("Tournament id is required")
        
        tournament = Tournaments.get(tournament_id)

        if not tournament:
            raise ValueError(f"tournament does not exist")

        if user_id == tournament.get_owner_user_id():
            for user in tournament.get_users():
                await cls._channel_layer.group_send(
                    f"mm_{user}",
                    {
                        'type': 'tournament_starting',
                    }
                )
            await tournament.start()
        else:
            raise ValueError(f"not the tournament owner")

    @classmethod
    async def request_cancel_tournament(cls, user_id: int, tournament_id: str) -> None:
        '''Request to cancel a tournament'''
        if not user_id:
            raise ValueError("User id is required")
        elif not tournament_id:
            raise ValueError("Tournament id is required")
        
        tournament = Tournaments.get(tournament_id)

        if not tournament:
            raise ValueError(f"tournament does not exist")
        elif tournament.is_running() or tournament.is_finished():
            raise ValueError(f"already started")

        if user_id == tournament.get_owner_user_id():
            await cls.cancel_tournament(tournament_id)
        else:
            raise ValueError(f"not the tournament owner")

    @classmethod
    async def cancel_tournament(cls, tournament_id: str) -> None:
        '''Cancel a tournament'''
        logger.debug(f"Cancelling tournament {tournament_id}")
        if not tournament_id:
            raise ValueError("Tournament id is required")
        tournament = Tournaments.get(tournament_id)
        if tournament:
            for user in tournament.get_users():
                try:
                    await cls._channel_layer.group_send(
                        f"mm_{user}",
                        {
                            'type': 'tournament_canceled',
                    });
                except Exception as e:
                    logger.error(f"Failed to send cancellation message to user {user}: {e}")
            Tournaments.remove(tournament_id)
        else:
            logger.error(f"Tournament {tournament_id} not found")