import pathlib
import random

class WordManager:
    def __init__(self):
        base_path = pathlib.Path(__file__).resolve().parent.parent
        self.filepath = base_path / 'data' / 'sedout.txt'
        self.words = self.load_words(self.filepath)
        self.word = random.choice(list(self.words))

    def load_words(self, filename):
        words = set()
        with open(filename, 'r', encoding='utf-8') as file:
            for line in file:
                words.add(line.strip().upper())
        return words

    def is_valid(self, word):
        return word.upper() in self.words

    def get_word(self): return self.word