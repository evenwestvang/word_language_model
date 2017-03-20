import os
import torch
import re
import math
import h5py, json
from pprint import pprint
from splitter import split_line_sentences_words

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

      if False: # os.path.exists(os.path.join(path, 'dictionary.json')):
        # load dictionary
        print("Loading dictionary")

        with h5py.File(os.path.join(path, 'indexed.hdf'),'r', encoding="utf-8") as f:
          dset = f['indexes']
          indexed_lines = torch.LongTensor(dset[...])

        with open(os.path.join(path, 'dictionary.json'), 'r') as f:
          self.dictionary.idx2word = json.load(f)

      else:

        tokens_lines = self.corpus_to_tokens(path)
        indexed_lines = self.index(tokens_lines)

        cnt = len(indexed_lines)

        with h5py.File(os.path.join(path, 'indexed.hdf'),'w') as f:
          dset = f.create_dataset('indexes', (cnt,), dtype='int64')
          dset[...] = indexed_lines.numpy()

        with open(os.path.join(path, 'dictionary.json'), 'w', encoding="utf-8") as f:
          json.dump(self.dictionary.idx2word, f)

      cnt = len(indexed_lines)
      self.train = indexed_lines[0:math.floor(cnt*0.9)]
      self.valid = indexed_lines[math.floor(cnt*0.9):math.floor(cnt*0.95)]
      self.test = indexed_lines[math.floor(cnt*0.95):math.floor(cnt*1)]


    def corpus_to_tokens(self, path):
      with open(os.path.join(path, 'data.txt'), 'r', encoding="utf-8") as f:
        print("Tokenizing")
        tokenized_sentences = []
        lineCnt = 0

        for line in f:

          lineCnt += 1
          if lineCnt % 500 == 0:
            print('- At line ', lineCnt)
          # if lineCnt > 8000:
          #   break

          # flatten punctuation
          line = line.lower()
          tokenized_sentences += split_line_sentences_words(line)

      return tokenized_sentences


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
      print('Building tensor')
      # wow, much ineffecicient
      ids = torch.LongTensor(len(token_ids))
      for i in range(len(token_ids)):
        ids[i] = token_ids[i]
      return ids


if __name__ == "__main__":
   Corpus('./data/local/')
