from __future__ import (absolute_import, print_function, division,
                        unicode_literals)

import os
import re
import time
import yaml
import requests

from plugins.runbot.config import RunBotConfig
from plugins.runbot.services import load_services, available_services

class RunBotState:
    def __init__(self, irc_c, channel, config_file, superadmins=None, config_folder=""):
        self.irc_c = irc_c
        self.channel = channel
        self.config = RunBotConfig(config_file, config_folder)
        self.superadmins = superadmins

        load_services(self.config.services)

        self.services = {}
        for service in self.config.services:
            self.services[service] = available_services[service](self.config.games)

        self._streams = {}
        self.announcements = {}

        self.stream_spam_limit = 8
        
        self.update_streams(on_new_broadcast=None)

        print("Channel {} initialized.".format(self.channel))
    
    @property
    def streams(self):
        return self.filter_streams(self._streams)

    def add_to_list(self, variable, keyword):
        if variable in ['keyword_whitelist', 'games']:
            self._add_to_list(self.config.__getattr__(variable), " ".join(keyword))
        else:
            self._add_to_list(self.config.__getattr__(variable), keyword)
        self.config.save()
        return True

    def del_from_list(self, variable, keyword):
        if variable in ['keyword_blacklist', 'games']:
            self._del_from_list(self.config.__getattr__(variable), " ".join(keyword))
        elif variable in ['admin_users']:
            for user in keyword:
                if user.lower() in self.superadmins:
                    return False
            self._del_from_list(self.config.__getattr__(variable), keyword)
        else:
            self._del_from_list(self.config.__getattr__(variable), keyword)
        self.config.save()
        return True

    def apply_streamer_whitelist(self, streams, all_streams):
        if not self.config.streamer_whitelist:
            return streams

        streams.update({stream_id: stream for stream_id, stream in all_streams.iteritems()
            if stream['streamer'].lower() in self.config.streamer_whitelist})

        return streams

    def apply_streamer_blacklist(self, streams):
        if not self.config.streamer_blacklist:
            return streams

        return {stream_id: stream for stream_id, stream in streams.iteritems()
            if stream['streamer'].lower() not in self.config.streamer_blacklist}

    def apply_keyword_whitelist(self, streams):
        if not self.config.keyword_whitelist:
            return streams
        
        whitelist = '|'.join(re.escape(term) for term in self.config.keyword_whitelist)
        whitelist_re = re.compile(whitelist, flags=re.IGNORECASE)

        return {stream_id: stream for stream_id, stream in streams.iteritems()
            if whitelist_re.search(stream['title'] or '')}

    def apply_keyword_blacklist(self, streams):
        if not self.config.keyword_blacklist:
            return streams
        
        blacklist = '|'.join(re.escape(term) for term in self.config.keyword_blacklist)
        blacklist_re = re.compile(blacklist, flags=re.IGNORECASE)

        return {stream_id: stream for stream_id, stream in streams.iteritems()
            if not blacklist_re.search(stream['title'] or '')}

    def filter_streams(self, all_streams):
        streams = self.apply_keyword_whitelist(all_streams)
        streams = self.apply_keyword_blacklist(streams)
        streams = self.apply_streamer_blacklist(streams)
        streams = self.apply_streamer_whitelist(streams, all_streams)
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
            announce_cutoff = time.time() - self.config.announce_limit
            for stream_id, stream in self.filter_streams(latest_streams).iteritems():
                if (stream_id not in self.streams 
                        and (
                            stream_id not in self.announcements
                            or self.announcements[stream_id] < announce_cutoff)):

                    on_new_broadcast(stream)
                self.announcements[stream_id] = time.time()
    
        self._streams = latest_streams

    def show_streams(self):
        # Sort streams by viewer count ascendingly
        streams = sorted(self.streams.iteritems(), key=lambda x: x[1].get('viewers', 0))

        if len(streams) > self.stream_spam_limit:
            streams = streams[-self.stream_spam_limit:]

        for stream_id, stream in streams:
            # Truncate the output to `display_cutoff` characters
            title = stream['title']
            output = "({}) {} | {}".format(
                stream['viewers'], stream['url'], title)
            if len(output) > self.config.display_cutoff:
                output = output[:self.config.display_cutoff-3] + "..."

            self.msg(output)
            time.sleep(0.2)

        if not self.streams:
            self.msg("Unfortunately there are no streams currently live.")

    def broadcast_live(self, stream):
        self.msg("NOW LIVE: ({}) {} | {}".format(
                stream['viewers'], stream['url'], stream['title']))

    def privmsg(self, to, message):
        self.irc_c.PRIVMSG(to, message)

    def msg(self, message):
        self.irc_c.PRIVMSG(self.channel, message)

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
