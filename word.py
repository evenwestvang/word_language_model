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
      self.score *= len(self.sequence)

      processor.addSolve([self.sequence, self.score])
      return
    else:
      self.done = False

    has_hits = False
    for hit in processor.hits:

      has_hits = True

      if hit[WordNode.START] == length:

        if hit[WordNode.BINGO]:
          # reward longer words with stems
          new_score = self.score + hit[WordNode.LENGTH] ** 2.5
          new_sequence = sequence + [hit[WordNode.BASE_FORM], hit[WordNode.ENDING] ]
          self.newChild(new_sequence, new_score)
        else:
          # penalty for very short sequences

          if hit[WordNode.LENGTH] > 2:
            new_score = self.score + hit[WordNode.LENGTH] ** 2
          else:
            new_score = self.score + hit[WordNode.LENGTH]

          new_sequence = sequence + [hit[WordNode.EXTENDED_FORM]]
          self.newChild(new_sequence, new_score)

    # add an extra character to see if we have matches. perhaps only do this if we have no hits

    if not has_hits:
      char = processor.word[length]
      new_sequence = sequence + [char]
      new_score = self.score - 0.5
      self.newChild(new_sequence, new_score)

  def newChild(self, new_sequence, base_score):
    # add extra point for filling up sentence
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

  def __init__(self, word):
    self.solves = []
    self.word = word

  def process(self):
    if self.word == '':
      return []

    print('word up "' + self.word + '"')

    self.hits = self.partitionWord(self.word)
    WordNode(self, [], 1)

    self.solves.sort(key=lambda x:x[1])
    self.solves.reverse()
    print(self.solves)

  def addSolve(self, sequence):
    self.solves.append(sequence)

  def partitionWord(self, word):

    if len(word) <= 3: return [word]

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

    # pprint (hits)

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
