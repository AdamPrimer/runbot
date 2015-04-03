from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from plugins.runbot.state import RunBotState
from pyaib.plugins import keyword, plugin_class, every, observe

import time
from parse import parse
from collections import defaultdict
import functools 

@plugin_class
class RunBot(object):
    def __init__(self, irc_c, config):
        self.state = RunBotState(
            games=config['games'],
            keyword_whitelist=config['keyword_whitelist'],
            keyword_blacklist=config['keyword_blacklist'],
            announce_limit=config['announce_limit'],
            services=config['services'],
            streamer_blacklist_file=config['streamer_blacklist_file'])

        self.display_cutoff = config['display_cutoff']
        self.update_interval = config['update_interval']
        self.login_timeout = config['login_timeout']
        self.admin_users = config['admin_users']
        
        # Save the IRC context
        self.irc_c = irc_c

        # Plugin is loaded before we are even live, so don't bother trying to
        # display anything on the detection of new broadcasts
        self.state.update_streams(on_new_broadcast=None)

        # Modify the @every decorator for the update_streams method, allows us
        # to configure this period via the config file.
        self.update_streams.__func__.__plugs__ = ('timers', 
            [('update_streams', self.update_interval)])

        self.registered_users = {}

        print("RunBot Plugin Loaded!")

    @observe('IRC_RAW_MSG')
    def parse_whois(self, irc_c, msg):
        login = parse(":{server} {} {} {nick} :is identified for this nick", msg)
        if login:
            data = login.named
            self.registered_users[data['nick']] = time.time()

    def require_admin(wrapped):
        @functools.wraps(wrapped)
        def _wrapper(self, irc_c, msg, trigger, args, kwargs):
            if (msg.sender.lower() not in self.admin_users):
                msg.reply("Sorry, {} is cannot perform that command.".format(msg.sender))
                return
                
            login_cutoff = time.time() - self.login_timeout
            if (msg.sender not in self.registered_users 
                    or self.registered_users[msg.sender] < login_cutoff):
                msg.reply("Please !login")
                return

            return wrapped(self, irc_c, msg, trigger, args, kwargs)
        return _wrapper 

    @require_admin
    @keyword('blacklist')
    def add_blacklist(self, irc_c, msg, trigger, args, kargs):
        if not args:
            msg.reply("Current Blacklist: {}".format(
                ", ".join(self.state.streamer_blacklist)))
            return
            
        for streamer in [arg.lower() for arg in args]:
            if streamer not in self.state.streamer_blacklist:
                self.state.streamer_blacklist.append(streamer)
        self.state.save_streamer_blacklist()
        msg.reply("Added {} to the blacklist.".format(" & ".join(args)))

    @require_admin
    @keyword('unblacklist')
    def del_blacklist(self, irc_c, msg, trigger, args, kargs):
        for streamer in [arg.lower() for arg in args]:
            if streamer in self.state.streamer_blacklist:
                self.state.streamer_blacklist.remove(streamer)
        self.state.save_streamer_blacklist()
        msg.reply("Removed {} from the blacklist.".format(" & ".join(args)))

    @keyword('login')
    def register(self, irc_c, msg, trigger, args, kargs):
        login_cutoff = time.time() - self.login_timeout
        if (msg.sender not in self.registered_users 
                or self.registered_users[msg.sender] < login_cutoff):
            irc_c.RAW('WHOIS {}'.format(msg.sender))
        else:
            msg.reply("Already logged in to the bot.")

    @keyword('streams')
    def streams(self, irc_c, msg, trigger, args, kargs):
        # Sort streams by viewer count ascendingly
        streams = sorted(self.state.streams.iteritems(), key=lambda x: x[1].get('viewers', 0))

        for stream_id, stream in streams:
            # Truncate the output to `display_cutoff` characters
            title = stream['title']
            output = "({}) {} | {}".format(
                stream['viewers'], stream['url'], title)
            if len(output) > self.display_cutoff:
                output = output[:self.display_cutoff-3] + "..."

            msg.reply(output)

        if not self.state.streams:
            msg.reply("Unfortunately there are no streams currently live.")

    def broadcast_live(self, stream):
        for channel in self.irc_c.channels.channels:
            self.irc_c.PRIVMSG(channel, "NOW LIVE: ({}) {} | {}".format(
                stream['viewers'], stream['url'], stream['title']))

    @every(60, "update_streams")
    def update_streams(self, irc_c, name):
        self.state.update_streams(on_new_broadcast=self.broadcast_live)
