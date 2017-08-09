#!/usr/bin/env python3

# -*- coding: utf_8 -*-


'''HANGMAN GAME'''


import shelve
import random
import unicodedata
from collections import namedtuple
import re


Player = namedtuple('Player', 'name ngames nwins score level')


class GameSession:
    """Class for a player game session."""

    _DEFAULT_DICT = 'fr_dict'
    _ATTEMPTS = 12
    _SCORE_INC_AMOUNT = 3
    _PLAYER_LEVELS = ['novice', 'average', 'pro', 'expert', 'godhead']


    def __init__(self, player_name):
        """Open a new session for the player.
        Retrieve player stats from database or create a new ones."""

        self._player = Player(player_name, 0, 0, 0, 'novice')
        with shelve.open('scores') as db:
            try:
                self._player = db[self._player.name]
            except KeyError:
                db[self._player.name] = self._player

    @property
    def player(self):
        return self._player

    def pick_word(self, dico=None):
        """Pick a new word in database. Return it coupled with a tracker"""

        if dico is None: dico = self._DEFAULT_DICT
        with shelve.open('./words') as db:
            try:
                word = ''.join(random.sample(db[dico], 1))
            except KeyError as exc:
                exc.args = ('dictionnary not found',)
                raise exc
            else:
                alpha_regex = re.compile(r'\w+')
                spaced_word = ' '.join(list(word))
                spaced_tracker = alpha_regex.sub('_', spaced_word)
                tracker = spaced_tracker.replace(' ', '')
            return (word, tracker)

    def validate(self, letter_or_word):
        """Raise ValueError if letter_or_word contains a non-
        alphabetic character. Return True otherwise."""

        if not str(letter_or_word).isalpha():
            raise ValueError('non-alphabetic character found')
        return True

    def starter(self, dico=None):
        """Coroutine that introduces a new word and receive the
        player proposals at each turn until the end of the round."""

        Report = namedtuple('Report', 
                            'word tracker counter proposals')
        word, tracker = self.pick_word(dico)
        proposals = set()
        counter = self._ATTEMPTS
        key = None      # determine weither the player wins or looses round

        while True:
            report = Report('*', tracker, counter, proposals)
            letter_or_word = yield report
            if letter_or_word is None:
                break
            try:
                self.validate(letter_or_word)
            except ValueError:
                counter -= 1
            else:
                if letter_or_word not in proposals:
                    counter -= 1
                    proposals.add(letter_or_word)
                    components = (word, letter_or_word, tracker)
                    tracker = self._update_tracker(*components)

                if tracker == word:
                    key = 'win'
                elif counter == 0:
                    key = 'loose'
                if key:
                    self._update_player_stats(key=key)
                    break

        return Report(word, tracker, counter, proposals)

    def _update_tracker(self, *components):
        """Update and return a tracker based on a word to find 
        and a proposed letter or word."""

        hidden_word, letter_or_word, tracker = components
        asciis = []

        # get a 'only ascii' version of both letter_or_word
        # and the hidden_word so that we can easily compare
        for word in [hidden_word, letter_or_word]:
            word = unicodedata.normalize('NFD', word)
            word = ''.join(char for char in word if not unicodedata.
                                                        combining(char))
            asciis.append(word)

        ascii_hidden_word, ascii_letter_or_word = asciis

        if len(letter_or_word) == 1:
            tracker = list(tracker)
            for i, char in enumerate(ascii_hidden_word):
                if char == ascii_letter_or_word:    # letter match found
                    tracker[i] = hidden_word[i]
            tracker = ''.join(tracker)

        elif ascii_letter_or_word == ascii_hidden_word:
            tracker = hidden_word

        return tracker

    def _update_player_stats(self, key):
        """Update player stats in database."""

        with shelve.open('./scores') as db:
            name, games, wins, score, level = db[self._player.name]
            games += 1
            if key == 'win':
                wins += 1
                score += self._SCORE_INC_AMOUNT
            if games > 5:   # level update from 5 games played
                average = wins / games
                average_id = int(average * len(self._PLAYER_LEVELS))
                level = self._PLAYER_LEVELS[average_id]
            
            new_stats = Player(name, games, wins, score, level)
            db[self._player.name] = new_stats
            self._player = new_stats
