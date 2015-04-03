from __future__ import (absolute_import, print_function, division,
                        unicode_literals)

import re
import requests

from plugins.runbot.services import service_class
from plugins.runbot.services.service import RunBotService

@service_class
class TwitchService(RunBotService):
    def __init__(self, games=[]):
        self.games = games

        if not isinstance(self.games, list):
            self.games = [self.games]
        
        self.endpoints = {
            'stream': 'https://api.twitch.tv/kraken/streams'
        }

        self.num_per_req = 100;

    def extract_stream_info(self, stream):
        '''Extracts title, viewer count, streamer name and url info from a
        stream dict.
        
        Args: 
            stream: A dict as output from get_all_streams()

        Returns:
            A dict with keys: title, viewers, streamer, url
        '''
        
        return {
            'title': stream['channel'].get('status', ''),
            'viewers': stream.get('viewers', 0),
            'streamer': stream['channel'].get('display_name', ''),
            'url': stream['channel'].get('url', ''),
        }

    def get_all_streams(self):
        '''Gets the streams for all games.

        Returns:
            A list of dicts, where each dict is a stream as returned by the
            Twitch v3 API.
            https://github.com/justintv/Twitch-API/blob/master/v3_resources/streams.md
        '''

        streams = []
        for game in self.games:
            streams.extend(self.get_all_streams_of_game(game))
        return streams

    def get_all_streams_of_streamers(self, streamers):
        url = self.endpoints['stream']
        params = {
            'channel': ",".join(streamers)
        }
        return self.get_all_streams_from_url(url, params)

    def get_all_streams_of_game(self, game):
        url = self.endpoints['stream']
        params = {
            'game': game
        }
        return self.get_all_streams_from_url(url, params)

    def get_all_streams_from_url(self, url, params):
        streams = []
        page = self.get_page(url, params)

        total = page['_total']
        streams.extend(page['streams'])

        offset = self.num_per_req
        last_page_offset = total // self.num_per_req * self.num_per_req;

        while (offset < last_page_offset):
            page = self.get_page(url, params, offset,
                    self.num_per_req)
            streams.extend(page['streams'])
            offset += self.num_per_req
        
        return streams

    def get_page(self, url, params, offset=0, num_per_req=100):
        pagination = {
            'limit': num_per_req,
            'offset': offset,
        }
        pagination.update(params)
        req = requests.get(url, params=pagination)
        return req.json()
