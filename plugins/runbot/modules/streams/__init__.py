from __future__ import (absolute_import, print_function, division,
                        unicode_literals)
import re
import time
import datetime

from plugins.runbot.modules import (
    RunBotModule,
    module_class,
    require_admin,
    require_super,
    case_insensitive_in
)
from plugins.runbot.modules.streams.services import (
    load_services,
    available_services
)

add_list_keywords = {
    'game':  ('games', 'games list'),
    'games':  ('games', 'games list'),
    'banword': ('keyword_blacklist', 'banned words list'),
    'banwords': ('keyword_blacklist', 'banned words list'),
    'keyword': ('keyword_whitelist', 'keywords list'),
    'keywords': ('keyword_whitelist', 'keywords list'),
    'whitelist': ('streamer_whitelist', 'whitelist'),
    'blacklist': ('streamer_blacklist', 'blacklist'),
}

del_list_keywords = {
    'ungame':   ('games', 'games list'),
    'unbanword': ('keyword_blacklist', 'banned words list'),
    'unkeyword': ('keyword_whitelist', 'keywords list'),
    'unwhitelist': ('streamer_whitelist', 'whitelist'),
    'unblacklist': ('streamer_blacklist', 'blacklist'),
}

@module_class
class StreamsModule(RunBotModule):
    def __init__(self, runbot, irc_c, channel, config):
        super(StreamsModule, self).__init__(runbot, irc_c, channel, config)
    
        self.default_config = {
            'announce_limit': 1800,
            'display_cutoff': 80,
            'games': [],
            'keyword_blacklist': [],
            'keyword_whitelist': [],
            'services': [
                'twitch'
            ],
            'streamer_blacklist': [],
            'streamer_whitelist': []
        }

        for key, val in self.default_config.iteritems():
            if self.config.__getattr__(key) == None:
                self.config.__setattr__(key, val)

        load_services(self.config.services)

        self.services = {}
        for service in self.config.services:
            self.services[service] = available_services[service](self.config.games)
        
        self._streams = {}
        self.announcements = {}

        self.stream_spam_limit = 8
        
        self.update_streams(on_new_broadcast=None)

        self.register_command('update_streams', self.cmd_update_streams)
        self.register_command('streams',        self.cmd_streams)
        self.register_command('rb_service',     self.cmd_add_service)
        self.register_command('rb_unservice',   self.cmd_del_service)
        self.register_command('hide',           self.cmd_hide_streamer)

        for keyword in add_list_keywords.keys():
            self.register_command(keyword, self.cmd_add_item_to_list)

        for keyword in del_list_keywords.keys():
            self.register_command(keyword, self.cmd_del_item_from_list)

        self.register_cron('update_streams', self.cron_update_streams, self.runbot.config['update_interval'])

        print("[RunBot] [{}] Streams Module loaded.".format(self.channel))

    @require_admin
    def cmd_hide_streamer(self, irc_c, msg, trigger, args, kargs):
        if not args:
            hidden = []
            if self.config.hidden_streamers:
                for streamer, ts in self.config.hidden_streamers:
                    seconds = int(ts)-int(time.time())
                    if seconds > 0:
                        hidden.append("{} ({})".format(
                        streamer, str(datetime.timedelta(seconds=seconds))))
   
            hidden = ", ".join(hidden)
            msg.reply("Currently hidden streamers: {}".format(hidden))
            return

        if len(args) < 2:
            msg.reply("Insufficient arguments. Usage: !hide username 3600")
            return

        try:
            streamer = args[0]
            length = int(args[1])
            if length < 0:
                raise ValueError("You must hide for at least 0 minutes")
            if length > 43200:
                raise ValueError("Cannot hide for more than 30 days")
        except ValueError as e:
            msg.reply("Invalid time. Usage: !hide username 30")
            return

        self.config.list_add('hidden_streamers',
                (streamer, str(int(time.time()) + (length * 60))))
        self.config.save()

        msg.reply("Streamer {} has been hidden for {} minutes.".format(
                streamer, length))

    @require_admin
    def cmd_add_service(self, irc_c, msg, trigger, args, kargs):
        if not args:
            msg.reply("Currently loaded services: {}".format(", ".join(self.config.services)))
            return

        service = args[0]

        if service in self.services:
            msg.reply("Service {} is already loaded.".format(service))
            return

        self.config.list_add('services', service)

        load_services(self.config.services)

        if service not in available_services:
            msg.reply("Service {} is not available to be loaded.".format(service))
            return

        self.services[service] = available_services[service](self.config.games)
        self.config.save()

        self.update_streams(on_new_broadcast=None)

        msg.reply("Loaded the {} service.".format(service))

    @require_admin
    def cmd_del_service(self, irc_c, msg, trigger, args, kargs):
        if not args:
            return

        service = args[0]

        if service not in self.services:
            msg.reply("Service {} not currently loaded.".format(service))
            return

        del self.services[service]

        try:
            self.config.list_rm('services', service)
            self.config.save()

            self.update_streams(on_new_broadcast=None)

            msg.reply("Removed the {} service.".format(service))
        except KeyError as e:
            msg.reply("The {} service is not loaded.".format(service))

    @require_admin
    def cmd_add_item_to_list(self, irc_c, msg, trigger, args, kargs):
        (variable, text) = add_list_keywords[trigger]
        if not args:
            items = self.config.__getattr__(variable)
            if items:
                msg.reply("Current {}: {}".format(text, ", ".join(items)))
            else:
                msg.reply("There is currently no {}".format(text))
            return
            
        if variable in ['keyword_whitelist', 'keyword_blacklist', 'games']:
            args = " ".join(args)
        else:
            args = args[0]

        if self.add_to_list(variable, args):
            msg.reply("Added {} to the {}.".format(args, text))
            if variable in ["games"]:
                self.update_streams(on_new_broadcast=None)
        else:
            msg.reply("Failed to add {} to the {}.".format(args, text))

    @require_admin
    def cmd_del_item_from_list(self, irc_c, msg, trigger, args, kargs):
        (variable, text) = del_list_keywords[trigger]
        if variable in ['keyword_whitelist', 'keyword_blacklist', 'games']:
            args = " ".join(args)
        else:
            args = args[0]

        if self.del_from_list(variable, args):
            msg.reply("Removed {} from the {}.".format(args, text))
        else:
            msg.reply("Failed to remove {} from the {}.".format(args, text))
    
    @require_admin
    def cmd_update_streams(self, irc_c, msg, trigger, args, kargs):
        self.update_streams(on_new_broadcast=self.broadcast_live)

    def cmd_streams(self, irc_c, msg, trigger, args, kargs):
        self.show_streams()

    def cron_update_streams(self, irc_c, name):
        self.update_streams(on_new_broadcast=self.broadcast_live)

    @property
    def streams(self):
        return self.filter_streams(self._streams)

    def add_to_list(self, variable, keyword):
        self.config.list_add(variable, keyword)
        self.config.save()
        return True

    def del_from_list(self, variable, keyword):
        try:
            if variable in ['admin_users']:
                for user in keyword:
                    if case_insensitive_in(user, self.runbot.superadmins):
                        return False
                self.config.list_rm(variable, keyword)
            else:
                self.config.list_rm(variable, keyword)
        except KeyError:
            return False
        
        self.config.save()
        return True

    def apply_streamer_hidelist(self, streams):
        if not self.config.hidden_streamers:
            return streams

        for (streamer, ts) in list(self.config.hidden_streamers):
            if int(ts) < time.time():
                try:
                    self.config.list_rm('hidden_streamers', (streamer, ts))
                except KeyError:
                    pass

        self.config.save()

        if not self.config.hidden_streamers:
            return streams

        return {stream_id: stream for stream_id, stream in streams.iteritems()
            if not stream['streamer'] in self.config.hidden_streamers}

    def apply_streamer_whitelist(self, streams, all_streams):
        if not self.config.streamer_whitelist:
            return streams

        streams.update({stream_id: stream for stream_id, stream in all_streams.iteritems()
            if stream['streamer'] in self.config.streamer_whitelist})

        return streams

    def apply_streamer_blacklist(self, streams):
        if not self.config.streamer_blacklist:
            return streams

        return {stream_id: stream for stream_id, stream in streams.iteritems()
            if not stream['streamer'] in self.config.streamer_blacklist}

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
        streams = self.apply_streamer_hidelist(streams)
        streams = self.apply_streamer_whitelist(streams, all_streams)
        return streams

    def update_streams(self, on_new_broadcast):
        print("[RunBot] [{}] [streams] Checking For Streams...".format(self.channel))
        latest_streams = {}
            
        for name, service in self.services.iteritems():
            try:
                streams = [service.extract_stream_info(stream)
                    for stream in service.get_all_streams()]
                latest_streams = {"{}_{}".format(name, stream['streamer']): stream
                    for stream in streams}
            except Exception as e:
                print(e)
                pass

        if on_new_broadcast:
            announcement_counter = 0
            announce_cutoff = time.time() - self.config.announce_limit
            for stream_id, stream in self.filter_streams(latest_streams).iteritems():
                if (stream_id not in self.streams 
                        and (
                            stream_id not in self.announcements
                            or self.announcements[stream_id] < announce_cutoff)):

                    # Avoid spamming announcements if a source has issues and
                    # releases a bunch of streams as online at once
                    if announcement_counter < 8:
                        on_new_broadcast(stream)
                    announcement_counter += 1

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
        self.msg("NOW LIVE: {} | {}".format(
                stream['url'], stream['title']))
        time.sleep(0.2)
