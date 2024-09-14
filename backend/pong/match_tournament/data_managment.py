import logging
from pong.match_tournament.match_session import MatchSession
from pong.match_tournament.tournament_session import TournamentSession


logger = logging.getLogger("PongConsumer")

class User:
    users = set()

    @classmethod
    def add_user(self, user):
        self.users.append(user)

    @classmethod
    def get_user(self, user_id):
        for user in self.users:
            if user.id == user_id:
                return user
        return None

    @classmethod
    def get_users(self):
        return self.users

    @classmethod
    def remove_user(self, user_id):
        for user in self.users:
            if user.id == user_id:
                self.users.remove(user)
                return True
        return False

    @classmethod
    def is_user_registered(self, user_id):
        '''Check if a user is registered for the matchmaking queue, a match or a tournament'''
        return MatchmakingQueue.is_user_registered(user_id) or Matches.is_user_registered(user_id) # or Tournaments.is_user_registered(user_id)

    @classmethod
    def is_user_connected_to_match(self, user_id: str, match_id: str) -> bool:
        '''Check if a user is connected to a match'''
        match = Matches.get_match(match_id)
        if match:
            return match.is_user_connected(user_id)
        return False

    @classmethod
    def get_user_match_id(self, user_id) -> str:
        '''Get the match id of a user'''
        return Matches.get_user_match_id(user_id)

    
class MatchmakingQueue:
    queue = set()

    @classmethod
    def add_to_queue(cls, user_id: str):
        '''Add a user to the matchmaking queue'''
        cls.queue.add(user_id)
        logger.info(f"User {user_id} added to matchmaking queue")

    @classmethod
    def remove_from_queue(cls, user_id: str):
        '''Remove a user from the matchmaking queue'''
        if user_id in cls.queue:
            cls.queue.remove(user_id)
            logger.info(f"User {user_id} removed from matchmaking queue")

    @classmethod
    def get_queue(cls) -> set:
        '''Get the matchmaking queue'''
        return cls.queue
    
    @classmethod
    def get_queue_length(cls):
        '''Get the length of the matchmaking queue'''
        return len(cls.queue)
    
    @classmethod
    def is_user_registered(cls, user_id: str) -> bool:
        '''Check if a user is registered for the matchmaking queue'''
        return user_id in cls.queue
    
    @classmethod
    def pop_next_user(cls) -> str:
        '''Pop the next user from the queue'''
        if cls.queue:
            return cls.queue.pop()
        return None
    
    
class Matches:
    matches = {}

    @classmethod
    def add_match(cls, match: MatchSession):
        match_id = match.get_id()
        cls.matches[match_id] = match

    @classmethod
    def get_match(cls, match_id) -> MatchSession:
        return cls.matches.get(match_id)

    @classmethod
    def remove_match(cls, match_id) -> bool:
        if match_id in cls.matches:
            del cls.matches[match_id]
            return True
        return False

    @classmethod
    def get_matches(cls) -> dict[str, MatchSession]:
        return cls.matches
    
    @classmethod
    def get_user_match_id(cls, user_id: str) -> str:
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
    tournaments = {}

    @classmethod
    def add_tournament(cls, tournament_id: str, tournament: TournamentSession):
        cls.tournaments[tournament_id] = tournament

    @classmethod
    def get_tournament(cls, tournament_id: str) -> TournamentSession:
        return cls.tournaments.get(tournament_id)

    @classmethod
    def remove_tournament(cls, tournament_id):
        if tournament_id in cls.tournaments:
            del cls.tournaments[tournament_id]
            return True
        return False

    @classmethod
    def get_tournaments(cls):
        return cls.tournaments

    @classmethod
    def get_user_tournament_id(cls, user_id: str) -> str:
        '''Get the tournament id of a user'''
        for tournament in cls.tournaments.values():
            if user_id in tournament.get_tournament_players():
                return tournament.get_id()
        return None
    
    @classmethod
    def get_tournament_players(cls, tournament_id: str) -> set:
        '''Get the players of a tournament'''
        tournament = cls.get_tournament(tournament_id)
        if tournament:
            return tournament.get_tournament_players()
        return set()
    
    @classmethod
    def is_user_registered(cls, user_id: str) -> bool:
        '''Check if a user is registered to a match or the matchmaking queue'''
        for tournament in cls.tournaments.values():
            if user_id in tournament.get_tournament_players():
                return True
        return False