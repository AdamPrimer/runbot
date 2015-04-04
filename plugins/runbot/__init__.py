from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from plugins.runbot.state import RunBotState
from pyaib.plugins import keyword, plugin_class, every, observe

import yaml
import time
import functools 
from parse import parse
from collections import defaultdict

@plugin_class
class RunBot:
    def __init__(self, irc_c, config):
        self.states = {}

        with open(config['config'], 'r') as fp:
            self.config = yaml.safe_load(fp)

        # Initialize all the channels
        for channel, config in self.config['channels'].iteritems():
            self.states[channel] = RunBotState(irc_c, channel, config, config_folder=self.config['folder'])
        
        # Save the IRC context
        self.irc_c = irc_c

        self.registered_users = {}

        # Modify the @every decorator for the update_streams method, allows us
        # to configure this period via the config file.
        self.cron_update_streams.__func__.__plugs__ = ('timers', 
            [('update_streams', self.config['update_interval'])])

        print("RunBot Plugin Loaded!")

    def require_admin(wrapped):
        @functools.wraps(wrapped)
        def _wrapper(self, irc_c, msg, trigger, args, kwargs):
            channel = self.states[msg.channel]

            if (msg.sender.lower() not in channel.config.admin_users):
                msg.reply("Sorry, {} cannot perform that command.".format(msg.sender))
                return
                
            login_cutoff = time.time() - self.config['login_timeout']
            if (msg.sender not in self.registered_users 
                    or self.registered_users[msg.sender] < login_cutoff):
                msg.reply("Please !login")
                return

            return wrapped(self, irc_c, msg, trigger, args, kwargs)
        return _wrapper

    @require_admin
    @keyword('keyword')
    def whitelist_keyword(self, irc_c, msg, trigger, args, kargs):
        channel = self.states[msg.channel]

        if not args:
            msg.reply("Current Keywords: {}".format(
                ", ".join(channel.config.keyword_whitelist)))
            return
            
        channel.whitelist_keyword(args)
        msg.reply("Added {} to the keyword list.".format(" ".join(args)))

    @require_admin
    @keyword('banword')
    def unwhitelist_keyword(self, irc_c, msg, trigger, args, kargs):
        channel = self.states[msg.channel]
        channel.unwhitelist_keyword(args)
        msg.reply("Removed {} from the keyword list.".format(" ".join(args)))

    @require_admin
    @keyword('whitelist')
    def whitelist_streamer(self, irc_c, msg, trigger, args, kargs):
        channel = self.states[msg.channel]

        if not args:
            msg.reply("Current Whitelist: {}".format(
                ", ".join(channel.config.streamer_whitelist)))
            return
            
        channel.whitelist_streamer(args)
        msg.reply("Added {} to the whitelist.".format(" & ".join(args)))

    @require_admin
    @keyword('unwhitelist')
    def unwhitelist_streamer(self, irc_c, msg, trigger, args, kargs):
        channel = self.states[msg.channel]
        channel.unwhitelist_streamer(args)
        msg.reply("Removed {} from the whitelist.".format(" & ".join(args)))

    @require_admin
    @keyword('blacklist')
    def blacklist_streamer(self, irc_c, msg, trigger, args, kargs):
        channel = self.states[msg.channel]

        if not args:
            msg.reply("Current Blacklist: {}".format(
                ", ".join(channel.config.streamer_blacklist)))
            return
            
        channel.blacklist_streamer(args)
        msg.reply("Added {} to the blacklist.".format(" & ".join(args)))

    @require_admin
    @keyword('unblacklist')
    def unblacklist_streamer(self, irc_c, msg, trigger, args, kargs):
        channel = self.states[msg.channel]
        channel.unblacklist_streamer(args)
        msg.reply("Removed {} from the blacklist.".format(" & ".join(args)))

    @keyword('login')
    def register(self, irc_c, msg, trigger, args, kargs):
        login_cutoff = time.time() - self.config['login_timeout']
        if (msg.sender not in self.registered_users 
                or self.registered_users[msg.sender] < login_cutoff):
            irc_c.RAW('WHOIS {}'.format(msg.sender))
        else:
            msg.reply("Already logged in to the bot.")

    @keyword('streams')
    def streams(self, irc_c, msg, trigger, args, kargs):
        channel = self.states[msg.channel]
        channel.show_streams()

    @observe('IRC_RAW_MSG')
    def parse_whois(self, irc_c, msg):
        login = parse(":{server} {} {} {nick} :is identified for this nick", msg)
        if login:
            data = login.named
            self.registered_users[data['nick']] = time.time()

    @observe('IRC_ONCONNECT')
    def on_connect(self, irc_c):
        for channel in self.states.keys():
            irc_c.JOIN(channel)

    @every(60, "update_streams")
    def cron_update_streams(self, irc_c, name):
        for channel in self.states.values():
            channel.update_streams(on_new_broadcast=channel.broadcast_live)
