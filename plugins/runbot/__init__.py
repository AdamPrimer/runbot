from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from plugins.runbot.state import RunBotState
from pyaib.plugins import keyword, plugin_class, every, observe

import yaml
import time
import functools 
from parse import parse
from collections import defaultdict

add_list_keywords = {
    'admin': ('admin_users', 'administrators'),
    'game':  ('games', 'games list'),
    'banword': ('keyword_blacklist', 'banned words list'),
    'keyword': ('keyword_whitelist', 'keywords list'),
    'whitelist': ('streamer_whitelist', 'whitelist'),
    'blacklist': ('streamer_blacklist', 'blacklist'),
}

del_list_keywords = {
    'unadmin': ('admin_users', 'administrators'),
    'ungame':   ('games', 'games list'),
    'unbanword': ('keyword_blacklist', 'banned words list'),
    'unkeyword': ('keyword_whitelist', 'keywords list'),
    'unwhitelist': ('streamer_whitelist', 'whitelist'),
    'unblacklist': ('streamer_blacklist', 'blacklist'),
}

@plugin_class
class RunBot:
    def __init__(self, irc_c, config):
        self.states = {}

        self.config_file = config['config']

        with open(config['config'], 'r') as fp:
            self.config = yaml.safe_load(fp)

        self.superadmins = [sa.lower()
            for sa in self.config.get('superadmins', [])]

        # Initialize all the channels
        for channel, config in self.config['channels'].iteritems():
            self.states[channel] = RunBotState(irc_c, channel, 
                    config,
                    superadmins=self.superadmins,
                    config_folder=self.config['folder'])
        
        # Save the IRC context
        self.irc_c = irc_c

        self.registered_users = {}

        # Modify the @every decorator for the update_streams method, allows us
        # to configure this period via the config file.
        self.cron_update_streams.__func__.__plugs__ = ('timers', 
            [('update_streams', self.config['update_interval'])])

        self._whois_event_stack = defaultdict(list)

        print("RunBot Plugin Loaded!")

    def require_admin(wrapped):
        @functools.wraps(wrapped)
        def _wrapper(self, irc_c, msg, trigger, args, kwargs):
            channel = self.states[msg.channel]

            if (msg.sender.lower() not in channel.config.admin_users
                    and msg.sender.lower() not in self.superadmins):
                msg.reply("Sorry, {} cannot perform that command.".format(msg.sender))
                return
                
            login_cutoff = time.time() - self.config['login_timeout']
            if (msg.sender not in self.registered_users 
                    or self.registered_users[msg.sender] < login_cutoff):
                irc_c.RAW('WHOIS {}'.format(msg.sender))
                self._whois_event_stack[msg.sender].append(
                    functools.partial(wrapped, self, irc_c, msg, trigger, args, kwargs)
                )
                return

            return wrapped(self, irc_c, msg, trigger, args, kwargs)
        return _wrapper

    def require_super(wrapped):
        @functools.wraps(wrapped)
        def _wrapper(self, irc_c, msg, trigger, args, kwargs):
            channel = self.states[msg.channel]

            if (msg.sender.lower() not in self.superadmins):
                msg.reply("Sorry, {} cannot perform that command.".format(msg.sender))
                return
                
            login_cutoff = time.time() - self.config['login_timeout']
            if (msg.sender not in self.registered_users 
                    or self.registered_users[msg.sender] < login_cutoff):
                irc_c.RAW('WHOIS {}'.format(msg.sender))
                self._whois_event_stack[msg.sender].append(
                    functools.partial(wrapped, self, irc_c, msg, trigger, args, kwargs)
                )
                return

            return wrapped(self, irc_c, msg, trigger, args, kwargs)
        return _wrapper

    @require_admin
    @keyword(*add_list_keywords.keys())
    def _add_to_list(self, irc_c, msg, trigger, args, kargs):
        (variable, text) = add_list_keywords[trigger]
        channel = self.states[msg.channel]

        if not args:
            msg.reply("Current {}: {}".format(text,
                ", ".join(channel.config.__getattr__(variable))))
            return
            
        if channel.add_to_list(variable, args):
            msg.reply("Added {} to the {}.".format(" ".join(args), text))
            if trigger in ["game"]:
                channel.update_streams(on_new_broadcast=None)
        else:
            msg.reply("Failed to add {} to the {}.".format(" ".join(args), text))

    @require_admin
    @keyword(*del_list_keywords.keys())
    def _del_from_list(self, irc_c, msg, trigger, args, kargs):
        (variable, text) = del_list_keywords[trigger]

        channel = self.states[msg.channel]
        if channel.del_from_list(variable, args):
            if trigger in ['unwhitelist', 'unblacklist']:
                msg.reply("Removed {} from the {}.".format(" & ".join(args), text))
            else:
                msg.reply("Removed {} from the {}.".format(" ".join(args), text))
        else:
            msg.reply("Failed to remove {} from the {}.".format(" ".join(args), text))

    @require_admin
    @keyword('updatestreams')
    def updatestreams(self, irc_c, msg, trigger, args, kargs):
        channel = self.states[msg.channel]
        channel.update_streams(on_new_broadcast=channel.broadcast_live)

    @require_super
    @keyword('channel_join')
    def join_channel(self, irc_c, msg, trigger, args, kargs):
        channel = args[0]
        if channel not in self.config['channels']:
            msg.reply("Please !channel_add {} first.".format(channel))
            return
        
        self.states[channel] = RunBotState(irc_c, channel, 
                config_file=self.config['channels'][channel],
                superadmins=self.superadmins,
                config_folder=self.config['folder'])
        irc_c.JOIN(channel)

    @require_admin
    @keyword('channel_part')
    def part_channel(self, irc_c, msg, trigger, args, kargs):
        channel = msg.channel
        del self.states[channel]
        irc_c.PART(channel, "RunBot bids you adieu.")

    @require_super
    @keyword('channel_add')
    def add_channel(self, irc_c, msg, trigger, args, kargs):
        if not args:
            msg.reply('RunBot is currently in: {}'.format(
                    ", ".join(self.config['channels'].keys())))
            return

        channel = args[0]
        if channel not in self.config['channels']:
            self.config['channels'][channel] = "runbot_{}.conf".format(channel[1:])

        with open(self.config_file, 'w+') as fp:
            yaml.safe_dump(self.config, fp)

        msg.reply("Added {} to the RunBot channel list".format(channel))

    @require_super
    @keyword('channel_delete')
    def del_channel(self, irc_c, msg, trigger, args, kargs):
        channel = args[0]
        if channel in self.config['channels']:
            del self.config['channels'][channel]

        with open(self.config_file, 'w+') as fp:
            yaml.safe_dump(self.config, fp)

        msg.reply("Removed {} from the RunBot channel list".format(channel))

    @keyword('streams')
    def streams(self, irc_c, msg, trigger, args, kargs):
        channel = self.states[msg.channel]
        channel.show_streams()

    @observe('IRC_RAW_MSG')
    def parse_whois(self, irc_c, msg):
        login = parse(":{server} {} {} {nick} :is identified for this nick", msg)
        if login:
            data = login.named
            while self._whois_event_stack[data['nick']]:
                func = self._whois_event_stack[data['nick']].pop(0)
                func()
            self.registered_users[data['nick']] = time.time()

    @observe('IRC_ONCONNECT')
    def on_connect(self, irc_c):
        for channel in self.states.keys():
            irc_c.JOIN(channel)

    @every(60, "update_streams")
    def cron_update_streams(self, irc_c, name):
        for channel in self.states.values():
            channel.update_streams(on_new_broadcast=channel.broadcast_live)
