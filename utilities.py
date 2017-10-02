#!/usr/bin/env python3

"""Utility objects and functions for hangman.py"""


from collections import namedtuple
import re
import os
import shelve


Player = namedtuple('Player', 'name ngames wins score level')
Report = namedtuple('Report', 'word tracker counter proposals')
alpha_regex = re.compile(r'[A-Za-z]+')


dicts = {'fr_dict', 'eng_dict'}     # word dicts keys for reference


def words_db_init():
    """Create or overwrite a db to store words dictionaries. 
    Should be kept in the subdirectory named 'dicos', the TXT files
    that represent each language dictionary.
    `words_eng.txt` and `words_fr.txt` are provided by default.
    Future additional dictionaries should follow the same naming rule:
    `words_[lang].txt`."""

    try:
        dicos = [item for item in os.listdir('dicos')]
    except FileNotFoudError:
        os.makedirs('dicos')
        return False

    dicos = [item for item in dicos if os.path.isfile(
                os.path.join('dicos', item))]
    dicos = [fname for fname in dicos if fname.lower().endswith(
                '.txt')]

    if not dicos:           # no .txt file found inside dicos
        return False

    with shelve.open('words') as db:
        for fname in dicos:
            prefix = fname.split('.')[0]        # strip away .txt
            prefix = prefix.split('_')[-1]      # string after '_'
            key = '{}_dict'.format(prefix)
            dicts.add(key)
            abs_fname = os.path.join('dicos', fname)

            with open(abs_fname, encoding='utf-8') as fp:
                word_list = fp.readlines()
                word_list = [word.strip() for word in word_list]
                db[key] = word_list

    return True
