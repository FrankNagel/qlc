# Introduction #

This tutorial demonstrates how to generate a phylogenetic tree from the data in the ASJP (The Automated Similarity Judgement Program) dataset. It uses a string comparison algorithm named "ALINE" to generate a distance matrix between a given set of languages. For this task, every string of one language in the ASJP set (100 strings for each language) is compared to the string with the same translation in another language. The distance between the languages is then calculated by summing up the differences between the strings of the two languages. To learn more about the algorithm and the data see the following website:

  * [Python implementation of ALINE](http://sourceforge.net/projects/pyaline/)
  * [Thesis of Paul Huff, developer of PyAline (PDF)](http://www.eva.mpg.de/~wichmann/HuffThesis.pdf)
  * [Website of the ASJP project](http://email.eva.mpg.de/~wichmann/ASJPHomePage.htm)
  * [Software to handle and process ASJP data](http://email.eva.mpg.de/~wichmann/software.htm)

Right now there are two scripts in the qlc repository to handle the data from the ASJP project:

  * An extraction script that writes the CSV table suitable for PyAline. It takes the data file downloaded from the ASJP website as input ("listss13.txt").
  * A script that calculates the distance matrix and outputs an (un)rooted, binary (phylogenetic) tree based on the distance matrix with the help of a neighbour-joining algorithm.

# Extracting the data #

To extract the data from the file "listss13.txt" ([download page](http://email.eva.mpg.de/~wichmann/languages.htm)) there is a Python script that writes a all strings TAB-separated to a table, one row for each language. The first 9 columns are reserved for the an ID, the name of the language, codes (WALS and ISO), family names (there are two kinds of family notation in the ASJP file), geographical position (latitude and longitude) and speaker number. The phonetic strings start from column 10. The extraction script is based on the script by Paul Huff which is [available here](http://email.eva.mpg.de/~wichmann/process_asjp-0.0.1.zip). In our repository the data file and the extraction script is available in "data/asjp".

To extract the data to a file "output\_aline.txt", just navigate to the folder "data/asjp" and call the script like this:

```
$ python process_asjp.py -f listss13.txt -i -r Sal
```

In this case the script exports only the languages from the Salish family (option "-r" expects a regular expression; we look for families that contain "Sal" here, which are only the Salish languages). Option "-f" takes the input file name, option "-i" tells the script to output in tabular format to use with PyAline.


# Distance matrix and neighbor-joining tree #

In our repository there is a script "bin/ex\_salish\_tree.py" that contains all the code from this sections and outputs two trees as files ("njtree.png" and "njtree.pdf"). To start this script first change the current path to the base path of the repository (the folder that contains "bin", "data", etc.). Then add the "src" path to your PYTHONPATH environment variable:

```
$ export PYTHONPATH=$PYTHONPATH:./src
```

Now you can call the script:

```
$ python bin/ex_salish_tree.py
```

This example script starts with a typical Python header and some import statements that load all the Python modules we will later need:

```
# -*- coding: utf-8 -*-
#!/usr/bin/python

import csv, sys
from qlc.comparison.languagecomparer import LanguageComparer
from qlc.comparison import aline
from qlc.distance import nj
from numpy import *
```

The next step is to calculate the distance matrix for all the strings between each language pair. For this, we transformed the PyAline script mentioned above to a Python class `comparison.languagecomparer.LanguageComparer` in our qlc module.

The `LanguageComparer` expects a three-dimensional matrix as input (or better: a list of lists of lists). The first dimension are the languages, the second are the 100 ASJP concepts , the third are the strings for a given language and concept. The latter dimension is needed because there might be more than one string in a language for a concept in the ASJP data. The ALINE algorithm later compares each of those strings with every other string of the same concept of the other language and takes the minimum distance of all string pairs.

The following Python code snippet builds the three-dimensional structure from the file "output\_aline.txt" that was generated in the previous step.

```
filename = "data/asjp/output_aline.txt"
file_data = open(filename, "rb")
file_content = csv.reader(file_data, quoting=csv.QUOTE_NONE, delimiter="\t")
languages = {}

language_names = []

language_data = []
for row in file_content:
    language_names.append(row[1])
    language_concepts = []
    for s in row[9:]:
        if s == "":
            language_concepts.append([])
            continue
        s_decode = s.decode("latin1")
        s_split = s_decode.split("|")
        language_concept_entries = []
        for s_entry in s_split:
            s_entry = s_entry.strip()                
            if s_entry != "":
                language_concept_entries.append(s_entry)
        language_concepts.append(language_concept_entries)
    language_data.append(language_concepts)
```

To calculate the distance matrix is then straight-forward:

```
x = LanguageComparer(language_data, aline.ASJP, False)
x.generate_matrix()
print x.matrix
```

The last step is to calculate a tree for the given distance matrix. We use a neighbor-joining algorithm for this, that outputs a binary tree for the given languages. For demonstrational purposes we calculate and display the tree in two variants. First, the qlc module contains a class `distance.nj.Nj` that calculates the tree and outputs a PNG image file with an unrooted, binary tree. It expects a distance matrix and a list of languages names for the labels as input:

```
nj = nj.Nj(x.matrix, language_names)
nj.generate_tree()
nj.as_png(filename="njtree.png")
```

The second possibility is to let the stastical software R calculate and output the tree. For this, we facilitate rpy2, a Python module that allows us to start and use an R environment from within our Python code. We use the ape package from R's CRAN repository here, because it has an easy-to-use `nj()` method to calcute the tree. As simple `plot()` than plots the tree, this time as a rooted, binary tree:

```
try:
    import rpy2.robjects as robjects
    from rpy2.robjects.packages import importr

    L = robjects.StrVector(language_names)
    M = robjects.r['matrix'](list(x.matrix.flatten()), len(language_names))
    
    # workaround to set column names, there is a bug in rpy2:
    # https://bitbucket.org/lgautier/rpy2/issue/70/matrix-colnames-and-possibly-rownames
    M = robjects.r['as.data.frame'](M)
    M.colnames = L
    M = robjects.r['as.matrix'](M)

    print M

    ape = importr('ape')
    grdevices = importr('grDevices')

    tr = ape.nj(M)

    ofn = 'njtree.pdf'
    grdevices.pdf(ofn)
    robjects.r.plot(tr)
    grdevices.dev_off()

except:
    print "rpy2 not installed, I will not plot nj tree with R."
```

Here is (more or less the same) code in R which plots a NJ tree for the distance matrix:

```
> M <- read.table("salish_matrix.txt", header=T)
> rownames(M) <- colnames(M)
> M2 <- data.matrix(M, rownames.force=T)
> library(ape)
> tr <- nj(M2)
> plot(tr)
```