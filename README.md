## Installing ##

    pip install -r requirements.txt

## Running ##

    python ./runbot.py

## Configuring ##

See `runbot.conf`

## Adding a new service ##

1. Create `yourservice.py` in `/plugins/runbot/services`
    a. See `/plugins/runbot/services/service.py` for the interface.
    b. See `/plugins/runbot/services/twitch.py` for an example.
2. Modify `runbot.conf` to add `yourservice` to the list of services

## New service template ##

    from __future__ import (absolute_import, print_function, division,
                            unicode_literals)

    import re
    import requests

    from plugins.runbot.services import service_class
    from plugins.runbot.services.service import RunBotService

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
