from __future__ import (absolute_import, print_function, division,
                        unicode_literals)

import os
import yaml
import codecs

# Ridiculous requirement to get PyYAML to encode strings as unicode. 
def construct_yaml_str(self, node):
    return unicode(self.construct_scalar(node))
yaml.Loader.add_constructor(u'tag:yaml.org,2002:str', construct_yaml_str)
yaml.SafeLoader.add_constructor(u'tag:yaml.org,2002:str', construct_yaml_str)

class RunBotConfigDict(dict):
    def __init__(self, init=None):
        if isinstance(init, dict):
            for key, value in init.iteritems():
                self[key] = value

        if isinstance(init, list):
            for item in init:
                self.append(item)

    def _rkey(self, key):
        rkey = key
        if isinstance(rkey, list) or isinstance(rkey, tuple):
            rkey = rkey[0]
        if isinstance(rkey, str) or isinstance(rkey, unicode):
            rkey = rkey.lower()
        return rkey

    def _rval(self, val):
        rval = val
        if isinstance(rval, tuple):
            rval = list(rval)
        return rval

    def __setitem__(self, key, value):
        rkey = self._rkey(key)
        rval = self._rval(value)
        super(RunBotConfigDict, self).__setitem__(rkey, rval) 

    def __getitem__(self, key):
        rkey = self._rkey(key)
        return super(RunBotConfigDict, self).__getitem__(key)

    def __delitem__(self, key):
        rkey = self._rkey(key) 
        if key not in self:
            raise KeyError(rkey)
        
        rkey = self._rkey(key) 
        self.pop(rkey)
        
    def append(self, value):
        self[value] = value

    def __contains__(self, key):
        rkey = key
        is_listy = False
        if isinstance(rkey, list) or isinstance(rkey, tuple):
            if len(rkey) > 1:
                is_listy = True
            rkey = rkey[0]
        if isinstance(rkey, str) or isinstance(rkey, unicode):
            rkey = rkey.lower()

        if not is_listy:
            return rkey in self.keys()
        else:
            return (len(self.get(rkey, [])) > 1 
                    and self._rval(self[rkey][1:]) == self._rval(key[1:]))

    def __unicode__(self):
        return repr(self.values())

    def __str__(self):
        return repr(self.values())

    def __iter__(self):
        return iter(self.values())

class RunBotConfig:
    def __init__(self, filename, folder=""):
        self.filename = filename
        self.folder = folder
        
        self._config = {
            'admin_users': RunBotConfigDict(),
            'modules': RunBotConfigDict([
                'core'
            ])
        }

        self.load()
    
    def load(self):
        filename = os.path.join(self.folder, self.filename)
        if os.path.exists(filename) and os.path.isfile(filename):
            with codecs.open(filename, 'rb+', encoding='utf-8') as fp:
                loaded = yaml.safe_load(fp)
                for key, val in loaded.iteritems():
                    if isinstance(val, dict) or isinstance(val, list):
                        val = RunBotConfigDict(val)
                    loaded[key] = val
                self._config.update(loaded)

    def save(self):
        with codecs.open(os.path.join(self.folder, self.filename), 'w+',
                encoding='utf-8') as fp:
            dump = {}
            for key, val in self._config.iteritems():
                if isinstance(val, RunBotConfigDict):
                    val = dict(val)
                dump[key] = val

            yaml.safe_dump(dump, fp,
                indent=4,
                encoding='utf-8',
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

    def __repr__(self):
        return repr(self._config)

    def list_get(self, variable):
        if variable not in self._config.keys():
            self.__setattr__(variable, RunBotConfigDict())
        return self.__getattr__(variable).values()
    
    def list_add(self, variable, item):
        if variable not in self._config.keys():
            self.__setattr__(variable, RunBotConfigDict())
        return self.__getattr__(variable).append(item)

    def list_rm(self, variable, item):
        if variable not in self._config.keys():
            self.__setattr__(variable, RunBotConfigDict())
        del self.__getattr__(variable)[item]
