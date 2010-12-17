

import os
import re

with open('/Users/cysouw/Desktop/test.txt') as f:
	data = f.read()

# error corrections
data = re.sub(' # #',' #',data)
data = re.sub('\. \[','# ',data)
data = re.sub('# n#\n','',data)

data = re.sub(' #\n# | # ',' . ',data)
data = re.sub('# | #\n','',data)
data_nounderline = re.sub('̱','',data)

graphemes = re.split(' ',re.sub(' \.','',data_nounderline))
syllables = re.split('\.',re.sub(' ','',data_nounderline))

set(graphemes)
set(syllables)
