from __future__ import (absolute_import, print_function, division,
                        unicode_literals)
from plugins.runbot.config import RunBotConfig
from plugins.runbot.modules import (
    available_modules,
    load_runbot_modules
)

class RunBotChannel:
    def __init__(self, runbot, irc_c, channel, config_file, config_folder=""):
        self.runbot = runbot
        self.irc_c = irc_c
        self.channel = channel
        self.config = RunBotConfig(config_file, config_folder)
        self.modules = {}

        load_runbot_modules(self.config.modules)
        for module in self.config.modules:
            if module in available_modules:
                self.modules[module] = available_modules[module](
                        runbot, irc_c, channel, self.config)
            else:
                print("[RunBot] [{}] Unable to load module: {}".format(
                    self.channel, module))

        print("[RunBot] [{}] Channel initialized.".format(self.channel))

    def reload_modules(self):
        print("[RunBot] [{}] Reloading modules.".format(self.channel))

        load_runbot_modules(self.config.modules)

        for module_name, module in list(self.modules.iteritems()):
            if module_name not in self.config.modules:
                module.unload()
                del self.modules[module_name]

        for name in self.config.modules:
            if name not in self.modules:
                if name in available_modules:
                    self.modules[name] = available_modules[name](
                            self.runbot, self.irc_c, self.channel, self.config)
                else:
                    print("[RunBot] [{}] Unable to load module: {}".format(
                        self.channel, module))

        print("[RunBot] [{}] Modules reloaded.".format(self.channel))
