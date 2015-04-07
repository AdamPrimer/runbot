from __future__ import (absolute_import, print_function, division,
                        unicode_literals)
import yaml

from plugins.runbot.state import RunBotChannel
from plugins.runbot.modules import (
    RunBotModule,
    module_class,
    require_admin,
    require_super
)

@module_class
class AdminModule(RunBotModule):
    def __init__(self, runbot, irc_c, channel, config):
        super(AdminModule, self).__init__(runbot, irc_c, channel, config)
    
        self.register_command('rbjoin',        self.cmd_join_channel, channels=[self.channel])
        self.register_command('rbpart',        self.cmd_part_channel, channels=[self.channel])
        self.register_command('rbadd',         self.cmd_add_channel, channels=[self.channel])
        self.register_command('rbrm',          self.cmd_del_channel, channels=[self.channel])

        print("[RunBot] [{}] Admin Module loaded.".format(self.channel))

    @require_super
    def cmd_join_channel(self, irc_c, msg, trigger, args, kargs):
        channel = args[0]
        if channel not in self.runbot.config['channels']:
            prefix = irc_c.config['triggers']['prefix']
            msg.reply("Channel config not found. Please {}rbadd {} first.".format(prefix, channel))
            return
        
        self.runbot.join_channel(channel)
        irc_c.JOIN(channel)

    @require_super
    def cmd_part_channel(self, irc_c, msg, trigger, args, kargs):
        if args:
            channel = args[0]
        else:
            channel = msg.channel

        self.runbot.part_channel(channel)
        irc_c.PART(channel, "RunBot bids you adieu.")

    @require_super
    def cmd_add_channel(self, irc_c, msg, trigger, args, kargs):
        if not args:
            msg.reply('RunBot is currently in: {}'.format(
                    ", ".join(self.runbot.config['channels'].keys())))
            return

        channel = args[0]
        self.runbot.add_channel(channel)
        msg.reply("Added {} to the RunBot channel list".format(channel))

    @require_super
    def cmd_del_channel(self, irc_c, msg, trigger, args, kargs):
        channel = args[0]
        self.runbot.remove_channel(channel)
        msg.reply("Removed {} from the RunBot channel list".format(channel))
