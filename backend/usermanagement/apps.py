from django.apps import AppConfig
import os

class UsermanagementConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'usermanagement'

    # still a bit buggy as on startup 5 process are started. So this gets ececuted 5 times
    def ready(self):
        self.adjectives = self.getWords('adjectives.txt')
        self.nouns = self.getWords('nouns.txt')
    
    def getWords(self, file):
        words = []
        dir_path = os.path.dirname(__file__) + '/username_gen'
        with open(os.path.join(dir_path, file)) as file:
            for line in file:
                words.append(line.strip())
        return words