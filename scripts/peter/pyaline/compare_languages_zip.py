#!/usr/bin/env python

import sys, os
import tempfile, subprocess
from zipfile import ZipFile
from util import Matrix, Infinity

class LanguageComparer(object):
    def __init__(self, languages):
        self.languages = languages
        self.names = self.languages.keys()
        self.matrix = None

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

    def compare_languages(self, x, y):
        sum = 0
        count = 0

        temppath = tempfile.mkdtemp()
        lang_1_1 = open(os.path.join(temppath, "lang_1_1.txt"), "w")
        lang_2_2 = open(os.path.join(temppath, "lang_2_2.txt"), "w")
        lang_1_2 = open(os.path.join(temppath, "lang_1_2.txt"), "w")

        for i in xrange(len(x)):
            #sys.stderr.write("First i: %i\n" % (i, ))
            if (x[i] == "") or (y[i] == ""):
                continue

            lang_1_1.write(x[i] + " " + x[i] + " ")
            lang_2_2.write(y[i] + " " + y[i] + " ")
            lang_1_2.write(x[i] + " " + y[i] + " ")
        
        lang_1_1.close()
        lang_2_2.close()
        lang_1_2.close()

        sizetxt_1_1 = os.path.getsize(os.path.join(temppath, "lang_1_1.txt"))
        sizetxt_2_2 = os.path.getsize(os.path.join(temppath, "lang_2_2.txt"))
        sizetxt_1_2 = os.path.getsize(os.path.join(temppath, "lang_1_2.txt"))

        subprocess.Popen([r"gzip", os.path.join(temppath, "lang_1_1.txt")]).wait()
        subprocess.Popen([r"gzip", os.path.join(temppath, "lang_2_2.txt")]).wait()
        subprocess.Popen([r"gzip", os.path.join(temppath, "lang_1_2.txt")]).wait()
        #myzip_1_1 = ZipFile(os.path.join(temppath, "lang_1_1.zip"), 'w')
        #myzip_1_1.write(os.path.join(temppath, "lang_1_1.txt"))
        #myzip_1_1.close()
        #myzip_2_2 = ZipFile(os.path.join(temppath, "lang_2_2.zip"), 'w')
        #myzip_2_2.write(os.path.join(temppath, "lang_2_2.txt"))
        #myzip_2_2.close()
        #myzip_1_2 = ZipFile(os.path.join(temppath, "lang_1_2.zip"), 'w')
        #myzip_1_2.write(os.path.join(temppath, "lang_1_2.txt"))
        #myzip_1_2.close()
        
        size_1_1 = os.path.getsize(os.path.join(temppath, "lang_1_1.txt.gz")) - 24
        size_2_2 = os.path.getsize(os.path.join(temppath, "lang_2_2.txt.gz")) - 24
        size_1_2 = os.path.getsize(os.path.join(temppath, "lang_1_2.txt.gz")) - 24

        ratio_1_1 = float(size_1_1) / float(sizetxt_1_1)
        ratio_2_2 = float(size_2_2) / float(sizetxt_2_2)
        ratio_1_2 = float(size_1_2) / float(sizetxt_1_2)
        
        #print ratio_1_1
        #print ratio_2_2
        #print ratio_1_2
        
        return 1.0 - (float(ratio_1_1+ratio_2_2) / float(2*ratio_1_2))

if __name__ == "__main__":
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("-f", "--file", dest="filename")
    parser.add_option("-e", "--header", action="store_true", dest="header")
    (options, args) = parser.parse_args()
    if not options.filename:
        print "Filename required."
        sys.exit(0)
    import csv
    words = csv.reader(open(options.filename), quoting=csv.QUOTE_NONE, delimiter="\t")
    if options.header:
        words.next()
    languages = {}
    for row in words:
        languages[row[0]] = row[3:]

    x = LanguageComparer(languages)
    x.generate_matrix()
