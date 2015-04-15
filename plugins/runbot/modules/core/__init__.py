from __future__ import (absolute_import, print_function, division,
                        unicode_literals)
from plugins.runbot.modules import (
    RunBotModule,
    module_class,
    require_admin,
)

@module_class
class CoreModule(RunBotModule):
    def __init__(self, runbot, irc_c, channel, config):
        super(CoreModule, self).__init__(runbot, irc_c, channel, config)
    
        self.register_command('rb_commands', self.cmd_commands)
        self.register_command('rb_leave',    self.cmd_part_channel)
        self.register_command('rb_module',   self.cmd_add_module)
        self.register_command('rb_unmodule', self.cmd_del_module)

        print("[RunBot] [{}] Core Module loaded.".format(self.channel))

    @require_admin
    def cmd_part_channel(self, irc_c, msg, trigger, args, kargs):
        channel = msg.channel
        self.runbot.part_channel(channel)
        irc_c.PART(channel, "RunBot bids you adieu.")

    @require_admin
    def cmd_add_module(self, irc_c, msg, trigger, args, kargs):
        if not args:
            msg.reply("Currently loaded modules: {}".format(", ".join(self.config.modules)))
            return
        
        module = args[0]

        self.config.list_add('modules', module)
        self.config.save()

        channel = self.runbot.channels[msg.channel]
        channel.reload_modules()

        if module in channel.modules:
            msg.reply("Loaded the {} module.".format(module))
        else:
            msg.reply("Could not load the {} module.".format(module))
            try:
                self.config.list_rm('modules', module)
            except KeyError:
                pass
                    
            self.config.save()

    @require_admin
    def cmd_del_module(self, irc_c, msg, trigger, args, kargs):
        if not args:
            return
        
        if args[0] == "core":
            msg.reply("You may not remove the core module.")
            return

        module = args[0]

        try:
            self.config.list_rm('modules', module)
            self.config.save()
        except KeyError:
            msg.reply("The {} module is not loaded.".format(module))
            return

        channel = self.runbot.channels[msg.channel]
        channel.reload_modules()

        if module not in channel.modules:
            msg.reply("Removed the {} module.".format(module))
        else:
            msg.reply("Could not unload the {} module.".format(module))
        
    def cmd_commands(self, irc_c, msg, trigger, args, kargs):
        channel = self.runbot.channels[msg.channel]
        commands = []
        for module_name, module in channel.modules.iteritems():
            commands.extend(module.list_commands())

        prefix = irc_c.config['triggers']['prefix']
        commands = sorted(["{}{}".format(prefix, c) for c in commands])
        msg.reply("Commands: {}".format(", ".join(commands)))
