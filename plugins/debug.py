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
import time

from pyaib.plugins import observe, keyword, plugin_class, every

@plugin_class
class Debug(object):
    def __init__(self, irc_c, config):
        print("[debug] Plugin loaded.")

    @observe('IRC_RAW_MSG', 'IRC_RAW_SEND')
    def debug(self, irc_c, msg):
        print("[debug] [%s] %r" % (time.strftime('%H:%M:%S'), msg))
