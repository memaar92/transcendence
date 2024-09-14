class TournamentSession:
    def __init__(self, tournament_id: str, tournament_name: str, tournament_type: str, tournament_size: int, tournament_players: list):
        self.tournament_id = tournament_id
        self.tournament_name = tournament_name
        self.tournament_type = tournament_type
        self.tournament_size = tournament_size
        self.tournament_players = tournament_players
        self.tournament_matches = []
        self.tournament_winner = None

    def get_tournament_id(self):
        return self.tournament_id

    def get_tournament_name(self):
        return self.tournament_name

    def get_tournament_type(self):
        return self.tournament_type

    def get_tournament_size(self):
        return self.tournament_size

    def get_tournament_players(self):
        return self.tournament_players

    def get_tournament_matches(self):
        return self.tournament_matches

    def get_tournament_winner(self):
        return self.tournament_winner

    def set_tournament_winner(self, winner):
        self.tournament_winner = winner

    def add_tournament_match(self, match):
        self.tournament_matches.append(match)

    def remove_tournament_match(self, match):
        self.tournament_matches.remove(match)

    def is_tournament_full(self):
        return len(self.tournament_players) == self.tournament_size

    def is_tournament_ready(self):
        return len(self.tournament_matches) == self.tournament_size

    def is_tournament_over(self):
        return self.tournament_winner is not None

    def __str__(self):
        return f'Tournament: {self.tournament_name} - {self.tournament_type} - {self.tournament_size} players'

    def __repr__(self):
        return f'Tournament: {self.tournament_name} - {self.tournament_type} - {self.tournament_size} players'