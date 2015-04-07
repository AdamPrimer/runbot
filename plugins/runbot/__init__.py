from __future__ import (absolute_import, print_function, division,
                        unicode_literals)
import time
import yaml
from parse import parse
from collections import defaultdict

from plugins.runbot.channel import RunBotChannel
from pyaib.plugins import (
    plugin_class,
    observe
)

@plugin_class
class RunBot:
    def __init__(self, irc_c, config):
        self.channels = {}

        self.irc_c = irc_c
        self.config_file = config['config']

        with open(config['config'], 'r') as fp:
            self.config = yaml.safe_load(fp)

        self.superadmins = self.config.get('superadmins', [])
        
        self.registered_users = {}
        self._whois_event_stack = defaultdict(list)

        # Initialize all the channels
        for channel, config in self.config['channels'].iteritems():
            self.channels[channel] = RunBotChannel(self, self.irc_c, channel, 
                    config,
                    config_folder=self.config['folder'])

        print("[RunBot] All channels loaded.")
        
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
        for channel in self.channels.keys():
            irc_c.JOIN(channel)

    def join_channel(self, channel):
        if channel in self.channels:
            return False

        self.channels[channel] = RunBotChannel(self, self.irc_c, channel, 
                self.config['channels'][channel],
                config_folder=self.config['folder'])

    def part_channel(self, channel):
        if channel not in self.channels:
            return False
        
        del self.channels[channel]

    def add_channel(self, channel):
        if channel in self.config['channels']:
            return False

        self.config['channels'][channel] = "runbot_{}.conf".format(channel[1:])
        self.save()

    def remove_channel(self, channel):
        if channel not in self.config['channels']:
            return False

        del self.config['channels'][channel]
        self.save()

    def save(self):
        with open(self.config_file, 'w+') as fp:
            yaml.safe_dump(self.config, fp)
