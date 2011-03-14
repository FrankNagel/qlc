#!/usr/bin/env python
import sys, copy
from util import *
from types import *
from math import log


class AlineString(object):
        def __init__(self, input_string):
            self.input_string = input_string
            self.feature_vector = self._translate_string(input_string)

        def _translate_string(self, input_string):
            output_vector = []
            for i in range(len(input_string)):
                if input_string[i] >= 'a' and input_string[i] <= 'z':
                    output_vector.append(copy.copy(aline_letters[input_string[i]]))
                elif aline_modifiers.has_key(input_string[i]):
                    output_vector[len(output_vector) - 1][aline_modifiers[input_string[i]]['feature']] = aline_modifiers[input_string[i]]['value']
		output_vector[len(output_vector) - 1]["input_string"] = output_vector[len(output_vector) - 1].get("input_string", "") + input_string[i]
            return output_vector

        def get_feature_vector(self):
            return self.feature_vector
	
	def __len__(self):
		return len(self.feature_vector)
	
	def __getitem__(self, index):
            if index >= 1:
		return self.feature_vector[index - 1]
            else:
                return {'null': 1, 'input_string': 'NaS'}
	
	def __repr__(self):
		string = ""
		for i in self.feature_vector:
			string += i['input_string']
		return string
        
        def __iter__(self):
            for i in self.feature_vector:
                yield i


class ASJPString(object):
        def __init__(self, input_string):
		self.input_string = input_string
		self.feature_vector = self._translate_string(input_string)

        def _translate_string(self, input_string):
		output_vector = []
		for i in range(len(input_string)):
			found = False
			if input_string[i] in asjp_letters.keys():
				found = True
				output_vector.append(copy.copy(asjp_letters[input_string[i]]))
			elif asjp_modifiers.has_key(input_string[i]):
				found = True
				output_vector[len(output_vector) - 1][aline_modifiers[input_string[i]]['feature']] = aline_modifiers[input_string[i]]['value']

			if found:
				output_vector[len(output_vector) - 1]["input_string"] = output_vector[len(output_vector) - 1].get("input_string", "") + input_string[i]
		return output_vector

        def get_feature_vector(self):
            return self.feature_vector
	
	def __len__(self):
		return len(self.feature_vector)
	
	def __getitem__(self, index):
            if index >= 1:
		return self.feature_vector[index - 1]
            else:
                return {'null': 1, 'input_string': 'NaS'}
	
	def __repr__(self):
		string = ""
		for i in self.feature_vector:
			string += i['input_string']
		return string

        def __iter__(self):
            for i in self.feature_vector:
                yield i

class Aline(object):
	c_skip = -1000
	c_sub = 3500
	c_exp = 4500
	c_vwl = 1000
	
	r_c = ['syllabic', 'manner', 'voice', 'nasal', 'retroflex', 'lateral', 'aspirated', 'place']
	r_v = ['syllabic', 'nasal', 'retroflex', 'high', 'back', 'round', 'long']

	epsilon = 0

	feature_salience = {'syllabic': 5, 
			    'place': 40, 
			    'manner': 50, 
			    'voice': 10, 
			    'nasal': 10,
			    'retroflex': 10, 
			    'lateral': 10, 
			    'aspirated': 5,
			    'long': 1, 
			    'high': 5, 
			    'back': 5, 
			    'round': 5}

	def __init__(self, x, y, pretty_print = True):
		self.pretty_print = pretty_print
		self.found = False
		self.x = x
		self.y = y
		self.S = None
	
	def sigma_skip(self, p, output = False):
		self.output_func(output, "c_skip: %s" % (self.c_skip, ))
		return self.c_skip
	
	def sigma_sub(self, p, q, output = False):
		self.output_func(output, "c_sub: %s" % (self.c_sub, ))
		s_d = self.delta(p, q, output)
		s_v_p = self.vowel_cost(p, output)
		s_v_q = self.vowel_cost(q, output)
		self.output_func(output, "c_sub: %s s_d: %s s_v_p: %s s_v_q: %s total cost: %d" % (self.c_sub, s_d, s_v_p, s_v_q, self.c_sub - s_d - s_v_p - s_v_q))
		return int(self.c_sub - s_d - s_v_p - s_v_q)
	
	def sigma_exp(self, p, q1, q2, output = False):
		if q1.has_key('null') or q2.has_key('null'):
			return -Infinity
		s_d_p_q1 = self.delta(p, q1)
		s_d_p_q2 = self.delta(p, q2)
		if s_d_p_q1 == 0 or s_d_p_q2 == 0:
			return -Infinity
		return int(self.c_exp - s_d_p_q1 - s_d_p_q2 - self.vowel_cost(p) - max(self.vowel_cost(q1), self.vowel_cost(q2)))
	
	def vowel_cost(self, p, output = False):
		if p.get('vowel', 0) == 1:
			self.output_func(output, "c_vwl: %s" % (self.c_vwl, ))
			return self.c_vwl
		else:
			self.output_func(output, "c_vwl: 0")
			return 0

	def delta(self, p, q, output = False):
		if (p.has_key('vowel') and p['vowel'] == 1) and (q.has_key('vowel') and q['vowel'] == 1):
			self.output_func(output, "delta features: r_v")
			features = self.r_v
		else:
			self.output_func(output, "delta features: r_c")
			features = self.r_c
		out = 0
		for feature in features:
			out += self.diff(p, q, feature, output) * self.feature_salience[feature]
		return out

	def diff(self, p, q, feature, output = False):
		self.output_func(output, "feature: %s p[feature]: %s q[feature]: %s feature_salience: %s" % (feature, p.get(feature, 0), q.get(feature, 0), self.feature_salience[feature]))
		temp = sys.maxint
		p_val = p.get(feature, 0)
		q_val = q.get(feature, 0)
		if type(p_val) is not ListType and type(p_val) is not TupleType:
			p_vals = (p_val, )
		else:
			p_vals = p_val
		if type(q_val) is not ListType and type(q_val) is not TupleType:
			q_vals = (q_val, )
		else:
			q_vals = q_val
		for i in p_vals:
			for j in q_vals:
				if temp > abs(i - j):
					self.output_func(output, "feature %s i: %s j: %s abs(i - j): %s" % (feature, i, j, abs(i - j)))
					temp = abs(i - j)
		self.output_func(output, "feature: %s final temp: %s" % (feature, temp))
		return temp

	def output_func(self, output, string):
		if output:
			print string
			
	
	def compute_similarity(self):
		if self.S is not None:
			return
		self.S = AlineMatrix(self.x, self.y)
		for i in xrange(1, len(self.x) + 1):
			for j in xrange(1, len(self.y) + 1):
				self.S[i][j] = max(self.S[i-1][j] + self.sigma_skip(self.x[i]),
						   self.S[i][j-1] + self.sigma_skip(self.y[j]),
						   self.S[i-1][j-1] + self.sigma_sub(self.x[i], self.y[j]),
						   self.S[i-1][j-2] + self.sigma_exp(self.x[i], self.y[j-1],self.y[j]),
						   self.S[i-2][j-1] + self.sigma_exp(self.y[j], self.x[i-1], self.x[i]),
						   0)


		self.T = (1-self.epsilon) * max([ max(w) for w in self.S ])
		self.out = []
		self.out_score = (max([ max(row) for row in self.S ]) / 100)
		return

	def get_similarity(self):
		if self.S is None:
			self.compute_similarity()
		return self.out_score

	def compute_self_similarity(self):
		if self.x.input_string != self.y.input_string:
			self.self_similarity = -Infinity;
			return
		sum = 0
		for i in xrange(1, len(self.x) + 1):
			sum += self.sigma_sub(self.x[i], self.y[i])
		self.self_similarity = sum / 100
		return

	def get_self_similarity(self):
		# Only meaningful for self comparisons
		self.compute_self_similarity()
		return self.self_similarity

	def get_normalized_similarity(self):
		AlineX = Aline(self.x, self.x)
		AlineY = Aline(self.y, self.y)
		s = self.get_similarity()
		s1 = AlineX.get_self_similarity()
		s2 = AlineY.get_self_similarity()
		return float((2*s))/float((s1+s2))

	def get_distance(self):
		return 1 - self.get_normalized_similarity()

	def get_geographic_distance(self):
		return -1 * log(self.get_normalized_similarity())

	def print_similarity(self):
		self.retrieve_alignment()
		print self.S
		self._print_alignment(self.out)
		print "Similarity score: %s" % (self.get_similarity(), )
		print "Normalized similarity: %s" % (self.get_normalized_similarity(), )
		print "Distance: %s"  % (self.get_distance(), )
		print "Geographic Distance: %s"  % (self.get_geographic_distance(), )
	def retrieve_alignment(self):
		if self.S is None:
			self.compute_similarity()
		for i in range(1, self.S.getX()):
			for j in range(1, self.S.getY()):
				if(self.S[i][j] >= self.T):
					self.retrieve(self.x, self.y, i, j,0)

	def get_alignment(self):
		self.retrieve_alignment()
		return self._format_alignment(self.out)

	def retrieve(self, x, y, i, j, s, out = []):
		output = False
		if self.found == True:
			return
		if(self.S[i][j] == 0):
			self.out = copy.deepcopy(out)
			self.found = True
		else:
			if (i == 0) or (self.S[i-1][j-1] + self.sigma_sub(x[i], y[j], output) + s >= self.T):
				out.append([x[i]['input_string'], y[j]['input_string']])
				self.retrieve(x, y, i-1, j-1, s + self.sigma_sub(x[i], y[j]), out)
				out.pop()
			if self.S[i][j-1] + self.sigma_skip(y[j], output) + s >= self.T:
				out.append(["-", y[j]['input_string']])
				self.retrieve(x, y, i, j-1, s + self.sigma_skip(y[j]), out)
				out.pop()
			if self.S[i-1][j-2] + self.sigma_exp(x[i], y[j-1], y[j]) + s >= self.T:
				out.append([x[i]['input_string'] + " <", y[j-1]['input_string'] + " " + y[j]['input_string']])
				self.retrieve(x, y, i-1, j-2, self.sigma_exp(x[i], y[j-1], y[j]) + s, out)
				out.pop()
			if (j == 0) or (self.S[i-1][j] + self.sigma_skip(x[i], output) + s >= self.T):
				out.append([x[i]['input_string'], "-"])
				self.retrieve(x, y, i-1, j, s + self.sigma_skip(x[i]), out)
				out.pop()
			if self.S[i-2][j-1] + self.sigma_exp(y[j], x[i-1], x[i]) + s >= self.T:
				out.append([x[i-1]['input_string'] + " " + x[i]['input_string'], y[j]['input_string'] + " <"])
				self.retrieve(x, y, i-2, j-1, s + self.sigma_exp(y[j], x[i-1], x[i]), out)
				out.pop()
				
	def _format_alignment(self, alignment):
		alignment.reverse()
		out_string_1 = ""
		out_string_2 = ""
		for align in alignment:
			out_string_1 += align[0] 
			if len(align[1]) > len(align[0]) and self.pretty_print:
				out_string_1 += " " * (abs(len(align[1]) - len(align[0])) + 1)
			else:
				out_string_1 += " "
			out_string_2 += align[1] 
			if len(align[0]) > len(align[1]) and self.pretty_print:
				out_string_2 += " " * (abs(len(align[1]) - len(align[0])) + 1)
			else:
				out_string_2 += " "
		return (out_string_1, out_string_2)
	
	def _print_alignment(self, alignment):
		(out_string_1, out_string_2) =  self._format_alignment(alignment)
		print out_string_1
		print out_string_2



if __name__ == '__main__':
	from optparse import OptionParser
	parser = OptionParser()
	parser.add_option("-f", "--file", dest="filename")
	parser.add_option("-a", "--asjp", action="store_true", dest="asjp")
	(options, args) = parser.parse_args()
	if options.asjp:
		string_class = ASJPString
	else:
		string_class = AlineString
	strings = []
	if options.filename:
		f = open(options.filename, "r")
		for line in f:
			if line.rstrip() != "":
				parts = line.rstrip().split('\t')
				strings.append((parts[0], parts[1]))
				
	else:
		strings.append((args[0], args[1]))

	for string_tuple in strings:
		x = string_class(string_tuple[0])
		y = string_class(string_tuple[1])
		a = Aline(x, y)
		print "%s %s" % (string_tuple[0], string_tuple[1])
		a.print_similarity()

