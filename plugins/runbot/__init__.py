from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from plugins.runbot.state import RunBotState
from pyaib.plugins import keyword, plugin_class, every

@plugin_class
class RunBot(object):
    def __init__(self, irc_c, config):
        self.state = RunBotState(
            games=config['games'],
            keyword_whitelist=config['keyword_whitelist'],
            keyword_blacklist=config['keyword_blacklist'],
            announce_limit=config['announce_limit'],
            services=config['services'])

        self.display_cutoff = config['display_cutoff']
        self.update_interval = config['update_interval']

        # Save the IRC context
        self.irc_c = irc_c

        # Plugin is loaded before we are even live, so don't bother trying to
        # display anything on the detection of new broadcasts
        self.state.update_streams(on_new_broadcast=None)

        # Modify the @every decorator for the update_streams method, allows us
        # to configure this period via the config file.
        self.update_streams.__func__.__plugs__ = ('timers', 
            [('update_streams', self.update_interval)])

        print("RunBot Plugin Loaded!")

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
