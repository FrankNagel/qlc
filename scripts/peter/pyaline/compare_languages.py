#!/usr/bin/env python

from pyaline import Aline, ASJPString, AlineString
from util import Matrix, Infinity
import sys

class LanguageComparer(object):
    def __init__(self, languages, language_names, string_class, divided = False):
        self.languages = languages
        self.names = language_names
        self.matrix = None
        self.string_class = string_class
        self.divided = divided

    def generate_matrix(self):
        if self.matrix == None:
            self.matrix = Matrix(len(self.names), len(self.names))
            for i in xrange(len(self.names)):
                #if i % 5 == 0:
                self.matrix[i][i] = 0.0
                for j in xrange(i+1, len(self.names)):
                    sys.stderr.write("language count: %s,%s\n" % (i, j))
                    self.matrix[i][j] = self.matrix[j][i] = self.compare_languages(self.languages[self.names[i]], self.languages[self.names[j]])
                    if self.matrix[i][j] == 0 or self.matrix[j][i] == 0:
                        sys.stderr.write("got 0 for %s and %s\n" % (self.names[i], self.names[j]))
            self.column_names = " ".join(self.names)
        print "%s" % (self.column_names,)
        print "%s" % (self.matrix,)
                    
    def normalize_asjp_string(self, x):
        if x.find("//") != -1:
            parts = x.split("//")
            return parts[0]
        else:
            return x
        
    def parse_lexemes(self, string):
        results = string.split("|")
        return [ self.string_class(self.normalize_asjp_string(x)) for x in results ]

    def compare_languages(self, x, y):
        sum = 0
        count = 0
        for i in xrange(len(x)):
            #sys.stderr.write("First i: %i\n" % (i, ))
            if (x[i] == "") or (y[i] == ""):
                continue
            x_strings = self.parse_lexemes(x[i])
            y_strings = self.parse_lexemes(y[i])
            try:
                sum += min(Aline(x_string, y_string).get_distance() for x_string in x_strings for y_string in y_strings)
            except ZeroDivisionError:
                sys.stderr.write("ZeroDision! initial sum i: %s x_strings: %s y_strings: %s\n" % (i, x_strings, y_strings))
                
            print x[i]
            print y[i]
            print x_strings
            print y_strings
            print sum
            print

            count += 1
        if self.divided:
            dividend = float(sum)/float(count)
            divisor_sum = 0
            divisor_count = 0
            for i in xrange(len(x)):
                for j in xrange(len(y)):
                    #sys.stderr.write("i: %s j: %s\n" % (i, j))
                    if i == j or (x[i] == "") or (y[j] == ""):
                        continue
                    else:
                        x_strings = self.parse_lexemes(x[i])
                        y_strings = self.parse_lexemes(y[j])
                        try:
                            divisor_sum += min(Aline(x_string, y_string).get_distance() for x_string in x_strings for y_string in y_strings)
                        except ZeroDivisionError:
                            sys.stderr.write("ZeroDision! initial sum i: %s i: %s j: %s x[i]: %s y[j]: %s x_strings: %s y_strings: %s\n" % (i, i, j, x[i], y[j], x_strings, y_strings))
                        divisor_count += 1
            divisor = float(divisor_sum) / float(divisor_count)
            return float(dividend) / float(divisor)
        else:
            return float(sum)/float(count)
    
    def compare_individual_languages(self, x, y):
        return "%s,%s\t%s" % (x, y, self.compare_languages(self.languages[self.names[x]], self.languages[self.names[y]]))
                

if __name__ == "__main__":
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("-f", "--file", dest="filename")
    parser.add_option("-a", "--asjp", action="store_true", dest="asjp")
    parser.add_option("-i", "--individual", action="store_true", dest="individual")
    parser.add_option("-e", "--header", action="store_true", dest="header")
    parser.add_option("-d", "--divided", action="store_true", dest="divided")
    (options, args) = parser.parse_args()
    if options.asjp:
        string_class = ASJPString
    else:
        string_class = AlineString
    if not options.filename:
        print "Filename required."
        sys.exit(0)
    import csv
    words = csv.reader(open(options.filename), quoting=csv.QUOTE_NONE, delimiter="\t")
    if options.header:
        words.next()
    languages = {}
    language_names = []
    for row in words:
        if options.asjp:
            languages[row[0]] = row[3:]
        else:
            languages[row[0]] = row[1:]
        language_names.append(row[0])

    x = LanguageComparer(languages, language_names, string_class, True if options.divided else False)
    if options.individual:
        x.compare_individual_languages(0, 1)
    else:
        x.generate_matrix()
