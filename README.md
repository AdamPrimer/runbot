## Installing ##

    pip install -r requirements.txt

## Running ##

    python ./runbot.py

## Configuring ##

See `runbot.conf`

Advanced users also see: `core.conf`

## Adding a new module ##

1. Create the directory `yourmodule` in `/plugins/runbot/modules/`
2. Create `__init__.py` in the directory.
3. Run the command `!rb_module your_module` in the channel to load the module

## New module template ##

    from __future__ import (absolute_import, print_function, division,
                            unicode_literals)
    from plugins.runbot.modules import (
        RunBotModule,
        module_class,
        require_admin
    )

    @module_class
    class YourModule(RunBotModule):
        def __init__(self, runbot, irc_c, channel, config):
            super(YourModule, self).__init__(runbot, irc_c, channel, config)
            
            self.register_command('your_command', self.cmd_your_command, channels=[self.channel])
            self.register_command('your_admin_command', self.cmd_your_admin_command, channels=[self.channel])

            print("[RunBot] [{}] Your Module loaded.".format(self.channel))

        def cmd_your_command(self, irc_c, msg, trigger, args, kargs):
            msg.reply("Your Command Here!")

        @require_admin
        def cmd_your_admin_command(self, irc_c, msg, trigger, args, kargs):
            if not args:
                msg.reply(self.config.your_config_variable))
                return

            value = " ".join(args)
            self.config.your_config_variable = value
            self.config.save()

## Adding a new streaming service ##

Create `yourservice.py` in `/plugins/runbot/modules/streams/services`
    a. See `/plugins/runbot/services/service.py` for the interface.
    b. See `/plugins/runbot/services/twitch.py` for an example.

## New streaming service template ##

    from __future__ import (absolute_import, print_function, division,
                            unicode_literals)
    from plugins.runbot.modules.streams.services import service_class
    from plugins.runbot.modules.streams.services.service import RunBotService

    @service_class
    class YourService(RunBotService):
        def __init__(self, games=[]):
            '''Instansiates a new service.

            Args:
                games: A list of games names to include in results.
            '''

            self.games = games
            self.keyword_whitelist = keyword_whitelist
            self.keyword_blacklist = keyword_blacklist

        def extract_stream_info(self, stream):
            '''Extracts title, viewer count, streamer name and url info from a
            stream dict.
            
            Args: 
                stream: A dict as output from get_all_streams()

            Returns:
                A dict with keys: title, viewers, streamer, url
            '''
            pass

        def get_all_streams(self):
            '''Gets the streams for all games.

            Returns:
                A list of dicts, where each dict is a stream as returned by the
                underlying API.
            '''
            pass

## TODO ##

- [streams] Allow blacklisting on a "timeout" so that bans wear off
  automatically after a specified period.
- [modules] Moderator/Admin hierarchy rather than all admins being equal
- [modules] Add ability for `!help <command>`
