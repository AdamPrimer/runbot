from __future__ import (absolute_import, print_function, division,
                        unicode_literals)

import os
import yaml

class RunBotConfig:
    def __init__(self, filename, folder=""):
        self.filename = filename
        self.folder = folder
        
        self._config = {
            'admin_users': 'adamprimer',
            'announce_limit': 1800,
            'display_cutoff': 80,
            'games': [],
            'keyword_blacklist': [],
            'keyword_whitelist': [],
            'services': ['twitch'],
            'update_interval': 60,
            'streamer_blacklist': [],
            'streamer_whitelist': [],
        }

        self.load()
    
    def load(self):
        with open(os.path.join(self.folder, self.filename), 'r+') as fp:
            self._config.update(yaml.safe_load(fp))

    def save(self):
        print("Saving")
        print(self._config)
        with open(os.path.join(self.folder, self.filename), 'w+') as fp:
            yaml.safe_dump(self._config, fp,
                indent=4,
                encoding=None,
                allow_unicode=True, 
                default_flow_style=False)

    def __getattr__(self, name):
        if name not in ["_config", "filename", "folder"]:
            if self._config.get(name) != None:
                return self._config.get(name)
            return None
        return self.__dict__.get(name, None)

    def __setattr__(self, name, value):
        if name not in ["_config", "filename", "folder"]:
            self._config[name] = value
        else:
            self.__dict__[name] = value

    def __str__(self):
        return self._config.__str__()
