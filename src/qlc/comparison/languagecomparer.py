# -*- coding: utf-8 -*-

import aline
import numpy
import sys


class LanguageComparer(object):
    def __init__(self, data, input_string_type, divided = False):
        self.__data = data
        self.__nr_of_languages = len(data)
        self.__matrix = None
        self.__input_string_type = input_string_type
        self.__divided = divided

    def compare_individual_languages(self, x, y):
        return "%s,%s\t%s" % (x, y, self.__compare_languages(self.__data[x], self.__data[y]))

    def generate_matrix(self):
        if self.__matrix == None:
            self.__matrix = numpy.zeros( (self.__nr_of_languages, self.__nr_of_languages) )
            for i in xrange(self.__nr_of_languages):
                for j in xrange(i+1, self.__nr_of_languages):
                    sys.stderr.write("language count: %s,%s\n" % (i, j))
                    
                    self.__matrix[i][j] = self.__matrix[j][i] = self.__compare_languages(self.__data[i], self.__data[j])
                    if self.__matrix[i][j] == 0 or self.__matrix[j][i] == 0:
                        sys.stderr.write("got 0 for %i and %i\n" % (i, j))
        
    @property
    def matrix(self):
        return self.__matrix

    def __str__(self):
        return self.__matrix.__str__()
        
    def __aline_repr(self, string):
        return aline.AlineRepr(string, self.__input_string_type)
        
    def __compare_languages(self, x, y):
        sum = 0
        count = 0
        for i in xrange(len(x)):
            if len(x[i]) == 0 or len(y[i]) == 0:
                continue
            try:
                sum += min(
                    aline.Aline(self.__aline_repr(x_string),
                                self.__aline_repr(y_string)).get_distance()
                    for x_string in x[i] for y_string in y[i])
            except ZeroDivisionError:
                sys.stderr.write("ZeroDision! initial sum i: %s x_strings: %s y_strings: %s\n" % (i, x[i], y[i]))

            #print x[i]
            #print y[i]
            #print sum
            #print
            
            count += 1
        if self.__divided:
            dividend = float(sum)/float(count)
            divisor_sum = 0
            divisor_count = 0
            for i in xrange(len(x)):
                for j in xrange(len(y)):
                    if i == j or len(x[i]) == 0 or len(y[j]) == 0:
                        continue
                    else:
                        try:
                            divisor_sum += min(
                                aline.Aline(self.__aline_repr(x_string),
                                            self.__aline_repr(y_string)).get_distance()
                                for x_string in x[i] for y_string in y[j])
                        except ZeroDivisionError:
                            sys.stderr.write("ZeroDision! initial sum i: %s i: %s j: %s x[i]: %s y[j]: %s\n" % (i, i, j, x[i], y[j]))
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
        
