import os
import sys

import pickle
import threading
from random import randint
from time import sleep

import asyncio

import discord
from pyprind import ProgBar
import json
# from . import markov
from musicbot import bot
from discord.ext import commands

_kg_music_id = 693769797963350047


class MusicBot(bot.MusicBot):

    def __init__(self, config_file=None, perms_file=None, aliases_file=None):
        super().__init__()
        try:
            self.model = pickle.load(open('neurofonix/msgs.model', 'rb'))
        except Exception as e:
            print(e)
            self.model = None
        self.messages = {}
        self.msg_list = []
        self._autoplay = False

    def train(self, lst: list):
        print('Training...', file=sys.stderr)
        text = ''
        lst.reverse()
        self.model = Model(lst)
        self.model.train()
        pickle.dump(self.model, open('neurofonix/msgs.model', 'wb'))

    @staticmethod
    def play_search_predicate(message):
        return 'play ' in message.content or 'search ' in message.content

    last_20 = []

    async def _cmd_autoplay(self):
        queue = self.model.get_next()
        iter = 0
        while queue in self.last_20:
            queue = self.model.get_next()
            iter += 1
            if iter == 10:
                self.model.last = None
        self.last_20.append(queue)
        if len(self.last_20) == 20:
            self.last_20.pop(0)
        print(queue.replace('-play', '').replace('-search', ''))
        play_task = asyncio.create_task(self.cmd_play(self.tempmessage, self.tempplayer, self.tempchannel,
                                                      self.tempauthor, self.temppermissions, self.templeftover_args, queue))
        await play_task
        if self._autoplay:
            await asyncio.sleep(120)
            autoplay_task = asyncio.create_task(self._cmd_autoplay())
            await autoplay_task

    async def cmd_autoplay(self, message, player, channel, author, permissions, leftover_args):
        if not self._autoplay:
            self._autoplay = True
            if self._autoplay:
                self.tempmessage = message
                self.tempplayer = player
                self.tempchannel = channel
                self.tempauthor = author
                self.temppermissions = permissions
                self.templeftover_args = leftover_args
                autoplay_task = asyncio.create_task(self._cmd_autoplay())
                await autoplay_task

    async def cmd_autostop(self):
        self._autoplay = False
        self.last_20 = []

    async def cmd_update(self, message):
        channel = message.channel
        await self.send_typing(channel)
        msgs = [elem async for elem in channel.history(limit=None).filter(self.play_search_predicate)]
        bar = ProgBar(len(msgs))
        for msg in msgs:
            if "```" not in msg.content and msg.author.name != 'Neurofonix':
                self.msg_list.append(msg.content.replace('-play ', '').replace('!play', ''))
            # if msg.author.name not in messages.keys():
            #     messages[msg.author.name] = []
            # messages[msg.author.name].append(msg.content)
            bar.update()
        json.dump(self.msg_list, open('neurofonix/msgs.json', 'w+'), sort_keys=True, indent=4)
        self.train(self.msg_list)
        await message.channel.send("Updated.")


class Model:
    def __init__(self, text):
        self.text = text
        self.model = {}
        self.last = None

    def train(self):
        if self.text is str:
            split_text = self.text.split(' ')
        else:
            split_text = self.text
        i = 0
        raw_model = {}
        for word in split_text:
            if word not in raw_model.keys():
                raw_model[word] = []
            try:
                raw_model[word].append(split_text[i + 1])
            except IndexError:
                pass
            i += 1
        # print(raw_model)
        for word in raw_model.keys():
            counts = {}
            for occ in raw_model[word]:
                if occ not in counts.keys():
                    counts[occ] = raw_model[word].count(occ)
            counts['__len__'] = len(raw_model[word])
            probs = {}
            for key in counts.keys():
                if key != '__len__':
                    probs[key] = counts[key] / counts['__len__']
            print(word, probs)
            self.model[word] = probs

    def get_next(self, start=None):
        if start is not None:
            if '-play' not in start:
                start = '-play %s' % start
            self.last = start
            return start
        if self.last is None:
            self.last = list(self.model.keys())[randint(0, len(self.model.keys()))]
            return self.last

        rand = randint(0, 100)
        rsum = 0
        try:
            for next_word in self.model[self.last]:
                rsum += self.model[self.last][next_word] * 100
                if rsum >= rand:
                    return next_word
        except:
            self.last = list(self.model.keys())[randint(0, len(self.model.keys()))]
            return self.last

