import os
from pprint import pprint

      # scan from front > 7/8
      # start segments on 0, consume hits
      # permute after
      # check for segments 1-2 missing chars (with penalty)
      # bonus for hitting every character
      # bonus for stemmed words
      # bonus for hitting end of word

class WordNode(object):

  START = 0
  END = 1
  LENGTH = 2
  BINGO = 3
  BASE_FORM = 4
  EXTENDED_FORM = 5
  ENDING = 6
  BINGO = 7

  def __init__(self, processor, sequence, score):

    self.score = score
    self.sequence = sequence
    self.processor = processor
    self.children = []

    # pprint([self.sequence, score])

    length = self.calc_length()
    # print('len',length)

    if (length == len(processor.word)):
      self.done = True
      # print('done! – ', self.sequence)
      self.score += (self.score * len(self.sequence)) * 0.1

      processor.addSolve([self.sequence, self.score])
      return
    else:
      self.done = False

    has_hits = False

    def scoreWord(length):
      if length > 4:
        length -= (length - 4)
      return length ** 4

    for hit in processor.hits:

      if hit[WordNode.START] == length:
        has_hits = True

        if hit[WordNode.BINGO] and length + hit[WordNode.LENGTH] == len(processor.word):
          new_score = self.score + (scoreWord(hit[WordNode.LENGTH]) * 2)
          # print('bingo', new_score)
          new_sequence = sequence + [hit[WordNode.BASE_FORM], hit[WordNode.ENDING] ]
          self.newChild(new_sequence, new_score)
        else:
          new_score = self.score + scoreWord(hit[WordNode.LENGTH])

          new_sequence = sequence + [hit[WordNode.EXTENDED_FORM]]
          self.newChild(new_sequence, new_score)

    # add an extra character to see if we have matches. perhaps only do this if we have no hits

    if not has_hits:
      char = processor.word[length]
      new_sequence = sequence + [char]
      new_score = (self.score * 0.2) - 140
      self.newChild(new_sequence, new_score)

  def newChild(self, new_sequence, base_score):
    # add extra point for filling up sentence
    # print(new_sequence, base_score)
    self.children.append(WordNode(self.processor, new_sequence, base_score))

  def calc_length(self):
    cnt = 0
    for token in self.sequence:
      cnt += len(token)
    return cnt

class Processor(object):

  idx2forms = []
  base2idx = {}
  extended2idx = {}

  solveCache = {}

  def __init__(self, word):
    self.solves = []
    self.word = word

  def process(self):
    if self.word == '':
      return []

    if self.word in Processor.solveCache:
      # print('cache hit "' + self.word + '"')
      return Processor.solveCache[self.word]

    # print('new word up "' + self.word + '"')

    self.hits = self.partitionWord(self.word)
    # pprint(self.hits)

    if len(self.hits) == 0:
      return self.word

    WordNode(self, [], 1)

    self.solves.sort(key=lambda x:x[1])
    self.solves.reverse()

    # print(self.solves[0:20])

    solve = self.solves[0][0]
    Processor.solveCache[self.word] = solve
    return solve

  def addSolve(self, sequence):
    self.solves.append(sequence)

  def partitionWord(self, word):

    hits = []

    for i in range(0,len(word)):
      for j in range(len(word), i, -1):
        if abs(i-j) < 2:
          continue
        sub_token = word[i:j]
        # print('i/j',i,j)
        # print (sub_token)
        if sub_token in Processor.extended2idx:
          base, extended = Processor.idx2forms[Processor.extended2idx[sub_token]]
          bingo = False
          ending = ''
          # Mark as bonus word
          if len(base) < len(extended) and extended.startswith(base):
            bingo = True
            ending = extended.replace(base,"")

          hits.append([i, j - 1, abs(i-j), bingo, base, extended, ending, bingo])
          # print('-', token[0:i])

    return hits


  print("Loading morphemes")
  with open(os.path.join('../corpus', 'fullform_bm.txt'), 'r', encoding="utf-8") as f:
    for line in f:
      columns = line.split("\t")

      if len(columns) > 2:
        base = columns[1]
        extended = columns[2]
        idx2forms.append([base, extended])
        base2idx[base] = len(idx2forms) - 1
        extended2idx[extended] = len(idx2forms) -1
