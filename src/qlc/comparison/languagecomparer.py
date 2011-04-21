# -*- coding: utf-8 -*-

import aline
#from pyaline import Aline, AlineRepr
#from util import Matrix, Infinity
import numpy
import sys

class LanguageComparer(object):
    def __init__(self, languages, input_string_type, divided = False):
        self.__languages = languages
        self.__names = self.__languages.keys()
        self.__matrix = None
        self.__input_string_type = input_string_type
        self.__divided = divided

    def compare_individual_languages(self, x, y):
        return "%s,%s\t%s" % (x, y, self.__compare_languages(self.__languages[self.__names[x]], self.__languages[self.__names[y]]))

    def generate_matrix(self):
        if self.__matrix == None:
            self.__matrix = numpy.empty( (len(self.__names), len(self.__names)) )
            for i in xrange(len(self.__names)):
                #if i % 5 == 0:
                self.__matrix[i][i] = 0.0
                for j in xrange(i+1, len(self.__names)):
                    sys.stderr.write("language count: %s,%s\n" % (i, j))

                    self.__matrix[i][j] = self.__matrix[j][i] = self.__compare_languages(self.__languages[self.__names[i]], self.__languages[self.__names[j]])
                    if self.__matrix[i][j] == 0 or self.__matrix[j][i] == 0:
                        sys.stderr.write("got 0 for %s and %s\n" % (self.__names[i], self.__names[j]))
            self.__column_names = self.__names
        #print "%s" % (self.__column_names,)
        #print "%s" % (self.__matrix,)
        #print self.__matrix

    @property
    def column_names(self):
        return self.__column_names
        
    @property
    def matrix(self):
        return self.__matrix

    def __str__(self):
        return self.__matrix.__str__()
        
    def __normalize_asjp_string(self, x):
        if x.find("//") != -1:
            parts = x.split("//")
            return parts[0]
        else:
            return x
        
    def __parse_lexemes(self, string):
        results = string.split("|")
        return [ aline.AlineRepr(self.__normalize_asjp_string(x), self.__input_string_type) for x in results ]

    def __compare_languages(self, x, y):
        sum = 0
        count = 0
        for i in xrange(len(x)):
            #sys.stderr.write("First i: %i\n" % (i, ))
            if (x[i] == "") or (y[i] == ""):
                continue
            x_strings = self.__parse_lexemes(x[i])
            y_strings = self.__parse_lexemes(y[i])
            try:
                sum += min(aline.Aline(x_string, y_string).get_distance() for x_string in x_strings for y_string in y_strings)
            except ZeroDivisionError:
                sys.stderr.write("ZeroDision! initial sum i: %s x_strings: %s y_strings: %s\n" % (i, x_strings, y_strings))
            count += 1
        if self.__divided:
            dividend = float(sum)/float(count)
            divisor_sum = 0
            divisor_count = 0
            for i in xrange(len(x)):
                for j in xrange(len(y)):
                    #sys.stderr.write("i: %s j: %s\n" % (i, j))
                    if i == j or (x[i] == "") or (y[j] == ""):
                        continue
                    else:
                        x_strings = self.__parse_lexemes(x[i])
                        y_strings = self.__parse_lexemes(y[j])
                        try:
                            divisor_sum += min(aline.Aline(x_string, y_string).get_distance() for x_string in x_strings for y_string in y_strings)
                        except ZeroDivisionError:
                            sys.stderr.write("ZeroDision! initial sum i: %s i: %s j: %s x[i]: %s y[j]: %s x_strings: %s y_strings: %s\n" % (i, i, j, x[i], y[j], x_strings, y_strings))
                        divisor_count += 1
            divisor = float(divisor_sum) / float(divisor_count)
            return float(dividend) / float(divisor)
        else:
            return float(sum)/float(count)

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
        string_type = aline.ASJP
    else:
        string_type = aline.ALINE
    if not options.filename:
        print "Filename required."
        sys.exit(0)
    import csv
    words = csv.reader(open(options.filename), quoting=csv.QUOTE_NONE, delimiter="\t")
    if options.header:
        words.next()
    languages = {}
    for row in words:
        if options.asjp:
            languages[row[1]] = row[3:]
        else:
            languages[row[0]] = row[1:]

    x = LanguageComparer(languages, string_type, True if options.divided else False)
    if options.individual:
        x.compare_individual_languages(0, 1)
    else:
        x.generate_matrix()
        print x.matrix
        
