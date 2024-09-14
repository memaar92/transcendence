from pong.match_tournament.match_session import MatchSession
from pong.match_tournament.tournament_session import TournamentSession

class User:
    users = set()

    def add_user(self, user):
        self.users.append(user)

    def get_user(self, user_id):
        for user in self.users:
            if user.id == user_id:
                return user
        return None

    def get_users(self):
        return self.users

    def remove_user(self, user_id):
        for user in self.users:
            if user.id == user_id:
                self.users.remove(user)
                return True
        return False

    
class MatchmakingQueue:
    queue = set()

    @classmethod
    def add_to_queue(cls, user_id: str):
        '''Add a user to the matchmaking queue'''
        cls.queue.add(user_id)

    @classmethod
    def remove_from_queue(cls, user_id:str):
        '''Remove a user from the matchmaking queue'''
        for user in cls.queue:
            if user.id == user_id:
                cls.queue.remove(user)
                return True

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
    
    
class Matches:
    matches = {}

    @classmethod
    def add_match(cls, match_id: str, match: MatchSession):
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
    def is_user_registered(cls, user_id: str) -> bool:
        '''Check if a user is registered to a match or the matchmaking queue'''
        for tournament in cls.tournaments.values():
            if user_id in tournament.get_tournament_players():
                return True
        return False