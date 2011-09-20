# -*- coding: utf-8 -*-

"""
Class to produce matrix data format as input for statistical packages like R.

"""

import operator # python-sort-a-dictionary-by-value

class Matrix(object):
    """ 
    Takes as input a hash of hashes -- language names and their segment inventories and counts:
    
    { language_name: {grapheme:count, grapheme2:count}
      language_name2: {grapheme:count, ...}
      ...
    }

    Returns a 2D matrix where the first row is a unique list of all segments (header)
    and subsequent rows are languages and their segment counts (the data), e.g.:

        a b c d
    lg1 2 1 0 0
    lg2 0 0 1 2
    ...

    """

    def __init__(self, input_hash):
        self.header_hash = {}
        # self.matrix = []
        self.input_hash = input_hash
        # print self.input_hash

        # 1. this code creates the matrix of segment coccurrences and prints it
        # create blank matrix

        self.header_hash = self.getHeader(self.input_hash)
        # print self.header_hash

        # self.matrix = self.createMatrixContainer(self.header_hash)
        # print self.matrix

        self.printMatrix(self.input_hash, self.header_hash)
        

    def getHeader(self, input_hash):
        """
        Create a hash set of segments for the header row
        """
        for k, v in input_hash.iteritems():
            for k2, v2 in input_hash[k].iteritems():
                if not self.header_hash.has_key(k2):
                    self.header_hash[k2] = 1
                else:
                    self.header_hash[k2] += 1
        return self.header_hash

    def createMatrixContainer(self, header_hash):
        """
        Create a container for the 2D matrix
        """
        for i in range(len(header_hash)):
            self.matrix.append([[] for j in range(len(header_hash))])
        return self.matrix


    def printMatrix(self, input_hash, header_hash):
        """
        print a 2D matrix given an input hash set and the header hash set
        """
        # create sorted header and sort it
        header = []

        # sort the header_hash -- returns a list of tuples (k, v)
        sorted_tuples = sorted(header_hash.iteritems(), key=operator.itemgetter(1), reverse=False)
        for i in sorted_tuples:
            header.append(i[0].strip())

        # print the header (first row)
        for i in header:                                                                                                 
            print "\t"+i.encode("utf-8"),
        print                                                                                                

        for k, v in input_hash.iteritems():
            result = k.strip()
            for i in header:
                if input_hash[k].has_key(i):
                    result += "\t"+str(input_hash[k][i])
                else:
                    result += "\t"+"0"
            print result

if __name__=="__main__":
    input_hash = {"aaa":{"a":1,"b":2}, "bbb":{"c":1,"d":2}}
    Matrix(input_hash)
