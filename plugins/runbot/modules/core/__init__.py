from __future__ import (absolute_import, print_function, division,
                        unicode_literals)
from plugins.runbot.modules import (
    RunBotModule,
    module_class,
    require_admin,
    case_insensitive_in
)

@module_class
class CoreModule(RunBotModule):
    def __init__(self, runbot, irc_c, channel, config):
        super(CoreModule, self).__init__(runbot, irc_c, channel, config)
    
        self.register_command('rb_commands', self.cmd_commands)
        self.register_command('rb_leave',    self.cmd_part_channel)
        self.register_command('rb_module',   self.cmd_add_module)
        self.register_command('rb_unmodule', self.cmd_del_module)
        self.register_command('rb_admin',    self.cmd_add_admin)
        self.register_command('rb_admin_users',   self.cmd_add_admin)
        self.register_command('rb_unadmin',  self.cmd_del_admin)

        print("[RunBot] [{}] Core Module loaded.".format(self.channel))

    @require_admin
    def cmd_part_channel(self, irc_c, msg, trigger, args, kargs):
        channel = msg.channel
        self.runbot.part_channel(channel)
        irc_c.PART(channel, "RunBot bids you adieu.")

    @require_admin
    def cmd_add_admin(self, irc_c, msg, trigger, args, kargs):
        if not args:
            admin_users = []
            if self.config.admin_users:
                admin_users = ["{} ({})".format(admin, level) 
                        for admin, level in self.config.admin_users]
            msg.reply("Current administrators: {}".format(", ".join(admin_users)))
            return

        if len(args) != 2:
            msg.reply("Incorrect arguments. Usage: !rb_admin nick <level>")
            return
            
        try:
            admin = args[0]
            level = int(args[1])
            if level < 1:
                raise ValueError("Administrators must be at least level 1")
            if level > 9000:
                raise ValueError("Administrators cannot go above level 9000")
        except ValueError as e:
            msg.reply("Invalid level (Range: 0-9000). Usage: !rb_admin nick <level>")
            return

        sender = msg.sender
        if not case_insensitive_in(sender, self.runbot.superadmins):
            level1 = self.config.admin_users[sender][1]
            if level > level1: 
                msg.reply("Sorry, you can only make administrators of level {} or lower.".format(
                    level1
                ))
                return

        self.config.list_add('admin_users', (admin, level))
        self.config.save()

        msg.reply("The user {} was added to the list of administrators at level {}".format(
            admin, level
        ))

    @require_admin
    def cmd_del_admin(self, irc_c, msg, trigger, args, kargs):
        if not args:
            return
        
        sender = msg.sender
        nick = args[0]
        if nick not in self.config.admin_users:
            msg.reply("Sorry, {} is not an administrator.".format(nick))
            return

        if not case_insensitive_in(sender, self.runbot.superadmins):
            level1 = self.config.admin_users[sender][1]
            level2 = self.config.admin_users[nick][1]
            if level1 <= level2: 
                msg.reply("Sorry, only admininistrators of level {} or greater may remove {}. You are level {}.".format(
                    level2 + 1, nick, level1
                ))
                return

        try:
            self.config.list_rm('admin_users', nick)
        except KeyError:
            msg.reply("Was unable to remove {} from the administrators list.".format(nick))
            return

        self.config.save()
    
        msg.reply("The user {} was removed from the administrators list.".format(nick))

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
