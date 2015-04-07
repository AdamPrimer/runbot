from __future__ import (absolute_import, print_function, division,
                        unicode_literals)
import time
import datetime
import requests

from plugins.runbot.modules import (
    RunBotModule,
    module_class,
    require_admin
)

@module_class
class RecordsModule(RunBotModule):
    def __init__(self, runbot, irc_c, channel, config):
        super(RecordsModule, self).__init__(runbot, irc_c, channel, config)
        
        self.endpoints = {
            'records': 'http://www.speedrun.com/api_records.php'
        }

        self.register_command('wr',    self.cmd_world_record, channels=[self.channel])
        self.register_command('wrgame', self.cmd_set_wr_game, channels=[self.channel])

        print("[RunBot] [{}] Records Module loaded.".format(self.channel))

    @require_admin
    def cmd_set_wr_game(self, irc_c, msg, trigger, args, kargs):
        if not args:
            msg.reply("Current World Record Game: {}".format(
                    self.config.wr_game))
            return

        game = " ".join(args)
        self.config.wr_game = game
        self.config.save()

        msg.reply("World Record Game set to be: {}".format(
                    self.config.wr_game))

    def cmd_world_record(self, irc_c, msg, trigger, args, kargs):
        if kargs and 'game' in kargs:
            game = kargs['game']
        else:
            game = self.config.wr_game or None

        if not game:
            prefix = irc_c.config['triggers']['prefix']
            msg.reply("No default game set. Please use {}wr -game=GAMENAME".format(
                    prefix))
            return

        cate = " ".join(args)

        records = []
        data = self.get_record_times(game)
        if not data:
            msg.reply("Unable to obtain world records for: {}".format(game))
            return
        
        for game, categories in data.iteritems():
            for category, record in categories.iteritems():
                if not cate or category.lower() == cate.lower():
                    records.append("{}: {} ({}) {}".format(
                        category, 
                        self.format_seconds(int(record['time'])), 
                        record['player'],
                        self.format_timestamp(int(record['date']))
                    ))
        
            if len(records) > 8:
                msg.reply("Too many categories to display all: {}".format(
                    ", ".join(categories)))

            for record in records[:8]:
                msg.reply(record)
                time.sleep(0.2)

    def format_timestamp(self, timestamp):
        return datetime.datetime.strftime(
                datetime.datetime.utcfromtimestamp(timestamp),
                '%Y-%m-%d')

    def format_seconds(self, seconds):
        return str(datetime.timedelta(seconds=seconds))

    def get_record_times(self, game):
        params = {
            'game': game,
            'timing': 'rta'
        }
        req = requests.get(self.endpoints['records'], params=params)
        if req.status_code != 200:
            return None
        
        data = req.json()
        if not data:
            return None

        return data
