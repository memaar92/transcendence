from .constants import RedisKeys, MatchSessionFields

class KeyCreation:
    @staticmethod
    def create_match_session_key(match_id: str, field: MatchSessionFields) -> str:
        '''Create the key for a match session field'''
        return f"{RedisKeys.MATCHES}:{match_id}:{field}"

