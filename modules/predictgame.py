from dota2py import api
from modules.module import Module
from collections import defaultdict
import json
import discord
import re
import pymongo
import threading
import asyncio
import time

config = json.load(open('config.json'))

class PredictGame(Module):

    def __init__(self, client):
        Module.__init__(self, 'PredictGame', client)
        # set the api key using the config
        api.set_api_key(config['steamApi'])

        # initialize the predictions field
        self.predictions = defaultdict(lambda: {'predictions': {}, 'info': None})

        # cached league names
        self.league_cache = {}

        # mongo setup
        self.dbclient = pymongo.MongoClient('localhost', 27017)
        self.db = self.dbclient['botdooder']
        self.fredpoints = self.db['fredpoints']

        # default channel
        self.default_channel = None

        # start the 60 second status check loop
        self.client.loop.create_task(self.check_game_status())

    def get_commands(self):
        return {
            '!livegames': self.send_live_games,
            '!fp': self.send_fred_points,
            '!bet': self.predict,
            '!leaderboard': self.send_leaderboard
        }

    async def send_live_games(self, message, content):
        league_games = api.get_live_league_games()['result']
        response_list = []
        for game in league_games['games']:
            if 'radiant_team' not in game:
                continue
            if 'dire_team' not in game:
                continue
            radi_team = game['radiant_team']['team_name']
            dire_team = game['dire_team']['team_name']
            match_id = str(game['match_id'])
            game_num = str(game['game_number'])
            league_name = self.get_league_name(game['league_id'])

            duration = 0
            if 'scoreboard' in game:
                duration = game['scoreboard']['duration']
            mins = int(duration / 60)
            seconds = int(duration % 60)
            dur_str = '%d:%02d' % (mins, seconds)

            response_list.append(league_name + ' - **' + 
                radi_team + '** vs. **' + dire_team + '**' + 
                ' - ' + dur_str)

        response = '\n'.join(response_list)
        await self.client.send_message(message.channel, response)

    async def send_fred_points(self, message, content):
        name = message.author.name
        fp = self.get_available_fp(name)
        response = '%s has %d FP.' % (name, fp)
        await self.client.send_message(message.channel, response)

    def get_league_name(self, league_id):
        league_id = int(league_id)
        if league_id in self.league_cache:
            return self.league_cache[league_id]
        else:
            league_listing = api.get_league_listing()['result']
            self.league_cache = {lg['leagueid']: lg['name'] for lg in league_listing['leagues']}
            return self.league_cache[league_id]

    def get_available_fp(self, name):
        fplisting = self.fredpoints.find_one({'name': name})

        if fplisting == None:
            fplisting = {'name': name, 'fp': 1000, 'predictions': 0, 'correct': 0}
            self.fredpoints.insert(fplisting)
        elif fplisting['fp'] == 0:
            self.fredpoints.update({'name': name}, {'$set': {'fp': 1}})

        used_fp = sum([v['predictions'][name]['fp'] \
            for k, v in self.predictions.items() \
            if name in v['predictions']])
        return fplisting['fp'] - used_fp

    def modify_fp(self, name, fp, victory):
        query = {'name': name}
        update = None
        if victory:
            update = {'$inc': {'predictions': 1, 'correct': 1, 'fp': fp}}
        else:
            update = {'$inc': {'predictions': 1, 'fp': fp}}
        self.fredpoints.update(query, update)


    async def predict(self, message, content):
        if message.channel != None and not message.channel.is_private:
            self.default_channel = message.channel
        if len(content) < 3:
            return

        fp_amount = 0
        try:
            fp_amount = int(content[1])
        except ValueError:
            return
        team_name = ' '.join(content[2:])
        user_name = message.author.name

        if fp_amount < 1:
            return

        # construct reverse map from team name to lobby
        league_games = api.get_live_league_games()['result']
        team_to_lobby = {}
        for game in league_games['games']:
            if 'radiant_team' not in game:
                continue
            if 'dire_team' not in game:
                continue
            radi_team = game['radiant_team']['team_name'].lower()
            dire_team = game['dire_team']['team_name'].lower()

            team_to_lobby[radi_team] = game
            team_to_lobby[dire_team] = game

        # find game
        if team_name.lower() not in team_to_lobby:
            return

        game = team_to_lobby[team_name.lower()]
        duration = 0
        if 'scoreboard' in game:
            duration = game['scoreboard']['duration']
        if duration > 0:
            response = 'The game has already begun, betting is now closed.'
            await self.client.send_message(message.channel, response)
            return

        preds = self.predictions[game['match_id']]

        prev_fp = 0
        prev_team = None

        avail_fp = self.get_available_fp(user_name) + prev_fp

        preds['info'] = game
        radi_team = game['radiant_team']['team_name']
        dire_team = game['dire_team']['team_name']
        team_name_match = ''
        if team_name.lower() == radi_team.lower():
            team_name_match = radi_team
        else:
            team_name_match = dire_team

        if user_name in preds['predictions']:
            prev_team = preds['predictions'][user_name]['radiant']

        # bet on other team
        if prev_team != None and (team_name_match == radi_team) != prev_team:
            response = 'You already bet on the other team!'
            await self.client.send_message(message.channel, response)
            return

        # not enough fp
        if fp_amount > avail_fp:
            response = 'You do not have enough FP. (%d)' % (avail_fp,)
            await self.client.send_message(message.channel, response)
            return

        # bet higher
        if user_name in preds['predictions']:
            prev_fp = preds['predictions'][user_name]['fp']
            if fp_amount <= prev_fp:
                response = 'You must bet higher than your previous amount. (%d)' % (prev_fp,)
                await self.client.send_message(message.channel, response)
                return


        preds['predictions'][user_name] = {'fp': fp_amount, 'radiant': (team_name_match == radi_team)}

        response = '%s has wagered **%d FP** on **%s** in %s vs. %s!' \
            % (user_name, fp_amount, team_name_match, radi_team, dire_team)
        await self.client.send_message(message.channel, response)
        return

    async def check_game_status(self):
        while not self.client.is_closed:
            try:
                deletions = []
                for match_id, game in self.predictions.items():
                    game_status = api.get_match_details(match_id)['result']
                    if 'radiant_win' in game_status:
                        await self.resolve_game(match_id, game_status['radiant_win'])
                        deletions.append(match_id)

                for m in deletions:
                    self.predictions.pop(m, None)
            except:
                print('Could not fetch match data.')

            await asyncio.sleep(30)

    async def resolve_game(self, match_id, radiant_win):
        response_list = []
        winner = ''
        loser = ''
        game = self.predictions[match_id]['info']
        radi_team = game['radiant_team']['team_name']
        dire_team = game['dire_team']['team_name']
        if radiant_win:
            winner = radi_team
            loser = dire_team
        else:
            winner = dire_team
            loser = radi_team

        response_list.append('__%s has defeated %s!__' % (winner, loser))
        for better, val in self.predictions[match_id]['predictions'].items():
            fp = val['fp']
            cur_fp = self.get_available_fp(better) + fp

            if radiant_win == val['radiant']:
                final_fp = cur_fp + fp
                self.modify_fp(better, fp, True)
                response = '%s bet %d FP and won! (%d -> %d)' % (better, fp, cur_fp, final_fp)
                response_list.append(response)
            else:
                final_fp = cur_fp - fp
                self.modify_fp(better, -fp, False)
                response = '%s bet %d FP and lost it all! (%d -> %d)' % (better, fp, cur_fp, final_fp)
                response_list.append(response)

        await self.client.send_message(self.default_channel, '\n'.join(response_list))

    async def send_leaderboard(self, message, content):
        response_list = []
        users = self.fredpoints.find({})
        for u in sorted(users, key=lambda x: -x['fp']):
            percent_correct = 0
            if u['predictions'] > 0:
                percent_correct = int(float(u['correct']) / u['predictions'] * 100)
            response = '%s - %d FP - %d victories, %d predictions (%d%%)' % \
                (u['name'], u['fp'], u['correct'], u['predictions'], percent_correct)
            response_list.append(response)

        await self.client.send_message(message.channel, '\n'.join(response_list))
