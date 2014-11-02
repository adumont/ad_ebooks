import random

class MarkovChainer(object):
    def __init__(self, chain_size):
        self.chain_size = chain_size
        self.EOS = ['.', '?', '!']
        self.dict = {}
        self.words = []
        self.cache = {}
        
    def chains(self):
        if len(self.words) < self.chain_size:
            return
        for i in range(len(self.words) - self.chain_size - 1):
            yield tuple(self.words_at_position(i))

    def words_at_position(self, i):
        """Uses the chain size to find a list of the words at an index."""
        chain = []
        for chain_index in range(0, self.chain_size):
            chain.append(self.words[i + chain_index])
        return chain

    def build_dict(self):
        for chain_set in self.chains():
            key = chain_set[:self.chain_size - 1]
            next_word = chain_set[-1]
            if key in self.cache:
                self.cache[key].append(next_word)
            else:
                self.cache[key] = [next_word]

    def generate_sentence(self):
        self.build_dict()
        word_size = len(self.words)        
        
        while True: # loop until we find a seed word that starts with a capital letter
            seed = random.randint(0, word_size - 3)
            gen_words = []
            seed_words = self.words_at_position(seed)[:-1]
            if seed_words[0][0].isupper():
                break

        gen_words.extend(seed_words)
        while True:
            last_word_len = self.chain_size - 1
            last_words = gen_words[-1 * last_word_len:]
            next_word = random.choice(self.cache[tuple(last_words)])
            gen_words.append(next_word)
            if next_word[-1] in self.EOS: 
                break
        return ' '.join(gen_words)

    def add_text(self, text):
        words = text.split()
        for w in words:
            self.words.append(w)

if __name__ == "__main__":
    print "Try running ebooks.py first"