from __future__ import (absolute_import, print_function, division,
                        unicode_literals)
import os
import time
import inspect
import functools
from importlib import import_module
from pyaib.components import (
    ComponentManager,
    triggers_on,
    every
)

available_modules = {}

CLASS_MARKER = '_RUNBOT_MODULE'

def module_class(cls):
    if inspect.isclass(cls):
        setattr(cls, CLASS_MARKER, True)
        return cls

def load_runbot_modules(modules):
    for module in modules:
        _, dirs, _ = os.walk("plugins/runbot/modules").next()
        if module not in dirs:
            return
        
        importname = "{}.{}".format("plugins.runbot.modules", module)
        try:
            component_ns = import_module(importname)
        except ImportError as e:
            raise ImportError('runbot failed to load module (%s): %r' % (importname, e))
        
        for name, member in inspect.getmembers(component_ns):
            if inspect.isclass(member) and hasattr(member, CLASS_MARKER):
                available_modules[module] = member
                break

def case_insensitive_in(item, container):
    if isinstance(container, dict):
        container = container.keys()
        
    try:
        s = item.lower()
        idx = [c.lower() for c in container].index(s)
    except ValueError as e:
        return False
    return container[idx]

def require_admin(wrapped):
    @functools.wraps(wrapped)
    def _wrapper(self, irc_c, msg, trigger, args, kwargs):
        # Only require admin to perform actions, not to simply list things
        if args:
            if (not case_insensitive_in(msg.sender, self.config.admin_users)
                    and not case_insensitive_in(msg.sender, self.runbot.superadmins)):
                msg.reply("Sorry, {} cannot perform that command.".format(msg.sender))
                return
                
            login_cutoff = time.time() - self.runbot.config['login_timeout']
            matched_name = case_insensitive_in(msg.sender, self.runbot.registered_users)
            if (not matched_name
                    or self.runbot.registered_users[matched_name] < login_cutoff):
                irc_c.RAW('WHOIS {}'.format(msg.sender))
                self.runbot._whois_event_stack[msg.sender].append(
                    functools.partial(wrapped, self, irc_c, msg, trigger, args, kwargs)
                )
                return
        return wrapped(self, irc_c, msg, trigger, args, kwargs)
    return _wrapper

def require_super(wrapped):
    @functools.wraps(wrapped)
    def _wrapper(self, irc_c, msg, trigger, args, kwargs):
        if not case_insensitive_in(msg.sender, self.runbot.superadmins):
            msg.reply("Sorry, {} cannot perform that command.".format(msg.sender))
            return
            
        login_cutoff = time.time() - self.runbot.config['login_timeout']
        if (msg.sender not in self.runbot.registered_users 
                or self.runbot.registered_users[msg.sender] < login_cutoff):
            irc_c.RAW('WHOIS {}'.format(msg.sender))
            self.runbot._whois_event_stack[msg.sender].append(
                functools.partial(wrapped, self, irc_c, msg, trigger, args, kwargs)
            )
            return

        return wrapped(self, irc_c, msg, trigger, args, kwargs)
    return _wrapper

class RunBotModule(object):
    def __init__(self, runbot, irc_c, channel, config):
        self.runbot = runbot
        self.irc_c = irc_c
        self.channel = channel
        self.config = config

        self._commands = []
        self._crons = []

    def list_commands(self):
        return [cmd for cmds in zip(*self._commands)[0] for cmd in cmds]

    def register_command(self, commands, function, channels=None):
        if not isinstance(commands, list):
            commands = [commands]
        if channels and not isinstance(channels, list):
            channels = [channels]
            
        self._commands.append((commands, function, channels))
        
        if channels:
            function = triggers_on.channel(*channels)(function)
        else:
            function = function.__func__

        function.__plugs__ = ('triggers', commands)
            
        cm = ComponentManager(self.irc_c, {})
        cm._install_hooks(self.irc_c, [function])

    def register_cron(self, name, function, seconds):
        self._crons.append((name, function, seconds))

        function.__func__.__plugs__ = ('timers', [(name, seconds)])
            
        cm = ComponentManager(self.irc_c, {})
        cm._install_hooks(self.irc_c, [function])

    def privmsg(self, to, message):
        self.irc_c.PRIVMSG(to, message)

    def msg(self, message):
        self.privmsg(self.channel, message)

    def unload(self):
        for (commands, function, channels) in self._commands:
            for cmd in commands:
                for obs in list(self.irc_c.triggers(cmd).observers()):
                    if obs._thing == function:
                        self.irc_c.triggers(cmd).unobserve(obs)
                        print("Unobserving", cmd, obs)
