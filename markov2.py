import sys
from pprint import pprint
from random import choice

class MarkovChainer(object):
    def __init__(self, order):
        self.order = order
        self.EOS = ['.', '?', '!']
        self.dict = {}
        self.words = []


    def build_dict(self, words):
        """
        Build a dictionary from the words.

        (word1, word2) => [w1, w2, ...]  # key: tuple; value: list
        """
        d = {}
        for i, word in enumerate(words):
            try:
                first, second, third = words[i], words[i+1], words[i+2]
            except IndexError:
                break
            key = (first, second)
            if key not in d:
                d[key] = []
            #
            d[key].append(third)

        return d

    def generate_sentence(self):
        d = self.build_dict(self.words)
        li = [key for key in d.keys() if key[0][0].isupper()]
        key = choice(li)

        li = []
        first, second = key
        li.append(first)
        li.append(second)
        while True:
            try:
                third = choice(d[key])
            except KeyError:
                break
            li.append(third)
            if third[-1] in self.EOS:
                break
            # else
            key = (second, third)
            first, second = key

        return ' '.join(li)

    def add_text(self, text):
        words = text.split()
        for w in words:
            self.words.append(w)

if __name__ == "__main__":
    print "Try running ebooks.py first"