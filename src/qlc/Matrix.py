# -*- coding: utf-8 -*-

"""
Class to produce matrix data format as input for statistical packages like R.
"""

import operator # python-sort-a-dictionary-by-value

class Matrix(object):
    """ 
    take as input a hash of hashes:
    
    { language_name: {grapheme:count, grapheme2:count}
      language_name2: {...}
      ...
    }

    return a 2D matrix

    """

    def __init__(self):
        self.header_hash = {}
        self.input_hash = {"aaa":{"a":1,"b":2}, "bbb":{"c":1,"d":2}}
        print self.input_hash

        # 1. this code creates the matrix of segment coccurrences and prints it
        # create blank matrix

        self.header_hash = self.getHeader(self.input_hash)
        print self.header_hash


    def getHeader(self, input_hash):
        for k, v in input_hash.iteritems():
            for k2, v2 in input_hash[k].iteritems():
                if not self.header_hash.has_key(k2):
                    self.header_hash[k2] = 1
                else:
                    self.header_hash[k2] += 1
        return self.header_hash



    """
    def createMatrix():
        matrix = []

        for i in range(len(segment_matrix_hash)):
            matrix.append([[] for j in range(len(segment_matrix_hash))])

            # sort the segments_matrix_hash (segments+index) -- returns a list of tuples (k, v)
            sorted_tuples = sorted(segment_matrix_hash.iteritems(), key=operator.itemgetter(1), reverse=False)

            # create sorted header                               
            header = []
            for i in sorted_tuples:
                header.append(i[0].strip())
        
                for i in header:                                                                                                 
                    print "\t"+i.encode("utf-8"),
                    print                                                                                                

    for k, v in cooccurrences_hash.iteritems():
        (x,y) = k.split("\t")
        count = v
        # print x.encode("utf-8"), y.encode("utf-8")
        x_coord = segment_matrix_hash[x]
        y_coord = segment_matrix_hash[y]
        # print x_coord, y_coord
        matrix[x_coord][y_coord] = count
        matrix[y_coord][x_coord] = count

    for i in range(0, len(matrix)):
        row_result = ""
        row = matrix[i]
        for j in row:
            if j == []:
                j = 0
            row_result += "\t"+str(j)
        print header[i].encode("utf-8")+row_result
        """




if __name__=="__main__":
    m = Matrix()
