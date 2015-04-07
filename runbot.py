#!/usr/bin/env python
#
# Copyright 2013 Facebook
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import sys
import yaml
from pyaib.ircbot import IrcBot

argv = sys.argv[1:]
bot = IrcBot(argv[0] if argv else 'core.conf')

# Load the IRC information from the RunBot sub-configuration
runbot_config_file = bot.irc_c.config['plugin']['runbot']['config']
with open(runbot_config_file, 'r') as fp:
    runbot_config = yaml.safe_load(fp)
bot.irc_c.config['irc'].update(runbot_config['irc'])

bot.run()
