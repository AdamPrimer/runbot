from __future__ import (absolute_import, print_function, division,
                        unicode_literals)

import re
import time
import requests

from plugins.runbot.services import load_services, available_services

class RunBotState:
    def __init__(self, games=[], 
            keyword_whitelist=[],
            keyword_blacklist=[],
            announce_limit=1800,
            services=[]):
        
        self.games = games
        self.keyword_whitelist = keyword_whitelist
        self.keyword_blacklist = keyword_blacklist
        self.announce_limit = announce_limit

        load_services(services)

        self.services = {}
        for service in services:
            self.services[service] = available_services[service](self.games, 
                self.keyword_whitelist,
                self.keyword_blacklist
            )

        self.streams = {}
        self.announcements = {}
    
    def update_streams(self, on_new_broadcast):
        print("Checking For Streams...")
        latest_streams = {}
            
        for name, service in self.services.iteritems():
            streams = [service.extract_stream_info(stream) 
                for stream in service.get_filtered_streams()]
            
            latest_streams = {"{}_{}".format(name, stream['streamer']): stream
                    for stream in streams}

        if on_new_broadcast:
            announce_cutoff = time.time() - self.announce_limit
            for stream_id, stream in latest_streams.iteritems():
                if (stream_id not in self.streams 
                        and (
                            stream_id not in self.announcements
                            or self.announcements[stream_id] < announce_cutoff)):

                    on_new_broadcast(stream)
                    self.announcements[stream_id] = time.time()
    
        self.streams = latest_streams
