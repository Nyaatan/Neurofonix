from random import randint


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
