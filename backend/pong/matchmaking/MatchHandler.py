from pong.matchmaking.MatchSession import MatchSession
from pong.matchmaking.ClientSession import 

class Matchhandler(object):
	def __new__(cls):
		if not hasattr(cls, 'instance'):
			cls.instance = super(Matchhandler, cls).__new__(cls)
			return cls.instance

	def createMatch() -> None:
		
