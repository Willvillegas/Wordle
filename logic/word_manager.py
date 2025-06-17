import pathlib
import random

class WordManager:
    def __init__(self):
        base_path = pathlib.Path(__file__).resolve().parent.parent
        self.path_valid_words = base_path / 'data' / 'sedout.txt'
        self.path_playable_words = base_path / 'data' / 'pr.txt'
        self.valid_words = self.load_words(self.path_valid_words)
        self.playable_words = self.load_playable_words(self.path_playable_words)
        self.word = random.choice(self.playable_words)

    def load_words(self, filename):
        valid_words = set()
        with open(filename, 'r', encoding='utf-8') as file:
            for line in file:
                valid_words.add(line.strip().upper())
        return valid_words

    def load_playable_words(self, filename):
        playable_words = []
        with open(filename, 'r', encoding='utf-8') as file:
            for line in file:
                playable_words.append(line.strip().upper())
        return playable_words

    def is_valid(self, word):
        return word.upper() in self.valid_words

    def get_word(self): return self.word