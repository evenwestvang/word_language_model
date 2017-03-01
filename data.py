import os
import torch
import re
import math
import h5py, json

TOKENCOUNT = 50000

class Dictionary(object):
    def __init__(self, path):

      # word to index lookup
      self.word2idx = {}
      # array of tokens
      self.idx2word = []

      # absolute counts
      self.wordCount = {}

    def add_word(self, word):
        if word not in self.wordCount:
          self.wordCount[word] = 1
        else:
          self.wordCount[word] += 1

    def prune(self, nth_most_common):
      words = self.wordCount.keys()
      actual_length = len(words)

      if nth_most_common > actual_length:
        print ("Fewer unique tokens in set than limit:", actual_length)
        nth_most_common = actual_length - 1

      def getKey(word):
        return self.wordCount[word]

      sorted_words = sorted(words, key=getKey, reverse=True)
      print('Frequency of least common word still in set:', self.wordCount[sorted_words[nth_most_common]])

      # print (sorted_words)

      words = sorted_words[0:nth_most_common]

      # complete pruning

      print('Word up')
      # print(words)

      self.word2idx = {}
      self.idx2word = []

      for i in range(len(words)):
        self.idx2word.append(words[i])
        self.word2idx[words[i]] = len(self.idx2word) - 1

      # print(self.word2idx)


    def containsWords(self, wordArray):
      # print (wordArray)
      for word in wordArray:
        if word not in self.word2idx:
          return False
      return True

    def __len__(self):
        return len(self.idx2word)


class Corpus(object):
    def __init__(self, path):
      self.dictionary = Dictionary(path)

      indexed_lines = []

      if os.path.exists(os.path.join(path, 'dictionary.json')):
        # load dictionary
        print("Loading dictionary")

        with h5py.File(os.path.join(path, 'indexed.hdf'),'r', encoding="utf-8") as f:
          dset = f['indexes']
          indexed_lines = torch.LongTensor(dset[...])

        with open(os.path.join(path, 'dictionary.json'), 'r') as f:
          self.dictionary.idx2word = json.load(f)

        # self.train = self.tokenize(os.path.join(path, 'train.txt'))
        # self.valid = self.tokenize(os.path.join(path, 'valid.txt'))
        # self.test = self.tokenize(os.path.join(path, 'test.txt'))

      else:
        self.idx2forms = []
        self.base2idx = {}
        self.extended2idx = {}

        self.loadStems(path)
        tokens_lines = self.lines_to_tokens(path)
        indexed_lines = self.index(tokens_lines)

        cnt = len(indexed_lines)

        with h5py.File(os.path.join(path, 'indexed.hdf'),'w') as f:
          dset = f.create_dataset('indexes', (cnt,), dtype='int64')
          dset[...] = indexed_lines.numpy()

        with open(os.path.join(path, 'dictionary.json'), 'w', encoding="utf-8") as f:
          json.dump(self.dictionary.idx2word, f)

      cnt = len(indexed_lines)
      self.train = indexed_lines[0:math.floor(cnt*0.8)]
      self.valid = indexed_lines[math.floor(cnt*0.8):math.floor(cnt*0.9)]
      self.test = indexed_lines[math.floor(cnt*0.9):math.floor(cnt*1)]

      # print(indexed_lines)
      # self.train = indexed_lines
      # self.valid = indexed_lines
      # self.test = indexed_lines


    def lines_to_tokens(self, path):
      with open(os.path.join(path, 'data.txt'), 'r', encoding="utf-8") as f:
        print("Tokenizing")
        tokenized_sentences = []

        lineCnt = 0

        for line in f:

          lineCnt += 1
          # if lineCnt > 300:
          #   break

          # flatten punctuation
          line = re.sub(r'(\W)(?=\1)', '', line).lower()

          # convert to sentences
          sentences = [sentence.strip() for sentence in re.split(r"[\.\!\?]\s|\w[\.\!\?]\w", line)]
          sentences = list(filter(None, sentences))
          sentences = [sentence + '.' if len(sentence) > 1 else sentence for sentence in sentences]

          for sentence in sentences:
            tokens = [self.subtokenize(token, []) for token in self.split(sentence)]
            finalTokens = []

            for token in tokens:
              if len(token) == 1:
                finalTokens += [token[0]]
              else:
                # print(token)
                for subtoken in token:
                  finalTokens += [subtoken]
                  if subtoken != token[-1]:
                    finalTokens += ['+']
            tokenized_sentences.append(finalTokens)
      return tokenized_sentences


    def subtokenize(self, token, tokensFound):
      if len(token) <= 2: return [token]

      hits = []
      # print('\n\nToken:', token)

      for i in range(4, len(token) + 1):

        if token[0:i] in self.extended2idx:
          hits.append(i)
          # print('-', token[0:i])

      if len(hits) == 0:
        tokensFound += [token]
        # print('Terminated with:', tokensFound)

      else:

        # print (token)
        # print ('hits:', hits)

        firstWord = -1
        wordBoundary = -1
        # print ('\n', token, hits)
        for i in range(len(hits)):
          base, extended = self.idx2forms[self.extended2idx[token[0:hits[i]]]]
          if firstWord == -1:
            firstWord = base
            # print (base, firstWord)
          elif base != firstWord:
            wordBoundary = i - 1
            # print (base, firstWord)
            break

        hit = 0

        if wordBoundary != -1:
          hit = hits[wordBoundary]
        else:
          if len(hits) >= 5:
            hit = hits[math.floor(len(hits)/2)]
          else:
            hit = hits[-1]

        idx = self.extended2idx[token[0:hit]]
        base, extended = self.idx2forms[idx]
        # print ('forms: ', base, extended, self.idx2forms[idx])

        # Chop up into stem and base if similar
        if len(base) < len(extended) and extended.startswith(base):
          tokensFound += [base, extended.replace(base,"")]
        else:
          tokensFound += [extended]

        # print('Found:', tokensFound)

        if hit < len(token):
          # print('Recursing: ', token[hit:])
          tokensFound += self.subtokenize(token[hit:], [])

      return tokensFound

    def split(self, str):
      return re.findall(r"[\w']+|[~.,!?;]", str.lower())

    def index(self, tokenized_lines):

      print("Counting")

      for line in tokenized_lines:
        for word in line:
          self.dictionary.add_word(word)

      print("Found", len(self.dictionary.wordCount), "unique tokens.")

      print("Pruning to ", TOKENCOUNT)

      self.dictionary.prune(TOKENCOUNT)

      print("Making vector")

      included = 0
      discarded = 0

      token_ids = []
      for line in tokenized_lines:
        if self.dictionary.containsWords(line):
          included += 1
          for word in line:
              token_ids.append(self.dictionary.word2idx[word])
        else:
          discarded += 1

      print ('included / discarded', included, discarded)
      print('Length of token vector:', len(token_ids))
      ids = torch.LongTensor(len(token_ids))

      # wow, much ineffecicient
      for i in range(len(token_ids)):
        ids[i] = token_ids[i]

      return ids

    def loadStems(self, path):
      print("Loading morphemes")
      with open(os.path.join(path, 'fullform_bm.txt'), 'r', encoding="utf-8") as f:
        for line in f:
          columns = line.split("\t")
          if len(columns) > 2:
            base = columns[1]
            extended = columns[2]
            self.idx2forms.append([base, extended])
            self.base2idx[base] = len(self.idx2forms) - 1
            self.extended2idx[extended] = len(self.idx2forms) -1


if __name__ == "__main__":
   # stuff only to run when not called via 'import' here
   Corpus('./data/local/')
