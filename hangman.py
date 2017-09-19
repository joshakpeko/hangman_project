#!/usr/bin/env python3

# -*- coding: utf_8 -*-


'''HANGMAN GAME'''


import shelve
import random
import unicodedata
from collections import namedtuple
import re


Player = namedtuple('Player', 'name ngames wins score level')
Report = namedtuple('Report', 'word tracker counter proposals')
alpha_regex = re.compile(r'[A-Za-z]+')


class GameSession:
    """Class for a player game session."""

    __dict_list = ['fr_dict', 'eng_dict']
    __attempts = 12
    __score_inc = 3
    __levels = ['novice', 'average', 'pro', 'expert', 'godhead']

    def __init__(self, player_name):
        """Open a new session for the player.
        Retrieve player stats from database or create a new ones."""

        # search player_name in players database
        # if not found create new one
        with shelve.open('scores') as db:
            try:
                player = db[player_name]
            except KeyError:
                player = Player(player_name, 0, 0, 0, 'novice')
                db[player_name] = player
            finally:
                self.__player = player

        # dispatch player stats for further update
        (self.__p_name, self.__p_ngames, self.__p_wins,
         self.__p_score, self.__p_level) = self.__player

        # 'fr_dict' as default dictionary
        self.__default_dict = self.__dict_list[0]

    @property
    def player(self):
        return self.__player

    @property
    def default_dict(self):
        return self.__default_dict

    @default_dict.setter
    def default_dict(self, dict_name):
        if dict_name in self.__dict_list:
            self.__default_dict = dict_name
        else:
            raise ValueError('unknow dictionary : %s' % dict_name)

    def pick_word(self, dico=None):
        """Return a new word picked in database, along with
        the normal form (NFD) of the word plus a blind tracker"""

        if dico is None: dico = self.default_dict
        with shelve.open('./words') as db:
            try:
                word = random.choice(db[dico])
            except KeyError as exc:
                exc.args = ('dictionnary not found',)
                raise exc
            else:
                norm_word = unicodedata.normalize('NFD', word)
                norm_word = ''.join(c for c in norm_word
                                    if not unicodedata.combining(c))
                spaced_letters = ' '.join(list(norm_word))
                tracker = alpha_regex.sub('_', spaced_letters)
                tracker = tracker.replace(' ', '')
            return (word, norm_word, tracker)

    def _validate(self, char):
        """Raise ValueError if char contains a non-
        alphabetic character. Return char otherwise."""

        if not str(char).isalpha():
            raise ValueError('non-alphabetic character found')
        return char

    def pinger(self, dico=None):
        """Coroutine that represents a game round.
        Introduce a new word and receive the player proposals 
        at each turn until its end."""

        word, norm_word, tracker = self.pick_word(dico)
        proposals = set()   # keep player letter/word proposals
        counter = self.__attempts
        key_wl = None       # whether the player wins round or not

        print(word) # debug
        while True:
            report = Report('*', tracker, counter, proposals)
            char = yield report
            if char is None:
                break

            try:
                char = self._validate(char)
            except ValueError:
                counter -= 1
            else:
                if char not in proposals:
                    counter -= 1
                    proposals.add(char)
                    args = (word, norm_word, char, tracker)
                    tracker = self._update_tracker(*args )

                if tracker == word:
                    key_wl = 1          # win
                elif counter == 0:
                    key_wl = -1         # loss

                if key_wl:
                    self._update_playerstats(key_wl)
                    break
        return Report(word, tracker, counter, proposals)

    def _update_tracker(self, *args ):
        """Update and return a tracker based on a word to find 
        and a proposed letter or word."""

        word, norm_word, char, tracker = args 
        # compare normalized versions of both word and char
        norm_char = unicodedata.normalize('NFD', char)
        norm_char = ''.join(c for c in norm_char 
                            if not unicodedata.combining(c))

        if len(char) == 1:
            tracker = list(tracker)
            for i, c in enumerate(norm_word):
                if c == norm_char:    # letter match found
                    tracker[i] = word[i]
            tracker = ''.join(tracker)

        elif norm_char == norm_word:
            tracker = word

        return tracker

    def _update_playerstats(self, key):
        """Update player stats in database."""

        self.__p_ngames += 1

        if key == 1:
            self.__p_wins += 1
            self.__p_score += self.__score_inc

        if self.__p_ngames > 5:
            average = self.__p_wins / self.__p_ngames
            average_id = int(average * len(self.__levels))
            self.__p_level = self.__levels[average_id]

        self.__player = Player(self.__p_name, self.__p_ngames,
                self.__p_wins, self.__p_score, self.__p_level)

    def save_stats(self):
        """Write player updated stats to database."""

        with shelve.open('./scores') as db:
            db[self.__p_name] = self.__player
