from __future__ import (absolute_import, print_function, division,
                        unicode_literals)

import os
import yaml

class RunBotConfig:
    def __init__(self, filename, folder=""):
        self.filename = filename
        self.folder = folder
        
        self._config = {
            'admin_users': [],
            'modules': [
                'core'
            ]
        }

        self.load()
    
    def load(self):
        filename = os.path.join(self.folder, self.filename)
        if os.path.exists(filename) and os.path.isfile(filename):
            with open(filename, 'r+') as fp:
                self._config.update(yaml.safe_load(fp))

    def save(self):
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

    def list_add(self, variable, item):
        self._add_to_list(self.__getattr__(variable), item)

    def list_rm(self, variable, item):
        self._del_from_list(self.__getattr__(variable), item)

    def _add_to_list(self, container, item):
        if not isinstance(item, list):
            item = [item]
        
        results = []
        for itm in item:
            s = itm.lower()
            try:
                idx = [c.lower() for c in container].index(s)
                results.append(False)
            except ValueError as e:
                container.append(itm)
                results.append(True)
        return results

    def _del_from_list(self, container, item):
        if not isinstance(item, list):
            item = [item]
        
        results = []
        for s in [s.lower() for s in item]:
            try:
                idx = [c.lower() for c in container].index(s)
                container.pop(idx)
            except ValueError as e:
                results.append(False)
        return results
