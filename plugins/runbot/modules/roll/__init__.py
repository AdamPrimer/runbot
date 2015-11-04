from __future__ import (absolute_import, print_function, division,
                        unicode_literals)
import time
import parse
import random
import datetime
import requests

from plugins.runbot.modules import (
    RunBotModule,
    module_class,
    require_admin
)

@module_class
class RollModule(RunBotModule):
    def __init__(self, runbot, irc_c, channel, config):
        super(RollModule, self).__init__(runbot, irc_c, channel, config)

        self.patterns = [
            ("{:d}d{:d}d{:d}", ('num', 'size', 'drop')),
            ("{:d}d{:d}k{:d}", ('num', 'size', 'keep')),
            ("{:d}d{:d}", ('num', 'size')),
            ("d{:d}",     ('size', )),
        ]

        self.char_stats = [
            'STR', 'DEX', 'CON', 'INT', 'WIL', 'CHA', 'PER', 'HOT',
        ]

        self.register_command('roll',   self.cmd_roll)
        self.register_command('char',   self.cmd_char)

        print("[RunBot] [{}] Roll Module loaded.".format(self.channel))

    def cmd_roll(self, irc_c, msg, trigger, args, kargs):
        if not args:
            return

        cmd = args[0]
        name = args[1] if len(args) > 1 else cmd

        rolls, drops = self.do_roll(self.parse_roll(cmd))

        roll_list = map(str, rolls)
        if drops:
            roll_list.extend(["({})".format(x) for x in drops])

        response = "{} -> {}: {} [{}={}]".format(
            msg.sender, name, sum(rolls), cmd, ",".join(roll_list)
        )

        msg.reply(response)

    def cmd_char(self, irc_c, msg, trigger, args, kargs):
        rollstr = args[0] if args else "3d6"
        char = self.generate_character(self.char_stats, rollstr)

        res = "{} -> {}".format(
            msg.sender, ", ".join(["{}: {}".format(k, v) for k, v in char]))
        msg.reply(res)

    def generate_character(self, stats, rollstr="3d6"):
        '''Rolls 3d6 (or `rollstr`) for each `stat` in `stats`, returns a list
        of tuples, each a pair of (`stat`, `total roll`).'''

        rolls = [self.do_roll(self.parse_roll(rollstr)) for stat in stats]
        return zip(stats, map(sum, [x[0] for x in rolls]))

    def parse_roll(self, msg):
        for pat, fields in self.patterns:
            res = parse.parse(pat, msg)
            if not res:
                continue

            roll = dict(zip(fields, res))
            if 'num' not in roll:
                roll['num'] = 1
            return roll

    def do_roll(self, roll):
        rolls = []
        drops = []
        for i in xrange(0, roll.get('num', 1)):
            rolls.append(random.randrange(1, roll.get('size', 6)+1))

        if 'drop' in roll:
            rolls = sorted(rolls)
            drops = rolls[:roll['drop']]
            rolls = rolls[roll['drop']:]

        elif 'keep' in roll:
            rolls = sorted(rolls, reverse=True)
            drops = rolls[roll['keep']:]
            rolls = rolls[:roll['keep']]

        return (sorted(rolls, reverse=True), sorted(drops, reverse=True))
