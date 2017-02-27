import os
import torch
import re

class Dictionary(object):
    def __init__(self):
        self.word2idx = {}
        self.idx2word = []
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
        print ("Fewer unique tokens in set than limit", actual_length)
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
        self.dictionary = Dictionary()
        self.train = self.tokenize(os.path.join(path, 'train.txt'))
        self.valid = self.tokenize(os.path.join(path, 'valid.txt'))
        self.test = self.tokenize(os.path.join(path, 'test.txt'))


    def split(self, str):
      return re.findall(r"[\w']+|[~.,!?;]", str.lower())

    def tokenize(self, path):
        """Tokenizes a text file."""
        assert os.path.exists(path)
        # Add words to the dictionary
        print("Building Dictionary")
        with open(path, 'r') as f:
            tokens = 0
            for line in f:
                words = self.split(line)
                tokens += len(words)
                for word in words:
                    self.dictionary.add_word(word)

        print("Pruning")

        self.dictionary.prune(30000)
        # self.dictionary.prune(1000)

        print("Tokenizing")

        # Tokenize file content

        with open(path, 'r') as f:

          token_ids = []
          for line in f:
            # print('--------------')
            # print(line)
            sentences = line.split('. ')
            # print(sentences)

            def filter_unknown(sentence):
              words = self.split(sentence)
              return self.dictionary.containsWords(words)

            sentences = filter(filter_unknown, sentences)
            line = ". ".join(sentences)

            # print(line)

            words = self.split(line)

            for word in words:
                token_ids.append(self.dictionary.word2idx[word])

          print('Number of tokens in total', len(token_ids))
          ids = torch.LongTensor(len(token_ids))

          # wow, much ineffecicient
          for i in range(len(token_ids)):
            ids[i] = token_ids[i]


        return ids
