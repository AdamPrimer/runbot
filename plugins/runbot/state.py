from __future__ import (absolute_import, print_function, division,
                        unicode_literals)

import os
import re
import time
import requests

from plugins.runbot.services import load_services, available_services

class RunBotState:
    def __init__(self, games=[], 
            keyword_whitelist=[],
            keyword_blacklist=[],
            announce_limit=1800,
            services=[],
            streamer_blacklist_file="streamer_blacklist.txt"):
        
        self.games = games
        self.keyword_whitelist = keyword_whitelist
        self.keyword_blacklist = keyword_blacklist
        self.announce_limit = announce_limit

        self.streamer_blacklist_file = streamer_blacklist_file
        self.streamer_blacklist = self.load_streamer_blacklist()
        self.streamer_whitelist = []

        load_services(services)

        self.services = {}
        for service in services:
            self.services[service] = available_services[service](self.games)

        self._streams = {}
        self.announcements = {}
    
    @property
    def streams(self):
        return self.filter_streams(self._streams)

    def blacklist_streamer(self, streamer):
        if not isinstance(streamer, list):
            streamer = [streamer]
            
        for s in [s.lower() for s in streamer]:
            if s not in self.state.streamer_blacklist:
                self.state.streamer_blacklist.append(s)

        self.state.save_streamer_blacklist()

    def unblacklist_streamer(self, streamer):
        if not isinstance(streamer, list):
            streamer = [streamer]
            
        for s in [s.lower() for s in streamer]:
            if s in self.state.streamer_blacklist:
                self.state.streamer_blacklist.remove(s)

        self.state.save_streamer_blacklist()

    def load_streamer_blacklist(self):
        if not os.path.exists(self.streamer_blacklist_file):
            return []
        
        with open(self.streamer_blacklist_file, 'r+') as fp:
            return [line.strip() for line in fp.readlines()]

    def save_streamer_blacklist(self):
        with open(self.streamer_blacklist_file, 'w+') as fp:
            for streamer in self.streamer_blacklist:
                fp.write("{}\n".format(streamer))

    def apply_streamer_blacklist(self, streams):
        if not self.streamer_blacklist:
            return streams

        return {stream_id: stream for stream_id, stream in streams.iteritems()
            if stream['streamer'].lower() not in self.streamer_blacklist}

    def apply_keyword_whitelist(self, streams):
        if not self.keyword_whitelist:
            return streams
        
        whitelist = '|'.join(re.escape(term) for term in self.keyword_whitelist)
        whitelist_re = re.compile(whitelist, flags=re.IGNORECASE)

        return {stream_id: stream for stream_id, stream in streams.iteritems()
            if whitelist_re.search(stream['title'] or '')}

    def apply_keyword_blacklist(self, streams):
        if not self.keyword_blacklist:
            return streams
        
        blacklist = '|'.join(re.escape(term) for term in self.keyword_blacklist)
        blacklist_re = re.compile(blacklist, flags=re.IGNORECASE)

        return {stream_id: stream for stream_id, stream in streams.iteritems()
            if not blacklist_re.search(stream['title'] or '')}

    def filter_streams(self, all_streams):
        streams = self.apply_keyword_whitelist(all_streams)
        streams = self.apply_keyword_blacklist(streams)
        streams = self.apply_streamer_blacklist(streams)
        return streams

    def update_streams(self, on_new_broadcast):
        print("Checking For Streams...")
        latest_streams = {}
            
        for name, service in self.services.iteritems():
            try:
                streams = [service.extract_stream_info(stream)
                    for stream in service.get_all_streams()]
            except Exception:
                pass
            
            latest_streams = {"{}_{}".format(name, stream['streamer']): stream
                    for stream in streams}

        if on_new_broadcast:
            announce_cutoff = time.time() - self.announce_limit
            for stream_id, stream in self.filter_streams(latest_streams).iteritems():
                if (stream_id not in self.streams 
                        and (
                            stream_id not in self.announcements
                            or self.announcements[stream_id] < announce_cutoff)):

                    on_new_broadcast(stream)
                self.announcements[stream_id] = time.time()
    
        self._streams = latest_streams
