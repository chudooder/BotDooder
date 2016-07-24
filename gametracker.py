from module import Module
from collections import defaultdict
from datetime import timedelta, datetime
import re
import pymongo
import discord
import dateparser

class GameTracker(Module):

    def __init__(self, client):
        Module.__init__(self, 'GameTracker', client)
        # mongo setup
        self.dbclient = pymongo.MongoClient('localhost', 27017)
        self.db = self.dbclient['botdooder']
        self.sessions = self.db['sessions']

        self.game_states = defaultdict(lambda: {'game': None, 'time': None})

    async def on_message(self, message):
        content = re.findall("([^\"]\\S*|\".+?\")\\s*", message.content)
        content = [re.sub(r'[\'\"]', '', s) for s in content if s != None]
        if content[0] != '!playtime':
            return

        # search target user or game: default message sender's name
        target = ''
        if len(content) < 2:
            target = message.author.name
        else:
            target = content[1]

        base_response = '__Total play time for %s:__\n' % (target,)
        startdate = datetime.min
        if len(content) > 2:
            startdate = dateparser.parse(content[2])
            base_response = '__Play time for %s since %s__:\n' % (target, startdate.strftime('%Y/%m/%d'))

        enddate = datetime.max
        if len(content) > 3:
            enddate = dateparser.parse(content[3])
            base_response = '__Play time for %s from %s to %s__:\n' % (target, startdate.strftime('%Y/%m/%d'), enddate.strftime('%Y/%m/%d'))

        results = self.sessions.find({'name': target, 'startTime': {'$gte': startdate, '$lte': enddate}})

        count = 0
        games = defaultdict(timedelta)
        target_id = None
        for result in results:
            count += 1
            if target_id == None:
                target_id = result['user']
            games[result['game']] += result['endTime'] - result['startTime']

        # tack on the current game's play time, if they're playing a game
        if target_id in self.game_states and self.game_states[target_id]['game'] != None:
            games[self.game_states[target_id]['game'].name] += datetime.now() - self.game_states[target_id]['time']

        # got a hit for the user: send the response
        if count > 0:
            response = base_response
            for g, t in sorted(zip(games.keys(), games.values()), key=lambda p: -p[1]):
                hours, remainder = divmod(t.total_seconds(), 3600)
                minutes, seconds = divmod(remainder, 60)
                timestr = '%d:%02d:%02d' % (hours, minutes, seconds)
                response += ('**' + str(g) + '**  - ' + timestr +'\n')

            await self.client.send_message(message.channel, response)
            return

        # no hits for user, try a game query
        results = self.sessions.find({'game': target, 'startTime': {'$gte': startdate, '$lte': enddate}})
        users = defaultdict(timedelta)
        user_ids = defaultdict(str)
        for result in results:
            count += 1
            users[result['name']] += result['endTime'] - result['startTime']
            user_ids[result['user']] = result['name']

        for user in user_ids.keys():
            if user in self.game_states and self.game_states[user]['game'] != None and self.game_states[user]['game'].name == target:
                user_state = self.game_states[user]
                users[user_ids[user]] += datetime.now() - user_state['time']

        if count > 0:
            response = base_response
            for u, t in sorted(zip(users.keys(), users.values()), key=lambda p: -p[1]):
                hours, remainder = divmod(t.total_seconds(), 3600)
                minutes, seconds = divmod(remainder, 60)
                timestr = '%d:%02d:%02d' % (hours, minutes, seconds)
                response += ('**' + str(u) + '** - ' + timestr +'\n')

            await self.client.send_message(message.channel, response)
            return

        # literally nothing
        return

    async def on_member_update(self, before, after):
        name = after.name
        user_id = after.id
        game = after.game
        status = after.status
        prev_game = before.game
        prev_status = before.status

        # user goes offline: end session
        if status == discord.Status.offline:
            self.create_session(user_id, name, prev_game)
            print(name, 'is now offline')

        # user comes online
        elif status == discord.Status.online and prev_status == discord.Status.offline:
            # log the new game session
            self.game_states[user_id]['game'] = game
            self.game_states[user_id]['time'] = datetime.now()
            if game == None:
                print(name, 'is now online')
            else:
                print(name, 'is now playing', game)

        # if user has started/stopped/switched playing a game
        elif prev_game != game:
            self.create_session(user_id, name, prev_game)

            # log the new game session
            self.game_states[user_id]['game'] = game
            self.game_states[user_id]['time'] = datetime.now()
            if game == None:
                print(name, 'is no longer playing anything')
            else:
                print(name, 'is now playing', game)


    def create_session(self, user_id, name, prev_game):
        if prev_game != None and self.game_states[user_id]['time'] != None:
            # create a session object to represent the last game played
            start_time = self.game_states[user_id]['time']
            end_time = datetime.now()

            session = {
                'user': user_id,
                'name': name,
                'game': prev_game.name,
                'startTime': start_time,
                'endTime': end_time
            }
            self.sessions.insert_one(session)