import logging
from pong.match_tournament.tournament_session import TournamentSession
from pong.match_tournament.data_managment import Tournaments, User
from channels.layers import get_channel_layer

logger = logging.getLogger("tournament")

class TournamentSessionHandler:
    channel_layer = get_channel_layer()

    @classmethod
    def create_online_tournament_session(cls, owner_user_id: str, tournament_name: str, size: int) -> TournamentSession:
        '''Create an online tournament session'''
        if not owner_user_id:
            raise ValueError("Owner user id is required")
        if not tournament_name:
            raise ValueError("Tournament name is required")
        if not size:
            raise ValueError("Tournament size is required")
        if size < 2:
            raise ValueError("Tournament size must be at least 2")
        if Tournaments.get_by_name(tournament_name):
            raise ValueError(f"Tournament with name {tournament_name} already exists")
        if User.is_user_registered(owner_user_id):
            raise ValueError(f"User {owner_user_id} is already registered for a match or tournament")
        tournament_session = TournamentSession(owner_user_id, tournament_name, size, Tournaments.remove)
        Tournaments.add(tournament_session)
        return tournament_session

    @classmethod
    def get_tournament_session(cls, tournament_id: str) -> TournamentSession:
        '''Get a tournament session'''
        return Tournaments.get(tournament_id)

    @classmethod
    def add_user_to_tournament(cls, tournament_id: str, user_id: str) -> None:
        '''Add a user to a tournament'''
        if not tournament_id:
            raise ValueError("Tournament id is required")
        if not user_id:
            raise ValueError("User id is required")
        
        tournament = Tournaments.get(tournament_id)

        if not tournament:
            raise ValueError(f"Tournament {tournament_id} not found")
        if tournament.has_user(user_id):
            raise ValueError(f"User {user_id} is already registered to this tournament")
        if User.is_user_registered(user_id):
            raise ValueError(f"User {user_id} is already registered for a match or tournament")
        elif tournament.is_full():
            raise ValueError(f"Tournament {tournament_id} is full")
        elif tournament.is_running() or tournament.is_finished():
            raise ValueError(f"Tournament {tournament_id} is running or finished")

        tournament.add_user(user_id)
        logger.debug(f"User {user_id} added to tournament {tournament_id}")

    @classmethod
    async def remove_user_from_tournament(cls, tournament_id: str, user_id: str) -> None:
        '''Remove a user from a tournament'''
        if not tournament_id:
            raise ValueError("Tournament id is required")
        if not user_id:
            raise ValueError("User id is required")
        
        tournament = Tournaments.get(tournament_id)

        if not tournament:
            raise ValueError(f"Tournament {tournament_id} not found")
        if not tournament.has_user(user_id):
            raise ValueError(f"User {user_id} is not registered to this tournament")
        if tournament.is_running() or tournament.is_finished():
            raise ValueError(f"Cannot remove user {user_id} from tournament {tournament_id} as it is running or finished")

        logger.debug(f"Owner user id: {tournament.get_owner_user_id()}")
        if user_id == tournament.get_owner_user_id():
            await cls.cancel_tournament(tournament_id)
        else:
            tournament.remove_user(user_id)

    @classmethod
    async def remove_user_from_all_inactive_tournaments(cls, user_id: str) -> None:
        '''Remove a user from all tournaments if they are not running or finished'''
        logger.debug(f"All tournaments: {Tournaments.get_all()}")
        tournaments = list(Tournaments.get_all().values())
        for tournament in tournaments:
            logger.debug(f"Checking tournament {tournament.get_id()}")
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

        if tournament:
            if user_id == tournament.get_owner_user_id():
                await tournament.start()
            else:
                raise ValueError(f"User {user_id} is not the owner of tournament {tournament_id}")
        else:
            raise ValueError(f"Tournament {tournament_id} not found")

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
                    await cls.channel_layer.group_send(
                        f"user_{user}",
                        {
                            'type': 'tournament_cancelled',
                            'tournament_id': tournament_id
                        }
                    )
                except Exception as e:
                    logger.error(f"Failed to send cancellation message to user {user}: {e}")
            Tournaments.remove(tournament_id)
        else:
            logger.error(f"Tournament {tournament_id} not found")