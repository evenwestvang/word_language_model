import re
from word import Processor

end_of_sentence = re.compile('\!|\.|\?|~|\n')
whitespace = re.compile('\s')
nonAlphaNumeric = re.compile('\W')

def intersperse(lst, item):
    result = [item] * (len(lst) * 2 - 1)
    result[0::2] = lst
    return result

def split_line_sentences_words(line):
  lastWord = 0
  sentences = []
  sentence = []
  # convert to sentences

  def addWord(word):
    word_array = Processor(word).process()
    return intersperse(word_array, '+')

  # print(line)

  for i in range(len(line)):
    char = line[i]
    if whitespace.search(char):
      sentence += addWord(line[lastWord:i])
      lastWord = i + 1
    elif end_of_sentence.search(char):
      # if i < len(line) -1 and whitespace.search(line[i + 1]):
      sentence += addWord(line[lastWord:i])
      sentence.append(char)
      sentences.append(list(filter(None, sentence)))
      lastWord = i + 1
      sentence = []
    elif nonAlphaNumeric.search(char):
      if lastWord < i:
        sentence += addWord(line[lastWord:i])
      sentence.append(char)
      lastWord = i + 1

  # print ('sentences:', sentences)

  return sentences


if __name__ == "__main__":

  sample_words = ['oversende', 'bussbransjeavtalen', 'akkurat', 'sjåførene', 'flyplass', 'flyplassen', 'flyplassentusiastene', 'sinnsforvirring', 'urbefolkning', 'pengegrisk', 'fornærmer', 'veiutbygging', 'undervisning', 'diskriminerende', 'byggetid']

  for word in sample_words:
    split_line_sentences_words(word + '\n')
