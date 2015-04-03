from __future__ import (absolute_import, print_function, division,
                        unicode_literals)

import re
import requests

from plugins.runbot.services import service_class
from plugins.runbot.services.service import RunBotService

@service_class
class HitboxService(RunBotService):
    def __init__(self, games=[]):
        self.games = games

        if not isinstance(self.games, list):
            self.games = [self.games]
        
        self.endpoints = {
            'stream': 'https://www.hitbox.tv/api/media/live/list',
            'game': 'https://www.hitbox.tv/api/game/'
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
            'title': stream['media_status'],
            'viewers': stream['media_views'],
            'streamer': stream['media_user_name'],
            'url': stream['channel']['channel_link'],
        }

    def get_all_streams(self):
        '''Gets the streams for all games.

        Returns:
            A list of dicts, where each dict is a stream as returned by the
            Hitbox API.
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
        game_url = game.lower().replace(" ", "-").replace(".", "").replace(":", "")
        url = "{}/{}".format(self.endpoints['game'], game_url)

        params = {
            'seo': 'true'
        }
        req = requests.get(url, params=params)
        req_json = req.json()

        game_id = req_json.get('category', {}).get('category_id', None)

        if not game_id:
            return []

        url = self.endpoints['stream']
        params = {
            'game': game_id,
            'hiddenOnly': 'false',
            'liveonly': 'true',
        }
        return self.get_all_streams_from_url(url, params)

    def get_all_streams_from_url(self, url, params):
        streams = []
        offset = 0
        while True:
            page = self.get_page(url, params, offset, self.num_per_req)

            if not page:
                break

            streams.extend(page['livestream'])

            if len(page['livestream']) < self.num_per_req:
                break

            offset += self.num_per_req
        
        return streams

    def get_page(self, url, params, offset=0, num_per_req=100):
        pagination = {
            'limit': num_per_req,
            'offset': offset,
        }
        pagination.update(params)
        req = requests.get(url, params=pagination)
        if req.content == "no_media_found":
            return None
        return req.json()
