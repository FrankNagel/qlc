#TODO add trill and central for ASJP!?!?
import re
Infinity = float('inf')

multivalued_features = {
    'place': {
        'bilabial': 100,
		'labiodental': 95,
		'dental': 90,
		'alveolar': 85,
		'retroflex': 80,
		'palato-alveolar': 75,
		'palatal': 70,
		'velar': 60,
		'uvular': 50,
		'pharyngeal': 30,
		'glottal': 10
    },
	'manner': {
        'stop': 100,
		'affricate': 90,
		'fricative': 80,
		'approximant': 60,
        'trill': 50,
        'vowel': 40,
		'high vowel': 40,
		'mid vowel': 20, 
		'low vowel': 0
    },
	'high': {
        'high': 100,
		'mid': 50,
		'low': 0
    },
	'back': {
        'front': 100,
		'central': 50,
		'back': 0
    }
}
        
asjp_letters = {
    'i': {
        'manner': multivalued_features['manner']['high vowel'],
        'high': multivalued_features['high']['high'],
        'back': multivalued_features['back']['front'],
        'vowel': 1,
        'syllabic': 100
    },
    'e': {
        'manner': multivalued_features['manner']['mid vowel'],
        'high': multivalued_features['high']['mid'],
        'back': multivalued_features['back']['front'],
        'vowel': 1,
        'syllabic': 100
    },
    'E': {'manner': multivalued_features['manner']['low vowel'],
          'high': multivalued_features['high']['low'],
          'back': multivalued_features['back']['front'],
          'vowel': 1,
          'syllabic': 100
          },
    '3': {'manner': multivalued_features['manner']['high vowel'],
          'high': multivalued_features['high']['high'],
          'back': multivalued_features['back']['central'],
          'vowel': 1,
          #'central': 100
          },
    'a': {'manner': multivalued_features['manner']['low vowel'],
          'high': multivalued_features['high']['low'],
          'back': multivalued_features['back']['central'],
          'vowel': 1,
          'syllabic': 100
          },
    'u': {'manner': multivalued_features['manner']['high vowel'],
          'high': multivalued_features['high']['high'],
          'back': multivalued_features['back']['back'],
          'vowel': 1,
          'syllabic': 100
          },
    'o': {'manner': multivalued_features['manner']['mid vowel'],
          'high': multivalued_features['high']['mid'],
          'back': multivalued_features['back']['back'],
          'vowel': 1,
          'syllabic': 100
          },
    'p': {'place': multivalued_features['place']['bilabial'],
          'manner': multivalued_features['manner']['stop'],
          'syllabic': 0,
          'voice': 0, 
          'nasal': 0,
          'retroflex': 0,
          'lateral': 0
          },
    'b': {'place': multivalued_features['place']['bilabial'],
          'manner': multivalued_features['manner']['stop'],
          'syllabic': 0,
          'voice': 100, 
          'nasal': 0,
          'retroflex': 0,
          'lateral': 0
          },
    'm': {'place': multivalued_features['place']['bilabial'],
          'manner': multivalued_features['manner']['stop'],
          'syllabic': 0,
          'voice': 100, 
          'nasal': 100,
          'retroflex': 0,
          'lateral': 0 
          },
    'f': {'place': multivalued_features['place']['labiodental'],
          'manner': multivalued_features['manner']['fricative'],
          'syllabic': 0,
          'voice': 0, 
          'nasal': 0,
          'retroflex': 0,
          'lateral': 0
          },
    'v': {'place': multivalued_features['place']['labiodental'],
          'manner': multivalued_features['manner']['fricative'],
          'syllabic': 0,
          'voice': 100, 
          'nasal': 0,
          'retroflex': 0,
          'lateral': 0
          },
    '8': {'place': multivalued_features['place']['dental'],
          'manner': multivalued_features['manner']['fricative'],
          'syllabic': 0,
          'voice': 0,
          'nasal': 0,
          'retroflex': 0,
          'lateral': 0
          },
    '4': {'place': multivalued_features['place']['dental'],
          'manner': multivalued_features['manner']['stop'],
          'syllabic': 0,
          'voice': 100,
          'nasal': 100,
          'retroflex': 0,
          'lateral': 0
          },
    't': {'place': multivalued_features['place']['alveolar'],
          'manner': multivalued_features['manner']['stop'],
          'syllabic': 0,
          'voice': 0, 
          'nasal': 0,
          'retroflex': 0,
          'lateral': 0
          },
    'd': {'place': multivalued_features['place']['alveolar'],
          'manner': multivalued_features['manner']['stop'],
          'syllabic': 0,
          'voice': 100, 
          'nasal': 0,
          'retroflex': 0,
          'lateral': 0
          },
    's': {'place': multivalued_features['place']['alveolar'],
          'manner': multivalued_features['manner']['fricative'],
          'syllabic': 0,
          'voice': 0, 
          'nasal': 0,
          'retroflex': 0,
          'lateral': 0
          },
    'z': {'place': multivalued_features['place']['alveolar'],
          'manner': multivalued_features['manner']['fricative'],
          'syllabic': 0,
          'voice': 100, 
          'nasal': 0,
          'retroflex': 0,
          'lateral': 0
          },
    'c': {'place': multivalued_features['place']['alveolar'],
          'manner': multivalued_features['manner']['affricate'],
          'syllabic': 0,
          'voice': 0, 
          'nasal': 0,
          'retroflex': 0,
          'lateral': 0
          },
    'n': {'place': multivalued_features['place']['alveolar'],
          'manner': multivalued_features['manner']['stop'],
          'syllabic': 0,
          'voice': 100,
          'nasal': 100,
          'retroflex': 0,
          'lateral': 0
          },
    'S': {'place': multivalued_features['place']['palato-alveolar'],
          'manner': multivalued_features['manner']['fricative'],
          'syllabic': 0,
          'voice': 0,
          'nasal': 0,
          'retroflex': 0,
          'lateral': 0
          },
    'Z': {'place': multivalued_features['place']['palato-alveolar'],
          'manner': multivalued_features['manner']['fricative'],
          'syllabic': 0,
          'voice': 100,
          'nasal': 0,
          'retroflex': 0,
          'lateral': 0
          },
    'C': {'place': multivalued_features['place']['palato-alveolar'],
          'manner': multivalued_features['manner']['affricate'],
          'syllabic': 0,
          'voice': 0,
          'nasal': 0,
          'retroflex': 0,
          'lateral': 0
          },
    'j': {'place': multivalued_features['place']['palato-alveolar'],
          'manner': multivalued_features['manner']['affricate'],
          'syllabic': 0,
          'voice': 100,
          'nasal': 0,
          'retroflex': 0,
          'lateral': 0
          },
    'T': {'place': multivalued_features['place']['palatal'],
          'manner': multivalued_features['manner']['stop'],
          'syllabic': 0,
          'voice': 0,
          'nasal': 0,
          'retroflex': 0,
          'lateral': 0
          },
    '5': {'place': multivalued_features['place']['palatal'],
          'manner': multivalued_features['manner']['stop'],
          'syllabic': 0,
          'voice': 100,
          'nasal': 100,
          'retroflex': 0,
          'lateral': 0
          },
    'k': {'place': multivalued_features['place']['velar'],
          'manner': multivalued_features['manner']['stop'],
          'syllabic': 0,
          'voice': 0,
          'nasal': 0,
          'retroflex': 0,
          'lateral': 0
          },
    'g': {'place': multivalued_features['place']['velar'],
          'manner': multivalued_features['manner']['stop'],
          'syllabic': 0,
          'voice': 0,
          'nasal': 0,
          'retroflex': 0,
          'lateral': 0
          },
    'x': {'place': multivalued_features['place']['velar'],
          'manner': multivalued_features['manner']['fricative'],
          'syllabic': 0,
          'voice': 0,
          'nasal': 0,
          'retroflex': 0,
          'lateral': 0
          },
    'N': {'place': multivalued_features['place']['velar'],
          'manner': multivalued_features['manner']['stop'],
          'syllabic': 0,
          'voice': 100,
          'nasal': 100,
          'retroflex': 0,
          'lateral': 0
          },
    'q': {'place': multivalued_features['place']['uvular'],
          'manner': multivalued_features['manner']['stop'],
          'syllabic': 0,
          'voice': 0,
          'nasal': 0,
          'retroflex': 0,
          'lateral': 0
          },
    'G': {'place': multivalued_features['place']['uvular'],
          'manner': multivalued_features['manner']['stop'],
          'syllabic': 0,
          'voice': 100,
          'nasal': 0,
          'retroflex': 0,
          'lateral': 0
          },
    'X': {'place': multivalued_features['place']['uvular'],
          'manner': multivalued_features['manner']['fricative'],
          'syllabic': 0,
          'voice': 100,
          'nasal': 0,
          'retroflex': 0,
          'lateral': 0
          },
    '7': {'place': multivalued_features['place']['glottal'],
          'manner': multivalued_features['manner']['stop'],
          'syllabic': 0,
          'voice': 0,
          'nasal': 0,
          'retroflex': 0,
          'lateral': 0
          },
    'h': {'place': multivalued_features['place']['glottal'],
          'manner': multivalued_features['manner']['fricative'],
          'syllabic': 0,
          'voice': 0,
          'nasal': 0,
          'retroflex': 0,
          'lateral': 0
          },
    'l': {'place': multivalued_features['place']['alveolar'],
          'manner': multivalued_features['manner']['approximant'],
          'syllabic': 0,
          'voice': 100,
          'nasal': 0,
          'retroflex': 0,
          'lateral': 1
          },
    'L': {'place': multivalued_features['place']['velar'],
          'manner': multivalued_features['manner']['approximant'],
          'syllabic': 0,
          'voice': 100,
          'nasal': 0,
          'retroflex': 0,
          'lateral': 1
          },
    'w': {'place': multivalued_features['place']['velar'],
          'manner': multivalued_features['manner']['approximant'],
          'syllabic': 0,
          'voice': 100,
          'nasal': 0,
          'retroflex': 0,
          'lateral': 0,
          'round': 1
          },
    'y': {'place': multivalued_features['place']['palatal'],
          'manner': multivalued_features['manner']['approximant'],
          'syllabic': 0,
          'voice': 100,
          'nasal': 0,
          'retroflex': 0,
          'lateral': 0
          },
    'r': {'place': multivalued_features['place']['alveolar'],
          'manner': multivalued_features['manner']['approximant'],
          'syllabic': 0,
          'voice': 100,
          'nasal': 0,
          'retroflex': 100,
          'lateral': 0,
          #'trill': 1
          }
}
                
                
asjp_modifiers = {}
                       
aline_letters = {
    'a': {'place': multivalued_features['place']['velar'],
          'manner': multivalued_features['manner']['vowel'],
	      'high': multivalued_features['high']['low'],
	      'back': multivalued_features['back']['central'],
          'vowel': 1,
	      'round': 0,
	      'syllabic': 100,
	      'voice': 100, 
	      'nasal': 0,
	      'retroflex': 0,
	      'lateral': 0},
    'b': {'place': multivalued_features['place']['bilabial'],
       'manner': multivalued_features['manner']['stop'],
       'syllabic': 0,
       'voice': 100, 
       'nasal': 0,
       'retroflex': 0,
       'lateral': 0},
    'c': {'place': multivalued_features['place']['alveolar'],
       'manner': multivalued_features['manner']['affricate'],
       'syllabic': 0,
       'voice': 0, 
       'nasal': 0,
       'retroflex': 0,
       'lateral': 0},
    'd': {'place': multivalued_features['place']['alveolar'],
       'manner': multivalued_features['manner']['stop'],
       'syllabic': 0,
       'voice': 100, 
       'nasal': 0,
       'retroflex': 0,
       'lateral': 0},
    'e': {'place': multivalued_features['place']['palatal'],
       'manner': multivalued_features['manner']['vowel'],
       'high': multivalued_features['high']['mid'],
       'back': multivalued_features['back']['front'],
               'vowel': 1,
       'round': 0,
       'syllabic': 100,
       'voice': 100, 
       'nasal': 0,
       'retroflex': 0,
       'lateral': 0},
    'f': {'place': multivalued_features['place']['labiodental'],
       'manner': multivalued_features['manner']['fricative'],
       'syllabic': 0,
       'voice': 0, 
       'nasal': 0,
       'retroflex': 0,
       'lateral': 0},
    'g': {'place': multivalued_features['place']['velar'],
       'manner': multivalued_features['manner']['stop'],
       'syllabic': 0,
       'voice': 100, 
       'nasal': 0,
       'retroflex': 0,
       'lateral': 0},
    'h': {'place': multivalued_features['place']['glottal'],
       'manner': multivalued_features['manner']['fricative'],
       'syllabic': 0,
       'voice': 0, 
       'nasal': 0,
       'retroflex': 0,
       'lateral': 0},
    'i': {'place': multivalued_features['place']['palatal'],
       'manner': multivalued_features['manner']['vowel'],
       'high': multivalued_features['high']['high'],
       'back': multivalued_features['back']['front'],
               'vowel': 1,
       'round': 0,   
       'syllabic': 100,
       'voice': 100, 
       'nasal': 0,
       'retroflex': 0,
       'lateral': 0},
    'j': {'place': multivalued_features['place']['alveolar'],
       'manner': multivalued_features['manner']['affricate'],
       'syllabic': 0,
       'voice': 100, 
       'nasal': 0,
       'retroflex': 0,
       'lateral': 0},
    'k': {'place': multivalued_features['place']['velar'],
       'manner': multivalued_features['manner']['stop'],
       'syllabic': 0,
       'voice': 0, 
       'nasal': 0,
       'retroflex': 0,
       'lateral': 0},
    'l': {'place': multivalued_features['place']['alveolar'],
       'manner': multivalued_features['manner']['approximant'],
       'syllabic': 0,
       'voice': 100, 
       'nasal': 0,
       'retroflex': 0,
       'lateral': 100},
    'm': {'place': multivalued_features['place']['bilabial'],
       'manner': multivalued_features['manner']['stop'],
       'syllabic': 0,
       'voice': 100, 
       'nasal': 100,
       'retroflex': 0,
       'lateral': 0},
    'n': {'place': multivalued_features['place']['alveolar'],
       'manner': multivalued_features['manner']['stop'],
       'syllabic': 0,
       'voice': 100, 
       'nasal': 100,
       'retroflex': 0,
       'lateral': 0},
    'o': {'place': multivalued_features['place']['velar'],
       'manner': multivalued_features['manner']['vowel'],
       'high': multivalued_features['high']['mid'],
       'back': multivalued_features['back']['back'],
               'vowel': 1,
       'round': 100,
       'syllabic': 100,
       'voice': 100, 
       'nasal': 0,
       'retroflex': 0,
       'lateral': 0},
    'p': {'place': multivalued_features['place']['bilabial'],
       'manner': multivalued_features['manner']['stop'],
       'syllabic': 0,
       'voice': 0, 
       'nasal': 0,
       'retroflex': 0,
       'lateral': 0},
    'q': {'place': multivalued_features['place']['glottal'],
       'manner': multivalued_features['manner']['stop'],
       'syllabic': 0,
       'voice': 0, 
       'nasal': 0,
       'retroflex': 0,
       'lateral': 0},
    'r': {'place': multivalued_features['place']['retroflex'],
       'manner': multivalued_features['manner']['approximant'],
       'syllabic': 0,
       'voice': 100, 
       'nasal': 0,
       'retroflex': 100,
       'lateral': 0},
    's': {'place': multivalued_features['place']['alveolar'],
       'manner': multivalued_features['manner']['fricative'],
       'syllabic': 0,
       'voice': 0, 
       'nasal': 0,
       'retroflex': 0,
       'lateral': 0},
    't': {'place': multivalued_features['place']['alveolar'],
       'manner': multivalued_features['manner']['stop'],
       'syllabic': 0,
       'voice': 0, 
       'nasal': 0,
       'retroflex': 0,
       'lateral': 0},
    'u': {'place': multivalued_features['place']['velar'],
       'manner': multivalued_features['manner']['vowel'],
       'high': multivalued_features['high']['high'],
       'back': multivalued_features['back']['back'],
               'vowel': 1,
       'round': 100,
       'syllabic': 100,
       'voice': 100, 
       'nasal': 0,
       'retroflex': 0,
       'lateral': 0},
    'v': {'place': multivalued_features['place']['labiodental'],
       'manner': multivalued_features['manner']['fricative'],
       'syllabic': 0,
       'voice': 100, 
       'nasal': 0,
       'retroflex': 0,
       'lateral': 0},
    'w': {'place': (multivalued_features['place']['velar'], multivalued_features['place']['bilabial']),
       'manner': multivalued_features['manner']['vowel'],
       'high': multivalued_features['high']['high'],
       'back': multivalued_features['back']['back'],
               'vowel': 1,
       'round': 100,
       'syllabic': 0,
       'voice': 100, 
       'nasal': 0,
       'retroflex': 0,
       'lateral': 0},
    'x': {'place': multivalued_features['place']['velar'],
       'manner': multivalued_features['manner']['fricative'],
       'syllabic': 0,
       'voice': 0, 
       'nasal': 0,
       'retroflex': 0,
       'lateral': 0},
    'y': {'place': multivalued_features['place']['palatal'],
       'manner': multivalued_features['manner']['vowel'],
       'high': multivalued_features['high']['high'],
       'back': multivalued_features['back']['front'],
               'vowel': 1,
       'round': 0,
       'syllabic': 0,
       'voice': 100, 
       'nasal': 0,
       'retroflex': 0,
       'lateral': 0},
    'z': {'place': multivalued_features['place']['alveolar'],
       'manner': multivalued_features['manner']['fricative'],
       'syllabic': 0,
       'voice': 100, 
       'nasal': 0,
       'retroflex': 0,
       'lateral': 0}
}

aline_modifiers = {'A': {'feature': 'aspirated',
			 'value': 100},
		   'B': {'feature': 'back',
			 'value': multivalued_features['back']['back']},
		   'C': {'feature': 'back',
			 'value': multivalued_features['back']['central']},
		   'D': {'feature': 'place',
			 'value': multivalued_features['place']['dental']},
		   'F': {'feature': 'back',
			 'value': multivalued_features['back']['front']},
		   'H': {'feature': 'long',
			 'value': 100},
		   'N': {'feature': 'nasal',
			 'value': 100},
		   'P': {'feature': 'place',
			 'value': multivalued_features['place']['palatal']},
		   'R': {'feature': 'round',
			 'value': 100},
		   'S': {'feature': 'manner',
			 'value': multivalued_features['manner']['fricative']},
		   'V': {'feature': 'place',
			 'value': multivalued_features['place']['palato-alveolar']}
		   }


class MatrixRow(object):
    def __init__(self, row_length):
        self.row = [ 0 for i in range(row_length)]
        
    def __getitem__(self, index):
        if index < 0:
            return -Infinity
        else:
            return self.row[index]
        
    def __setitem__(self, index, value):
        if index >= 0:
            self.row[index] = value

    def __iter__(self):
        for y in self.row:
            yield y

class Matrix(object):
    def __init__(self, x, y, output_type=None):
        self.rows = []
        self.x_length = x
        self.y_length = y
        for i in range(self.x_length):
            self.rows.append(MatrixRow(self.y_length))
        self.output_type = output_type
            
    def __repr__(self):
        out_string = ""
        if self.output_type == 'r':
            out_string = "c("
        for x in range(self.x_length):
            for y in range(self.y_length):
                if self.output_type == 'r':
                    out_string += "%s, " % self.rows[x][y]
                else:
                    out_string += "%s " % self.rows[x][y]
            out_string = out_string.strip() + "\n"
        out_string = out_string.strip()
        if self.output_type == 'r':
            out_string = re.sub(',$', ')', out_string)
        return out_string

    def __getitem__(self, index):
        if index < 0:
            return [ -Infinity for y in range(self.y_length) ]
        else:
            return self.rows[index]

    def __iter__(self):
        for x in self.rows:
            yield x

    def getX(self):
        return self.x_length

    def getY(self):
        return self.y_length

class AlineMatrix(Matrix):
    def __init__(self, x, y, output_type=None):
        self.x = x
        self.y = y
        super(AlineMatrix, self).__init__(len(x) + 1, len(y) + 1, output_type)

    def __repr__(self):
        out_string = super(AlineMatrix, self).__repr__()
        out_parts = out_string.split("\n")
        # how much space we need for each letter on the y axis
        space = max([len(x['input_string']) for x in self.y]) + 1 

        top_line = " " * (space + 2)
        for i in self.x:
            top_line += i['input_string'] + " "
        new_array = [top_line]
        index = 0

        for j in out_parts:
            if index > 0:
                j = self.y[index]['input_string'] + " " * (space - (len(self.y[index]['input_string']))) + j 
            else:
                j = " " * space + j
            new_array.append(j)
            index += 1
        new_out_string = "\n".join(new_array)
        return new_out_string 
    
